"""
Plugin Manager & Execution Sandbox for Cloud AI Chatbot.

Manages:
- Plugin registry and discovery
- Persistent state (connected, enabled, permissions, configuration)
- Security checks & sandboxed execution
- Granular execution logging (plugin name, action, status, duration, timestamp)
- REST APIs support (list, connect, disconnect, enable, disable, permissions, logs)
- AI Automatic Tool Selection & contextual grounding
"""

import os
import json
import time
import uuid
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from .base_plugin import BasePlugin
from .calculator_plugin import CalculatorPlugin
from .web_search_plugin import WebSearchPlugin
from .file_analysis_plugin import FileAnalysisPlugin
from .azure_blob_plugin import AzureBlobPlugin
from .github_plugin import GitHubPlugin
from .integrations_catalog import (
    GmailPlugin,
    GoogleDrivePlugin,
    OutlookPlugin,
    GoogleCalendarPlugin,
    SlackPlugin,
    DropboxPlugin,
    NotionPlugin,
    DatabasesPlugin,
)

logger = logging.getLogger("chatbot.plugins.manager")


class PluginManager:
    """
    Central Coordinator for the Dynamic AI Plugin Marketplace.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.state_file = os.path.join(self.data_dir, "plugin_state.json")
        self.logs_file = os.path.join(self.data_dir, "plugin_logs.json")

        self.plugins: Dict[str, BasePlugin] = {}
        self._register_default_plugins()
        self._load_persisted_state()

    def _register_default_plugins(self) -> None:
        """Registers all built-in plugins and integrations catalog."""
        default_instances: List[BasePlugin] = [
            # Real working plugins
            CalculatorPlugin(),
            WebSearchPlugin(),
            FileAnalysisPlugin(),
            AzureBlobPlugin(),
            # Future connectable integrations
            GmailPlugin(),
            GitHubPlugin(),
            GoogleDrivePlugin(),
            OutlookPlugin(),
            GoogleCalendarPlugin(),
            SlackPlugin(),
            DropboxPlugin(),
            NotionPlugin(),
            DatabasesPlugin(),
        ]

        for p in default_instances:
            self.plugins[p.id] = p
            logger.debug("Registered plugin: %s (%s)", p.name, p.id)

    def _load_persisted_state(self) -> None:
        """Loads saved plugin states (connected, enabled, permissions, configs) from disk."""
        if not os.path.exists(self.state_file):
            self._save_state()
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                saved = json.load(f)

            for pid, pdata in saved.items():
                plugin = self.plugins.get(pid)
                if plugin:
                    if "is_connected" in pdata:
                        plugin.is_connected = bool(pdata["is_connected"])
                    if "is_enabled" in pdata:
                        plugin.is_enabled = bool(pdata["is_enabled"])
                    if "config" in pdata and isinstance(pdata["config"], dict):
                        plugin.config = pdata["config"]

                    # Restore permissions
                    saved_perms = pdata.get("permissions", {})
                    if isinstance(saved_perms, dict):
                        for perm_id, perm_val in saved_perms.items():
                            if perm_id in plugin.permissions:
                                plugin.permissions[perm_id].enabled = bool(perm_val)

        except Exception as e:
            logger.warning("Could not load persisted plugin state: %s. Using defaults.", e)

    def _save_state(self) -> None:
        """Persists current state of all plugins to disk."""
        try:
            state_data = {}
            for pid, p in self.plugins.items():
                state_data[pid] = {
                    "is_connected": p.is_connected,
                    "is_enabled": p.is_enabled,
                    "config": p.config,
                    "permissions": {perm.id: perm.enabled for perm in p.permissions.values()},
                }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save plugin state: %s", e)

    # ---------------------------------------------------------------------------
    # Management APIs
    # ---------------------------------------------------------------------------
    def list_plugins(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        connected_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Returns list of plugin dicts with optional filtering."""
        result = []
        q = search_query.strip().lower() if search_query else None

        for p in self.plugins.values():
            if connected_only and not p.is_connected:
                continue

            if category and category.lower() != "all":
                # Check category match or category in tags
                cat_match = p.category.lower() == category.lower()
                tag_match = any(category.lower() in t.lower() for t in p.tags)
                if not (cat_match or tag_match):
                    continue

            if q:
                in_name = q in p.name.lower()
                in_desc = q in p.description.lower()
                in_cat = q in p.category.lower()
                in_tags = any(q in t.lower() for t in p.tags)
                if not (in_name or in_desc or in_cat or in_tags):
                    continue

            result.append(p.to_dict())

        return result

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        return self.plugins.get(plugin_id)

    def connect_plugin(self, plugin_id: str, config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found.", None

        plugin.is_connected = True
        plugin.is_enabled = True
        if config and isinstance(config, dict):
            plugin.config.update(config)

        self._save_state()
        logger.info("Plugin connected: %s", plugin.name)
        return True, f"Successfully connected '{plugin.name}'.", plugin.to_dict()

    def disconnect_plugin(self, plugin_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found.", None

        plugin.is_connected = False
        plugin.is_enabled = False
        plugin.config = {}
        self._save_state()
        logger.info("Plugin disconnected: %s", plugin.name)
        return True, f"Successfully disconnected '{plugin.name}'.", plugin.to_dict()

    def enable_plugin(self, plugin_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found.", None

        if not plugin.is_connected:
            return False, f"Plugin '{plugin.name}' must be connected before enabling.", None

        plugin.is_enabled = True
        self._save_state()
        return True, f"Enabled '{plugin.name}'.", plugin.to_dict()

    def disable_plugin(self, plugin_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found.", None

        plugin.is_enabled = False
        self._save_state()
        return True, f"Disabled '{plugin.name}'.", plugin.to_dict()

    def update_permissions(self, plugin_id: str, permissions_update: Dict[str, bool]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found.", None

        for perm_id, is_enabled in permissions_update.items():
            if perm_id in plugin.permissions:
                plugin.permissions[perm_id].enabled = bool(is_enabled)

        self._save_state()
        return True, f"Updated permissions for '{plugin.name}'.", plugin.to_dict()

    def update_config(self, plugin_id: str, new_config: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found.", None

        plugin.config.update(new_config)
        self._save_state()
        return True, f"Updated configuration for '{plugin.name}'.", plugin.to_dict()

    # ---------------------------------------------------------------------------
    # Execution Sandbox & Logging
    # ---------------------------------------------------------------------------
    def execute_tool(
        self,
        plugin_id: str,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a plugin tool in a controlled sandbox with strict validation and logging.
        """
        plugin = self.plugins.get(plugin_id)
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat()

        if not plugin:
            err_msg = f"Plugin '{plugin_id}' does not exist."
            self._record_log(
                plugin_id=plugin_id,
                plugin_name="Unknown",
                tool_name=tool_name,
                status="error",
                duration_ms=0,
                timestamp=timestamp,
                input_params=params,
                error_message=err_msg,
                session_id=session_id,
            )
            return {"success": False, "error": err_msg, "summary": "Plugin not found"}

        if not plugin.is_connected:
            err_msg = f"Plugin '{plugin.name}' is disconnected."
            self._record_log(
                plugin_id=plugin_id,
                plugin_name=plugin.name,
                tool_name=tool_name,
                status="blocked",
                duration_ms=0,
                timestamp=timestamp,
                input_params=params,
                error_message=err_msg,
                session_id=session_id,
            )
            return {"success": False, "error": err_msg, "summary": "Plugin disconnected"}

        if not plugin.is_enabled:
            err_msg = f"Plugin '{plugin.name}' is disabled."
            self._record_log(
                plugin_id=plugin_id,
                plugin_name=plugin.name,
                tool_name=tool_name,
                status="blocked",
                duration_ms=0,
                timestamp=timestamp,
                input_params=params,
                error_message=err_msg,
                session_id=session_id,
            )
            return {"success": False, "error": err_msg, "summary": "Plugin disabled"}

        # Validate call & arguments
        valid, validation_err = plugin.validate_tool_call(tool_name, params)
        if not valid:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self._record_log(
                plugin_id=plugin_id,
                plugin_name=plugin.name,
                tool_name=tool_name,
                status="blocked",
                duration_ms=duration_ms,
                timestamp=timestamp,
                input_params=params,
                error_message=validation_err,
                session_id=session_id,
            )
            return {"success": False, "error": validation_err, "summary": f"Validation failed: {validation_err}"}

        # Execute
        try:
            result = plugin.execute(tool_name, params, context=context)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            status = "success" if result.get("success", False) else "error"
            summary = result.get("summary", "")
            error_msg = result.get("error")

            self._record_log(
                plugin_id=plugin_id,
                plugin_name=plugin.name,
                tool_name=tool_name,
                status=status,
                duration_ms=duration_ms,
                timestamp=timestamp,
                input_params=params,
                output_summary=summary,
                error_message=error_msg,
                session_id=session_id,
            )

            result["duration_ms"] = duration_ms
            return result

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.exception("Plugin execution error in %s.%s: %s", plugin_id, tool_name, e)
            err_str = f"Execution runtime error: {str(e)}"
            self._record_log(
                plugin_id=plugin_id,
                plugin_name=plugin.name,
                tool_name=tool_name,
                status="error",
                duration_ms=duration_ms,
                timestamp=timestamp,
                input_params=params,
                error_message=err_str,
                session_id=session_id,
            )
            return {"success": False, "error": err_str, "duration_ms": duration_ms, "summary": "Runtime error"}

    # ---------------------------------------------------------------------------
    # Logging & Telemetry Persistence
    # ---------------------------------------------------------------------------
    def _record_log(
        self,
        plugin_id: str,
        plugin_name: str,
        tool_name: str,
        status: str,  # "success", "error", "blocked"
        duration_ms: float,
        timestamp: str,
        input_params: Optional[Dict[str, Any]] = None,
        output_summary: Optional[str] = None,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Appends an execution log entry to plugin_logs.json."""
        # Sanitize sensitive keys from input params
        safe_params = {}
        if input_params and isinstance(input_params, dict):
            for k, v in input_params.items():
                if "key" in k.lower() or "token" in k.lower() or "secret" in k.lower() or "password" in k.lower():
                    safe_params[k] = "******"
                elif isinstance(v, str) and len(v) > 150:
                    safe_params[k] = v[:150] + "..."
                else:
                    safe_params[k] = v

        entry = {
            "id": f"log_{uuid.uuid4().hex[:10]}",
            "plugin_id": plugin_id,
            "plugin_name": plugin_name,
            "action": tool_name,
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": timestamp,
            "input_params": safe_params,
            "output_summary": output_summary or (error_message if status != "success" else "Executed"),
            "error_message": error_message,
            "session_id": session_id,
        }

        try:
            logs = self._read_all_logs()
            logs.insert(0, entry)
            # Cap logs to max 400 items
            if len(logs) > 400:
                logs = logs[:400]

            with open(self.logs_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.warning("Could not append plugin log: %s", e)

    def _read_all_logs(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.logs_file):
            return []
        try:
            with open(self.logs_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def get_logs(
        self,
        plugin_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        logs = self._read_all_logs()
        filtered = []
        for l in logs:
            if plugin_id and l.get("plugin_id") != plugin_id:
                continue
            if status and status.lower() != "all" and l.get("status") != status.lower():
                continue
            filtered.append(l)
            if len(filtered) >= limit:
                break
        return filtered

    def clear_logs(self, plugin_id: Optional[str] = None) -> int:
        logs = self._read_all_logs()
        if plugin_id:
            remaining = [l for l in logs if l.get("plugin_id") != plugin_id]
            cleared = len(logs) - len(remaining)
        else:
            cleared = len(logs)
            remaining = []

        try:
            with open(self.logs_file, "w", encoding="utf-8") as f:
                json.dump(remaining, f, indent=2)
        except Exception as e:
            logger.warning("Failed to clear plugin logs: %s", e)

        return cleared

    def get_stats(self) -> Dict[str, Any]:
        """Calculates marketplace analytics and execution statistics."""
        logs = self._read_all_logs()
        total_execs = len(logs)
        success_count = sum(1 for l in logs if l.get("status") == "success")
        error_count = sum(1 for l in logs if l.get("status") == "error")
        blocked_count = sum(1 for l in logs if l.get("status") == "blocked")

        connected_count = sum(1 for p in self.plugins.values() if p.is_connected)
        enabled_count = sum(1 for p in self.plugins.values() if p.is_connected and p.is_enabled)
        total_tools = sum(len(p.tools) for p in self.plugins.values())

        avg_duration = 0.0
        if total_execs > 0:
            avg_duration = round(sum(l.get("duration_ms", 0.0) for l in logs) / total_execs, 2)

        return {
            "total_plugins": len(self.plugins),
            "connected_plugins": connected_count,
            "enabled_plugins": enabled_count,
            "total_tools": total_tools,
            "total_executions": total_execs,
            "successful_executions": success_count,
            "failed_executions": error_count,
            "blocked_executions": blocked_count,
            "success_rate_percent": round((success_count / total_execs * 100), 1) if total_execs > 0 else 100.0,
            "average_duration_ms": avg_duration,
        }

    # ---------------------------------------------------------------------------
    # AI Automatic Tool Selection & Intent Grounding
    # ---------------------------------------------------------------------------
    def detect_and_execute_plugin(
        self,
        message: str,
        file_context: Optional[str] = None,
        file_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any], str]]:
        """
        Intelligently detects if the user request requires an active connected plugin tool.
        Returns: (plugin_name, tool_name, result_data, formatted_context_for_llm) or None.
        """
        if not message:
            return None

        msg = message.strip()
        lower_msg = msg.lower()

        # 1. Check Calculator Plugin Intent
        calc_plugin = self.plugins.get("calculator")
        if calc_plugin and calc_plugin.is_connected and calc_plugin.is_enabled:
            # Check unit conversion patterns (e.g. "convert 50 km to miles", "100 c in f")
            unit_match = re.search(
                r"\b(?:convert|change|what is)\s+([0-9.]+)\s*([a-zA-Z]+)\s+(?:to|in|into)\s+([a-zA-Z]+)\b",
                msg,
                re.IGNORECASE,
            )
            if unit_match:
                val, u1, u2 = unit_match.group(1), unit_match.group(2), unit_match.group(3)
                res = self.execute_tool("calculator", "convert_units", {"value": float(val), "from_unit": u1, "to_unit": u2}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: Calculator & Math Engine]\nResult: {res.get('summary')}\nRaw Data: {json.dumps(res.get('data'))}\n[END PLUGIN TOOL]"
                    return calc_plugin.name, "convert_units", res, context_str

            # Check direct math / calculation expressions (e.g. "calculate 45 * 38 + sqrt(144)", "what is 2^10", "45 * 38")
            math_prefix_match = re.search(r"^(?:calculate|compute|solve|eval|what is|evaluate)?\s*([0-9\s\+\-\*\/\^\(\)\.\%eEpisqrtcbrtlogsincoatanfactorial\,]+)$", msg, re.IGNORECASE)
            # Only trigger if it contains mathematical operators
            if math_prefix_match and any(op in msg for op in ["+", "*", "/", "^", "sqrt", "sin", "cos", "tan", "log", "factorial"]):
                raw_expr = math_prefix_match.group(1).strip()
                # Ensure it's not just a year or single number
                if len(raw_expr) > 2 and any(char.isdigit() for char in raw_expr):
                    res = self.execute_tool("calculator", "calculate", {"expression": raw_expr}, session_id=session_id)
                    if res.get("success"):
                        context_str = f"[PLUGIN TOOL EXECUTION: Calculator & Math Engine]\nResult: {res.get('summary')}\n[END PLUGIN TOOL]"
                        return calc_plugin.name, "calculate", res, context_str

        # 2. Check Azure Blob Storage Plugin Intent
        blob_plugin = self.plugins.get("azure_blob")
        if blob_plugin and blob_plugin.is_connected and blob_plugin.is_enabled:
            if re.search(r"\b(list (?:my )?(?:azure )?(?:storage )?blobs|show (?:my )?azure files|check azure (?:blob|storage))\b", lower_msg):
                res = self.execute_tool("azure_blob", "list_storage_blobs", {}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: Azure Blob Storage]\nBlobs in container: {json.dumps(res.get('blobs'))}\nSummary: {res.get('summary')}\n[END PLUGIN TOOL]"
                    return blob_plugin.name, "list_storage_blobs", res, context_str

            if re.search(r"\b(azure storage status|test azure blob connection|is azure blob connected)\b", lower_msg):
                res = self.execute_tool("azure_blob", "check_storage_status", {}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: Azure Blob Storage]\nStatus: {res.get('status')}\nConnected: {res.get('connected')}\n[END PLUGIN TOOL]"
                    return blob_plugin.name, "check_storage_status", res, context_str

        # 3. Check File Analysis Plugin Intent
        file_plugin = self.plugins.get("file_analysis")
        if file_plugin and file_plugin.is_connected and file_plugin.is_enabled:
            if re.search(r"\b(list (?:my )?uploaded (?:files|docs|documents)|what files have i uploaded)\b", lower_msg):
                res = self.execute_tool("file_analysis", "list_uploaded_files", {}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: Document & File Analysis]\nUploaded files: {json.dumps(res.get('files'))}\n[END PLUGIN TOOL]"
                    return file_plugin.name, "list_uploaded_files", res, context_str

        # 4. Check Explicit Web Search Plugin Intent
        web_plugin = self.plugins.get("web_search")
        if web_plugin and web_plugin.is_connected and web_plugin.is_enabled:
            search_match = re.search(r"^(?:search the web for|web search for|google|search web:?)\s+(.+)$", msg, re.IGNORECASE)
            if search_match:
                s_query = search_match.group(1).strip()
                res = self.execute_tool("web_search", "search_web", {"query": s_query, "num_results": 5}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: Web Search & Grounding]\nQuery: {s_query}\nResults:\n{res.get('summary')}\n[END PLUGIN TOOL]"
                    return web_plugin.name, "search_web", res, context_str

        # 5. Check GitHub Plugin Intent (Upload files, list repos, inspect files)
        github_plugin = self.plugins.get("github")
        if github_plugin and github_plugin.is_connected and github_plugin.is_enabled:
            # Check file upload/commit patterns
            # e.g., "upload file app.py to github repo my_cloud_bot", "upload test.txt to github", "commit README.md to repo pranav/bot"
            upload_match = re.search(
                r"\b(?:upload|commit|push|add)\s+(?:file\s+)?([a-zA-Z0-9_.\-\/\\]+)\s+(?:to\s+(?:my\s+)?(?:github\s+)?(?:repo(?:sitory)?\s+)?([a-zA-Z0-9_.\-\/]+)|to\s+github)\b",
                msg,
                re.IGNORECASE,
            )
            if upload_match or any(kw in lower_msg for kw in ["upload to github", "upload file to github", "push to github", "commit to github"]):
                target_file = upload_match.group(1) if upload_match else (file_name or "sample_file.py")
                target_repo = upload_match.group(2) if (upload_match and upload_match.group(2)) else (github_plugin.config.get("repo") or "my_cloud_bot")

                # Clean file path
                clean_path = target_file.strip().replace("\\", "/").split("/")[-1]
                if not clean_path:
                    clean_path = "sample_code.py"

                # Check if content is provided in prompt (e.g. "with content: ...")
                custom_content = ""
                content_match = re.search(r"(?:with\s+content|body|code)[:\s]+([\s\S]+)", msg, re.IGNORECASE)
                if content_match:
                    custom_content = content_match.group(1).strip()
                elif file_context:
                    custom_content = file_context

                commit_msg = f"Add {clean_path} via Cloud AI Chatbot Plugin"

                res = self.execute_tool(
                    "github",
                    "upload_file_to_repo",
                    {
                        "repo": target_repo,
                        "file_path": clean_path,
                        "content": custom_content,
                        "file_name": file_name or clean_path,
                        "commit_message": commit_msg,
                        "branch": "main",
                    },
                    context={"file_content": file_context} if file_context else None,
                    session_id=session_id,
                )
                if res.get("success"):
                    context_str = (
                        f"[PLUGIN TOOL EXECUTION: GitHub Integration]\n"
                        f"Action: Upload & Commit File\n"
                        f"Status: Success\n"
                        f"Target Repository: {res.get('repo')}\n"
                        f"File: {res.get('file_path')} (Branch: {res.get('branch')})\n"
                        f"Commit SHA: {res.get('commit_sha')}\n"
                        f"Commit Message: {res.get('commit_message')}\n"
                        f"File URL: {res.get('file_url')}\n"
                        f"Summary: {res.get('summary')}\n"
                        f"[END PLUGIN TOOL]"
                    )
                    return github_plugin.name, "upload_file_to_repo", res, context_str

            # Check list repositories pattern
            if re.search(r"\b(list (?:my )?(?:github )?repos(?:itories)?|show (?:my )?github repos)\b", lower_msg):
                res = self.execute_tool("github", "list_repositories", {}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: GitHub Integration]\nRepositories: {json.dumps(res.get('repos'))}\nSummary: {res.get('summary')}\n[END PLUGIN TOOL]"
                    return github_plugin.name, "list_repositories", res, context_str

            # Check list contents / files in repository
            repo_files_match = re.search(r"\b(?:list|show|get)\s+files\s+(?:in|from)\s+(?:github\s+repo(?:sitory)?\s+)?([a-zA-Z0-9_.\-\/]+)\b", msg, re.IGNORECASE)
            if repo_files_match:
                tgt_repo = repo_files_match.group(1).strip()
                res = self.execute_tool("github", "list_repo_contents", {"repo": tgt_repo}, session_id=session_id)
                if res.get("success"):
                    context_str = f"[PLUGIN TOOL EXECUTION: GitHub Integration]\nRepo Contents: {json.dumps(res.get('items'))}\nSummary: {res.get('summary')}\n[END PLUGIN TOOL]"
                    return github_plugin.name, "list_repo_contents", res, context_str

        return None


# Global singleton instance
plugin_manager = PluginManager()
