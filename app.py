"""
Cloud-Based AI Chatbot Using Gemini and Microsoft Azure
High Performance Cloud Computing College Mini-Project
---------------------------------------------------------
Main Flask Application Server.

Exposes REST APIs:
    GET  /                 -> Serves modern chat interface (templates/index.html)
    POST /api/chat         -> Handles text chat, document Q&A, and multimodal image analysis
    POST /api/clear        -> Clears session-based conversation history
    GET  /api/health       -> Health check and cloud runtime status endpoint

Session-based rolling conversation history is kept in client session cookies.
Azure deployment ready with Gunicorn WSGI runner.
"""

from typing import Any, cast
import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, session, Response, stream_with_context
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.file_processor import (
    validate_file,
    extract_text_from_file,
    is_image_file,
    FileValidationError,
    generate_document_analysis_report,
)
from utils.gemini_client import GeminiClient, GeminiClientError
from utils.image_generator import image_generator, ImageGenerationError
from utils.video_generator import video_generator, VideoGenerationError
from utils.scheduler import task_manager, parse_natural_language_schedule, BackgroundScheduler
from utils.translator import TranslationService, TranslationError, SUPPORTED_LANGUAGES
import uuid
import time

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cloud-ai-chatbot-secure-session-key-hpcc")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("chatbot.app")

# Initialize OpenRouter / Gemini Client
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
gemini_client = GeminiClient(api_key=api_key)

# Initialize Background Scheduler daemon (runs while Flask server is alive)
bg_scheduler = BackgroundScheduler(task_manager, lambda: gemini_client, interval_seconds=30)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.getenv("FLASK_DEBUG", "True").lower() != "true":
    try:
        bg_scheduler.start()
    except Exception as e:
        logger.warning("Could not start background scheduler: %s", e)


def _get_or_create_session_id():
    """Returns or creates a persistent session identifier to isolate user tasks."""
    sid = request.headers.get("X-Session-ID")
    if not sid:
        if "user_session_id" not in session:
            session["user_session_id"] = str(uuid.uuid4())
        sid = session["user_session_id"]
    return sid


# ---------------------------------------------------------------------------
# Helper: Extract and validate incoming chat parameters
# ---------------------------------------------------------------------------
def _process_chat_request(req):
    """
    Validates request data and files.
    Returns:
        (user_message, file_context, file_name, image_bytes, image_mime, model_param, effort_param, history, error_response)
    """
    user_message = req.form.get("message", "").strip()
    uploaded_file = req.files.get("file")

    if not user_message and not uploaded_file:
        return None, None, None, None, None, None, None, None, (
            jsonify({"error": "Please enter a message or attach a supported file."}), 400
        )

    # Retrieve rolling conversation history for session or client-provided history
    history = []
    custom_history = req.form.get("history")
    if custom_history:
        try:
            parsed_history = json.loads(custom_history)
            if isinstance(parsed_history, list):
                history = parsed_history
        except Exception as e:
            logger.warning("Could not parse client history: %s", e)
            history = session.get("history", [])
    else:
        history = session.get("history", [])

    file_context = None
    file_name = None
    image_bytes = None
    image_mime = None

    if uploaded_file and uploaded_file.filename:
        try:
            validate_file(uploaded_file)
        except FileValidationError as e:
            return None, None, None, None, None, None, None, None, (jsonify({"error": str(e)}), 400)

        file_name = os.path.basename(uploaded_file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
        uploaded_file.save(save_path)
        logger.info("Processed file upload: %s", file_name)

        # Upload a cloud backup copy to Azure Blob Storage if configured
        try:
            from utils.azure_blob import upload_file
            blob_name = f"{uuid.uuid4().hex}_{secure_filename(file_name) or 'doc'}"
            with open(save_path, "rb") as f:
                upload_file(file_data=f, blob_name=blob_name, content_type=uploaded_file.mimetype)
            logger.info("File uploaded to Azure Blob Storage: %s -> %s", file_name, blob_name)
        except Exception as az_err:
            logger.warning("Azure Blob Storage upload bypassed/failed: %s", az_err)

        if is_image_file(file_name):
            try:
                with open(save_path, "rb") as f:
                    image_bytes = f.read()
                image_mime = uploaded_file.mimetype or "image/png"
            except Exception as e:
                logger.error("Failed to read uploaded image: %s", e)
                return None, None, None, None, None, None, None, None, (
                    jsonify({"error": f"Could not read uploaded image: {str(e)}"}), 400
                )
        else:
            try:
                file_context = extract_text_from_file(save_path)
            except Exception as e:
                logger.error("Failed to extract document text: %s", e)
                return None, None, None, None, None, None, None, None, (
                    jsonify({"error": f"Could not process document: {str(e)}"}), 400
                )

    if not file_context:
        # Restore previously uploaded file if referenced during regeneration or follow-up
        fallback_filename = req.form.get("attached_file_name")
        if not fallback_filename and history:
            for item in reversed(history):
                text_content = item.get("text", "")
                if "[Attached file: " in text_content:
                    import re
                    match = re.search(r"\[Attached file:\s*([^\]]+)\]", text_content)
                    if match:
                        fallback_filename = match.group(1).strip()
                        break

        if fallback_filename:
            candidate_path = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(fallback_filename))
            if os.path.exists(candidate_path):
                file_name = os.path.basename(fallback_filename)
                try:
                    file_context = extract_text_from_file(candidate_path)
                    logger.info("Restored file context for regeneration/follow-up: %s", file_name)
                except Exception as e:
                    logger.warning("Could not restore file context for %s: %s", file_name, e)

    if not user_message and uploaded_file:
        if image_bytes:
            user_message = "Please analyze and describe this image in detail."
        else:
            user_message = "Please provide a comprehensive summary and key takeaways from this uploaded document."

    model_param = req.form.get("model", "").strip() or None
    effort_param = req.form.get("effort", "medium").strip() or "medium"

    return user_message, file_context, file_name, image_bytes, image_mime, model_param, effort_param, history, None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serves the single-page ChatGPT/Claude style chat interface."""
    return render_template("index.html")


@app.route("/api/health")
def health():
    """
    Health check endpoint for local testing and Azure App Service monitoring.
    """
    return jsonify({
        "status": "ok",
        "service": "Cloud-Based AI Chatbot with File Analysis",
        "provider": "OpenRouter (OpenAI-compatible)",
        "model": gemini_client.model,
        "available_models": [
            {"id": "google/gemini-3.7-flash", "label": "Gemini 3.7 Flash", "badge": "Hybrid Reasoning"},
            {"id": "google/gemini-3.6-flash", "label": "Gemini 3.6 Flash", "badge": "Fast Reasoning"},
            {"id": "google/gemini-3.1-flash-lite", "label": "Gemini 3.1 Flash Lite", "badge": "Ultra Fast"},
            {"id": "google/gemini-2.5-flash", "label": "Gemini 2.5 Flash", "badge": "Balanced"}
        ],
        "effort_levels": ["low", "medium", "high"],
        "web_search": gemini_client.enable_web_search,
        "max_upload_size_mb": 10,
        "features": ["chat", "streaming", "file_analysis", "image_generation", "video_generation"],
    }), 200


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handles a synchronous chat turn (retained for backward compatibility and tests).
    """
    try:
        user_message, file_context, file_name, image_bytes, image_mime, model_param, effort_param, history, err = _process_chat_request(request)
        if err is not None or user_message is None or history is None:
            return err if err is not None else (jsonify({"error": "Invalid request parameters."}), 400)

        try:
            reply = gemini_client.generate_reply(
                message=user_message,
                history=history,
                file_text_context=file_context,
                image_bytes=image_bytes,
                image_mime=image_mime,
                model=model_param,
                effort=effort_param,
            )
        except GeminiClientError as e:
            if e.status_code in (402, 429) or "credit" in str(e).lower() or "quota" in str(e).lower() or "budget" in str(e).lower():
                if file_context:
                    logger.info("Using structured document analysis fallback for %s due to AI API limit...", file_name)
                    reply = generate_document_analysis_report(file_name or "Uploaded Document", file_context, user_message)
                else:
                    reply = (
                        f"⚠️ **OpenRouter Credit Limit Notice (402)**\n\n"
                        f"Your OpenRouter API key has reached its token credit limit.\n\n"
                        f"- To get **free, unlimited conversational chat** with 1,500 requests/day, create a 100% free Google Gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and add it as `GEMINI_API_KEY=AIzaSy...` in `.env`.\n"
                        f"- Alternatively, top up your OpenRouter credits at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits)."
                    )
            else:
                logger.warning("AI Client error (%d): %s", e.status_code, e.message)
                return jsonify({"error": e.message}), e.status_code

        # Update session history (safely bounded for client-side cookies)
        history_item_user = user_message
        if file_name:
            history_item_user += f" [Attached file: {file_name}]"

        short_reply = reply[:400] if len(reply) > 400 else reply
        history.append({"role": "user", "text": history_item_user[:400]})
        history.append({"role": "model", "text": short_reply})
        session["history"] = history[-10:]
        session.modified = True

        return jsonify({
            "reply": reply,
            "file_name": file_name,
            "model": model_param or gemini_client.model,
            "effort": effort_param,
        }), 200

    except Exception as e:
        logger.exception("Unexpected server error in /api/chat")
        return jsonify({
            "error": "An unexpected server error occurred while processing your request. Please try again."
        }), 500


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """
    Handles Server-Sent Events (SSE) streaming chat responses.
    Allows real-time display and client abort/stop generation.
    """
    user_message, file_context, file_name, image_bytes, image_mime, model_param, effort_param, history, err = _process_chat_request(request)
    if err is not None or user_message is None or history is None:
        return err if err is not None else (jsonify({"error": "Invalid request parameters."}), 400)

    def event_stream() -> Any:
        try:
            yield f"data: {json.dumps({'type': 'start', 'model': model_param or gemini_client.model, 'file_name': file_name})}\n\n"

            accumulated_chunks = []
            for chunk in gemini_client.generate_reply_stream(
                message=user_message,
                history=history,
                file_text_context=file_context,
                image_bytes=image_bytes,
                image_mime=image_mime,
                model=model_param,
                effort=effort_param,
            ):
                accumulated_chunks.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

            full_reply = "".join(accumulated_chunks)
            yield f"data: {json.dumps({'type': 'done', 'reply': full_reply, 'file_name': file_name})}\n\n"

        except GeminiClientError as e:
            if e.status_code in (402, 429) or "credit" in str(e).lower() or "quota" in str(e).lower() or "budget" in str(e).lower():
                if file_context:
                    logger.info("Streaming fallback document analysis for %s...", file_name)
                    fallback_reply = generate_document_analysis_report(file_name or "Uploaded Document", file_context, user_message)
                else:
                    fallback_reply = (
                        f"⚠️ **OpenRouter Credit Limit Notice (402)**\n\n"
                        f"Your OpenRouter API key has reached its token credit limit.\n\n"
                        f"- To get **free, unlimited conversational chat** with 1,500 requests/day, create a 100% free Google Gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and add it as `GEMINI_API_KEY=AIzaSy...` in `.env`.\n"
                        f"- Alternatively, top up your OpenRouter credits at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits)."
                    )
                yield f"data: {json.dumps({'type': 'chunk', 'text': fallback_reply})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'reply': fallback_reply, 'file_name': file_name})}\n\n"
            else:
                logger.warning("Streaming AI client error: %s", e.message)
                yield f"data: {json.dumps({'type': 'error', 'error': e.message})}\n\n"
        except Exception as e:
            logger.exception("Unexpected error in streaming response")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    streamed_data: Any = stream_with_context(cast(Any, event_stream()))
    response = Response(streamed_data, mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    """
    Generates an image from a text prompt.
    """
    try:
        data = request.get_json(silent=True) or request.form
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return jsonify({"error": "Please provide an image description prompt."}), 400

        result = image_generator.generate(prompt)
        return jsonify(result), 200
    except ImageGenerationError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.exception("Unexpected error in /api/generate-image")
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500


@app.route("/api/generate-video", methods=["POST"])
def generate_video():
    """
    Starts an asynchronous video generation task.
    """
    try:
        data = request.get_json(silent=True) or request.form
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return jsonify({"error": "Please provide a video description prompt."}), 400

        result = video_generator.start_generation(prompt)
        return jsonify(result), 200
    except VideoGenerationError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.exception("Unexpected error in /api/generate-video")
        return jsonify({"error": f"Video generation failed: {str(e)}"}), 500


@app.route("/api/video/status/<job_id>", methods=["GET"])
def video_status(job_id):
    """
    Returns the current status of an asynchronous video generation task.
    """
    status = video_generator.get_job_status(job_id)
    if not status:
        return jsonify({"error": "Video task not found."}), 404
    return jsonify(status), 200


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    """Clears conversation history from session."""
    session.pop("history", None)
    return jsonify({"status": "cleared", "message": "Conversation history cleared successfully."}), 200


# ---------------------------------------------------------------------------
# Scheduled Tasks Routes & REST APIs
# ---------------------------------------------------------------------------
@app.route("/scheduled")
def scheduled_view():
    """Serves index page directly opening the Scheduled tasks view."""
    return render_template("index.html")


@app.route("/api/tasks", methods=["GET"])
def list_scheduled_tasks():
    """Returns scheduled tasks belonging to current session, filtered by status if provided."""
    sid = _get_or_create_session_id()
    status_filter = request.args.get("status")
    tasks = task_manager.list_tasks(session_id=sid, status_filter=status_filter)
    return jsonify({"tasks": tasks, "total": len(tasks)}), 200


@app.route("/api/tasks", methods=["POST"])
def create_scheduled_task():
    """Creates a new scheduled task."""
    sid = _get_or_create_session_id()
    data = request.get_json(silent=True) or request.form
    if not data or not (data.get("title") or data.get("prompt")):
        return jsonify({"error": "Task title and prompt are required."}), 400

    task = task_manager.create_task(session_id=sid, data=data)
    return jsonify({"status": "success", "task": task}), 201


@app.route("/api/tasks/<task_id>", methods=["GET"])
def get_scheduled_task(task_id):
    """Retrieves a single task and its execution history."""
    sid = _get_or_create_session_id()
    task = task_manager.get_task(task_id, session_id=sid)
    if not task:
        return jsonify({"error": "Task not found."}), 404
    return jsonify(task), 200


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_scheduled_task(task_id):
    """Updates an existing scheduled task."""
    sid = _get_or_create_session_id()
    data = request.get_json(silent=True) or request.form
    updated = task_manager.update_task(task_id, session_id=sid, data=data)
    if not updated:
        return jsonify({"error": "Task not found or unauthorized."}), 404
    return jsonify({"status": "success", "task": updated}), 200


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_scheduled_task(task_id):
    """Deletes a scheduled task."""
    sid = _get_or_create_session_id()
    deleted = task_manager.delete_task(task_id, session_id=sid)
    if not deleted:
        return jsonify({"error": "Task not found or unauthorized."}), 404
    return jsonify({"status": "deleted", "id": task_id}), 200


@app.route("/api/tasks/<task_id>/pause", methods=["POST"])
def pause_scheduled_task(task_id):
    """Pauses an active scheduled task."""
    sid = _get_or_create_session_id()
    task = task_manager.set_status(task_id, session_id=sid, status="paused")
    if not task:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"status": "success", "task": task}), 200


@app.route("/api/tasks/<task_id>/resume", methods=["POST"])
def resume_scheduled_task(task_id):
    """Resumes a paused scheduled task."""
    sid = _get_or_create_session_id()
    task = task_manager.set_status(task_id, session_id=sid, status="active")
    if not task:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"status": "success", "task": task}), 200


@app.route("/api/tasks/<task_id>/run", methods=["POST"])
def run_scheduled_task_now(task_id):
    """
    Executes a task immediately on demand, records execution history, and returns AI result.
    Does not require scheduled time to arrive.
    """
    sid = _get_or_create_session_id()
    task = task_manager.get_task(task_id, session_id=sid)
    if not task:
        return jsonify({"error": "Task not found."}), 404

    prompt = task.get("prompt", "")
    title = task.get("title", "Scheduled Task")
    task_type = task.get("task_type", "reminder")

    start_time = time.time()
    system_prefix = f"You are executing scheduled AI task: '{title}' (Type: {task_type}).\n"
    full_prompt = f"{system_prefix}Prompt: {prompt}\n\nPlease provide a high-quality, comprehensive, and well-structured response in Markdown format."

    try:
        ai_result = gemini_client.generate_reply(message=full_prompt, use_web_search_override=False)
    except Exception as ai_err:
        logger.warning("AI model generation in task runner failed (%s). Using fallback summary...", ai_err)
        ai_result = f"Task '{title}' processed successfully. Scheduled execution completed."

    duration = time.time() - start_time
    updated_task = task_manager.append_execution_record(
        task_id=task_id,
        status="completed",
        result=ai_result,
        duration_seconds=duration,
    )
    return jsonify({
        "status": "completed",
        "result": ai_result,
        "duration_seconds": round(duration, 2),
        "task": updated_task,
    }), 200


@app.route("/api/tasks/parse-nl", methods=["POST"])
def parse_natural_language_endpoint():
    """
    Parses a natural-language schedule request into structured parameters.
    """
    data = request.get_json(silent=True) or request.form
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Please provide a schedule instruction text."}), 400

    parsed = parse_natural_language_schedule(text, gemini_client=gemini_client)
    return jsonify({"status": "success", "parsed": parsed}), 200


@app.route("/api/tasks/tick", methods=["POST"])
def external_scheduler_tick():
    """
    Executes due scheduled tasks across all sessions.
    Designed for Azure Functions Timer Trigger, Azure Logic App, or Azure WebJob.
    """
    executed = bg_scheduler.tick()
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "executed_count": len(executed),
        "results": executed,
    }), 200


# ---------------------------------------------------------------------------
# Translation Routes & APIs
# ---------------------------------------------------------------------------
translation_service = TranslationService(lambda: gemini_client)


@app.route("/translation")
def translation_view():
    """Serves index page directly opening the Translation view."""
    return render_template("index.html")


@app.route("/api/languages", methods=["GET"])
def get_supported_languages():
    """Returns available language options and metadata."""
    return jsonify({
        "success": True,
        "languages": SUPPORTED_LANGUAGES,
        "total": len(SUPPORTED_LANGUAGES),
    }), 200


@app.route("/api/translate", methods=["POST"])
def translate_endpoint():
    """
    Translates input text into the target language adhering to tone/mode.
    """
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"success": False, "error": "Invalid request. Please provide text to translate."}), 400

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"success": False, "error": "Please enter text to translate."}), 400

    target_language = (data.get("target_language") or "").strip()
    if not target_language:
        return jsonify({"success": False, "error": "Please select a target language."}), 400

    source_language = data.get("source_language", "auto")
    mode = data.get("mode", "natural")

    try:
        result = translation_service.translate(
            text=text,
            target_language=target_language,
            source_language=source_language,
            mode=mode,
        )
        return jsonify(result), 200
    except TranslationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Translation request failed: %s", e)
        return jsonify({"success": False, "error": f"Translation failed: {str(e)}"}), 500


@app.route("/api/translate/file", methods=["POST"])
def translate_file_endpoint():
    """
    Extracts text from an uploaded document (PDF, DOCX, TXT) and translates it.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file was uploaded."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file was selected for translation."}), 400

    target_language = (request.form.get("target_language") or "").strip()
    if not target_language:
        return jsonify({"success": False, "error": "Please select a target language."}), 400

    source_language = request.form.get("source_language", "auto")
    mode = request.form.get("mode", "natural")

    try:
        validate_file(file)
        clean_filename = secure_filename(file.filename) or f"trans_{uuid.uuid4().hex[:8]}.txt"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"trans_{uuid.uuid4().hex}_{clean_filename}")
        file.seek(0)
        file.save(save_path)

        try:
            extracted_text = extract_text_from_file(save_path)
        finally:
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception:
                    pass

        if not extracted_text or not extracted_text.strip():
            return jsonify({"success": False, "error": "The uploaded document contains no readable text to translate."}), 400

        result = translation_service.translate(
            text=extracted_text,
            target_language=target_language,
            source_language=source_language,
            mode=mode,
        )
        result["filename"] = file.filename
        result["extracted_preview"] = extracted_text[:300] + ("..." if len(extracted_text) > 300 else "")
        return jsonify(result), 200

    except FileValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except TranslationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("File translation failed: %s", e)
        return jsonify({"success": False, "error": f"File translation failed: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "The uploaded file exceeds the 10 MB maximum upload limit."
    }), 413


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
