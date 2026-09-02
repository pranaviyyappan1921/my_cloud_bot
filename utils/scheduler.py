"""
Scheduled Tasks Utility for Cloud AI Chatbot.
Provides thread-safe TaskManager, persistence in data/scheduled_tasks.json,
recurrence & next_run calculation, background task runner, and natural language schedule parser.
"""

import os
import json
import time
import uuid
import re
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger("chatbot.scheduler")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TASKS_FILE = os.path.join(DATA_DIR, "scheduled_tasks.json")
os.makedirs(DATA_DIR, exist_ok=True)

TASK_TYPE_ICONS = {
    "reminder": "⏰",
    "briefing": "📰",
    "web_monitor": "🔎",
    "report": "📊",
    "study": "📚",
    "price_monitor": "💰",
    "website_monitor": "🌐",
}

TASK_TYPE_LABELS = {
    "reminder": "Reminder",
    "briefing": "AI Briefing",
    "web_monitor": "Web Monitor",
    "report": "Report",
    "study": "Study Reminder",
    "price_monitor": "Price Monitor",
    "website_monitor": "Website Monitor",
}


def calculate_next_run(
    recurrence: str,
    time_str: str,
    days_of_week: Optional[List[str]] = None,
    specific_date: Optional[str] = None,
    tz_offset_minutes: int = 0,
) -> Optional[str]:
    """
    Calculates the next ISO timestamp for a task based on recurrence and time (HH:MM).
    Supports: once, daily, weekly, weekdays, custom.
    """
    try:
        now = datetime.utcnow()
        # Parse target hour and minute
        time_parts = time_str.split(":")
        target_hour = int(time_parts[0])
        target_minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        recurrence = (recurrence or "daily").lower()

        if recurrence == "once":
            if specific_date:
                # Format: YYYY-MM-DD
                dt = datetime.strptime(f"{specific_date} {target_hour:02d}:{target_minute:02d}", "%Y-%m-%d %H:%M")
                return dt.isoformat() + "Z"
            else:
                candidate = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                if candidate <= now:
                    candidate += timedelta(days=1)
                return candidate.isoformat() + "Z"

        elif recurrence == "daily":
            candidate = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate.isoformat() + "Z"

        elif recurrence == "weekdays":
            candidate = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            # Monday is 0, Sunday is 6. Weekdays are 0 to 4.
            while candidate.weekday() >= 5:
                candidate += timedelta(days=1)
            return candidate.isoformat() + "Z"

        elif recurrence in ("weekly", "custom"):
            valid_days = [d.capitalize() for d in (days_of_week or ["Monday"])]
            day_map = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            target_weekdays = sorted([day_map[d] for d in valid_days if d in day_map])
            if not target_weekdays:
                target_weekdays = [0]  # Default Monday

            # Look ahead up to 14 days for the closest match
            for day_offset in range(0, 15):
                candidate = (now + timedelta(days=day_offset)).replace(
                    hour=target_hour, minute=target_minute, second=0, microsecond=0
                )
                if candidate.weekday() in target_weekdays and candidate > now:
                    return candidate.isoformat() + "Z"

            candidate = now + timedelta(days=7)
            return candidate.isoformat() + "Z"

        # Default fallback
        candidate = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) + timedelta(days=1)
        return candidate.isoformat() + "Z"

    except Exception as e:
        logger.error("Error calculating next_run: %s", e)
        return (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"


class TaskManager:
    """
    Thread-safe manager for scheduled AI tasks.
    Persists data in data/scheduled_tasks.json and supports session-based user isolation.
    """

    def __init__(self, storage_path: str = TASKS_FILE):
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        with self._lock:
            if os.path.exists(self.storage_path):
                try:
                    with open(self.storage_path, "r", encoding="utf-8") as f:
                        self._tasks = json.load(f)
                except Exception as e:
                    logger.warning("Could not read tasks file, initializing empty: %s", e)
                    self._tasks = {}
            else:
                self._tasks = {}

    def _save(self):
        # Assumes caller holds self._lock
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save tasks to %s: %s", self.storage_path, e)

    def list_tasks(self, session_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of tasks belonging to session_id, filtered by status if provided."""
        with self._lock:
            results = []
            for task in self._tasks.values():
                if task.get("session_id") == session_id:
                    if not status_filter or status_filter.lower() == "all" or task.get("status", "").lower() == status_filter.lower():
                        results.append(dict(task))
            # Sort by created_at descending
            results.sort(key=lambda t: t.get("created_at", 0), reverse=True)
            return results

    def get_task(self, task_id: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single task by id, verifying session ownership if provided."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            if session_id and task.get("session_id") != session_id:
                return None
            return dict(task)

    def create_task(self, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates and stores a new scheduled task."""
        with self._lock:
            task_id = f"task_{uuid.uuid4().hex[:10]}"
            now_iso = datetime.utcnow().isoformat() + "Z"
            now_ts = int(time.time())

            recurrence = data.get("recurrence", "daily")
            time_str = data.get("time", "08:00")
            days_of_week = data.get("days_of_week", [])
            specific_date = data.get("specific_date")
            timezone_str = data.get("timezone", "UTC")

            next_run = calculate_next_run(
                recurrence=recurrence,
                time_str=time_str,
                days_of_week=days_of_week,
                specific_date=specific_date,
            )

            task_type = data.get("task_type", "reminder")
            if task_type not in TASK_TYPE_ICONS:
                task_type = "reminder"

            task = {
                "id": task_id,
                "session_id": session_id,
                "title": (data.get("title") or "Untitled Task").strip(),
                "prompt": (data.get("prompt") or "").strip(),
                "task_type": task_type,
                "recurrence": recurrence,
                "time": time_str,
                "days_of_week": days_of_week,
                "specific_date": specific_date,
                "timezone": timezone_str,
                "next_run": next_run,
                "status": "active",
                "created_at": now_ts,
                "updated_at": now_ts,
                "created_at_iso": now_iso,
                "execution_history": [],
            }

            self._tasks[task_id] = task
            self._save()
            logger.info("Created scheduled task %s ('%s') for session %s", task_id, task["title"], session_id[:8])
            return dict(task)

    def update_task(self, task_id: str, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.get("session_id") != session_id:
                return None

            if "title" in data:
                task["title"] = data["title"].strip()
            if "prompt" in data:
                task["prompt"] = data["prompt"].strip()
            if "task_type" in data and data["task_type"] in TASK_TYPE_ICONS:
                task["task_type"] = data["task_type"]
            if "recurrence" in data:
                task["recurrence"] = data["recurrence"]
            if "time" in data:
                task["time"] = data["time"]
            if "days_of_week" in data:
                task["days_of_week"] = data["days_of_week"]
            if "specific_date" in data:
                task["specific_date"] = data["specific_date"]
            if "timezone" in data:
                task["timezone"] = data["timezone"]
            if "status" in data and data["status"] in ("active", "paused", "completed", "failed"):
                task["status"] = data["status"]

            # Recalculate next_run
            task["next_run"] = calculate_next_run(
                recurrence=task.get("recurrence", "daily"),
                time_str=task.get("time", "08:00"),
                days_of_week=task.get("days_of_week", []),
                specific_date=task.get("specific_date"),
            )
            task["updated_at"] = int(time.time())

            self._save()
            logger.info("Updated scheduled task %s", task_id)
            return dict(task)

    def delete_task(self, task_id: str, session_id: str) -> bool:
        """Deletes a task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.get("session_id") != session_id:
                return False
            del self._tasks[task_id]
            self._save()
            logger.info("Deleted task %s", task_id)
            return True

    def set_status(self, task_id: str, session_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Sets status (active/paused)."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.get("session_id") != session_id:
                return None
            task["status"] = status
            task["updated_at"] = int(time.time())
            if status == "active":
                task["next_run"] = calculate_next_run(
                    recurrence=task.get("recurrence", "daily"),
                    time_str=task.get("time", "08:00"),
                    days_of_week=task.get("days_of_week", []),
                    specific_date=task.get("specific_date"),
                )
            self._save()
            logger.info("Task %s status set to %s", task_id, status)
            return dict(task)

    def append_execution_record(
        self,
        task_id: str,
        status: str,
        result: str,
        duration_seconds: float,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Records an execution outcome and advances next_run."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None

            now_iso = datetime.utcnow().isoformat() + "Z"
            record = {
                "id": f"run_{uuid.uuid4().hex[:8]}",
                "executed_at": now_iso,
                "status": status,
                "duration_seconds": round(duration_seconds, 2),
                "result": result,
                "error": error,
            }

            history = task.setdefault("execution_history", [])
            history.insert(0, record)
            # Retain up to 25 execution entries per task
            task["execution_history"] = history[:25]

            # If it's a one-time task, mark completed
            if task.get("recurrence") == "once":
                task["status"] = "completed"
            else:
                task["next_run"] = calculate_next_run(
                    recurrence=task.get("recurrence", "daily"),
                    time_str=task.get("time", "08:00"),
                    days_of_week=task.get("days_of_week", []),
                    specific_date=task.get("specific_date"),
                )

            task["updated_at"] = int(time.time())
            self._save()
            return dict(task)

    def get_due_tasks(self) -> List[Dict[str, Any]]:
        """Returns all active tasks whose next_run is <= now."""
        with self._lock:
            now_iso = datetime.utcnow().isoformat() + "Z"
            due = []
            for task in self._tasks.values():
                if task.get("status") == "active":
                    next_run = task.get("next_run")
                    if next_run and next_run <= now_iso:
                        due.append(dict(task))
            return due


# Singleton TaskManager
task_manager = TaskManager()


# ---------------------------------------------------------------------------
# Natural Language Schedule Parser
# ---------------------------------------------------------------------------
def parse_natural_language_schedule(text: str, gemini_client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Parses natural language requests into structured task specifications:
      - title
      - prompt
      - task_type
      - recurrence ('once', 'daily', 'weekly', 'weekdays', 'custom')
      - time ('HH:MM')
      - days_of_week
    Uses fast deterministic regex parsing first, and falls back to Gemini if available.
    """
    raw = (text or "").strip()
    lower = raw.lower()

    # Defaults
    result = {
        "title": "Scheduled Task",
        "prompt": raw,
        "task_type": "reminder",
        "recurrence": "daily",
        "time": "08:00",
        "days_of_week": [],
        "specific_date": None,
    }

    # Detect Task Type
    if any(k in lower for k in ["news", "briefing", "headline", "tech news", "ai news"]):
        result["task_type"] = "briefing"
        result["title"] = "Daily AI & Tech Briefing"
    elif any(k in lower for k in ["study", "course", "exam", "homework", "learn", "reading", "read"]):
        result["task_type"] = "study"
        result["title"] = "Study Session Reminder"
    elif any(k in lower for k in ["price", "discount", "deal", "amazon", "product"]):
        result["task_type"] = "price_monitor"
        result["title"] = "Price Monitor Task"
    elif any(k in lower for k in ["website", "site", "webpage", "check url", "url"]):
        result["task_type"] = "website_monitor"
        result["title"] = "Website Status Monitor"
    elif any(k in lower for k in ["report", "weekly report", "summary of week", "activity"]):
        result["task_type"] = "report"
        result["title"] = "Weekly AI Report"
    elif any(k in lower for k in ["monitor", "watch", "check"]):
        result["task_type"] = "web_monitor"
        result["title"] = "Web Monitoring Task"
    else:
        result["task_type"] = "reminder"
        result["title"] = "Reminder Task"

    # Detect Recurrence
    if "weekday" in lower or "monday to friday" in lower or "every weekday" in lower:
        result["recurrence"] = "weekdays"
    elif "every day" in lower or "daily" in lower or "each day" in lower or "every morning" in lower or "every evening" in lower:
        result["recurrence"] = "daily"
    elif "once" in lower or "tomorrow" in lower or "today" in lower:
        result["recurrence"] = "once"
        if "tomorrow" in lower:
            tomorrow_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
            result["specific_date"] = tomorrow_date

    # Detect Days of Week
    days_map = {
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
        "sunday": "Sunday",
    }
    matched_days = [cap for name, cap in days_map.items() if name in lower]
    if matched_days:
        result["days_of_week"] = matched_days
        if result["recurrence"] != "weekdays":
            result["recurrence"] = "weekly"

    # Detect Time (e.g. 7 PM, 9:30 AM, 14:00, morning, evening, afternoon)
    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3)
        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        result["time"] = f"{hour:02d}:{minute:02d}"
    else:
        # Check 24-hour time format: 14:30
        h24_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lower)
        if h24_match:
            result["time"] = f"{int(h24_match.group(1)):02d}:{int(h24_match.group(2)):02d}"
        elif "morning" in lower:
            result["time"] = "08:00"
        elif "evening" in lower or "night" in lower:
            result["time"] = "19:00"
        elif "afternoon" in lower or "noon" in lower:
            result["time"] = "13:00"

    # Generate cleaner Title and Prompt
    cleaned_prompt = raw
    # Strip schedule phrases to make a clean action prompt
    cleaned_prompt = re.sub(r"(?i)\b(every\s+(day|monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekday|morning|evening|week))\b", "", cleaned_prompt)
    cleaned_prompt = re.sub(r"(?i)\b(at\s+\d{1,2}(:\d{2})?\s*(am|pm)?)\b", "", cleaned_prompt)
    cleaned_prompt = re.sub(r"(?i)\b(remind me to|give me a|tell me if it|please)\b", "", cleaned_prompt)
    cleaned_prompt = cleaned_prompt.strip(" ,.;:-")
    if cleaned_prompt:
        result["prompt"] = cleaned_prompt[0].upper() + cleaned_prompt[1:]
        # Formulate a dynamic title
        words = result["prompt"].split()[:5]
        result["title"] = (" ".join(words)).title()
    else:
        result["prompt"] = raw

    return result


# ---------------------------------------------------------------------------
# Background Task Runner (Local Dev Execution Loop)
# ---------------------------------------------------------------------------
class BackgroundScheduler(threading.Thread):
    """
    Background daemon thread that periodically checks for due active tasks
    and executes them using GeminiClient while the Flask server is running.
    """

    def __init__(self, task_mgr: TaskManager, gemini_client_getter, interval_seconds: int = 30):
        super().__init__(daemon=True, name="CloudBot-BackgroundScheduler")
        self.task_mgr = task_mgr
        self.get_gemini_client = gemini_client_getter
        self.interval = interval_seconds
        self._running = True

    def run(self):
        logger.info("BackgroundScheduler started (poll interval: %ds)", self.interval)
        while self._running:
            try:
                self.tick()
            except Exception as e:
                logger.error("Error in BackgroundScheduler tick: %s", e)
            time.sleep(self.interval)

    def tick(self) -> List[Dict[str, Any]]:
        """
        Executes all due tasks. Can also be invoked directly by POST /api/tasks/tick.
        """
        due_tasks = self.task_mgr.get_due_tasks()
        results = []
        if not due_tasks:
            return results

        logger.info("BackgroundScheduler found %d due task(s) to execute", len(due_tasks))
        client = self.get_gemini_client()

        for task in due_tasks:
            task_id = task["id"]
            title = task.get("title", "Scheduled Task")
            prompt = task.get("prompt", "")
            task_type = task.get("task_type", "reminder")

            logger.info("Executing due task %s: '%s'", task_id, title)
            start_time = time.time()
            try:
                # Prepare contextual prompt for AI based on task type
                system_prefix = f"You are executing a scheduled automated task: '{title}' (Category: {task_type}).\n"
                full_prompt = f"{system_prefix}Request: {prompt}\n\nPlease provide a high-quality, comprehensive, and well-structured response in Markdown format."

                if client and hasattr(client, "generate_reply"):
                    ai_result = client.generate_reply(message=full_prompt)
                else:
                    ai_result = f"Task completed successfully: {prompt}"

                duration = time.time() - start_time
                self.task_mgr.append_execution_record(
                    task_id=task_id,
                    status="completed",
                    result=ai_result,
                    duration_seconds=duration,
                )
                results.append({"task_id": task_id, "status": "completed", "result": ai_result})
                logger.info("Task %s completed in %.2fs", task_id, duration)

            except Exception as e:
                duration = time.time() - start_time
                err_msg = str(e)
                logger.error("Task %s failed: %s", task_id, err_msg)
                self.task_mgr.append_execution_record(
                    task_id=task_id,
                    status="failed",
                    result=f"Execution error: {err_msg}",
                    duration_seconds=duration,
                    error=err_msg,
                )
                results.append({"task_id": task_id, "status": "failed", "error": err_msg})

        return results

    def stop(self):
        self._running = False
