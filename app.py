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

import os
import logging
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv

from utils.file_processor import (
    validate_file,
    extract_text_from_file,
    is_image_file,
    FileValidationError,
)
from utils.gemini_client import GeminiClient, GeminiClientError

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
            {"id": "google/gemini-3.1-flash-lite", "label": "Gemini 3.1 Flash Lite", "badge": "Ultra Fast"}
        ],
        "effort_levels": ["low", "medium", "high"],
        "web_search": gemini_client.enable_web_search,
        "max_upload_size_mb": 10,
    }), 200


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handles a chat turn.
    Accepts multipart/form-data with:
        message : str (required unless file attached)
        file    : uploaded file (optional: PDF, TXT, DOCX, PNG, JPG, WEBP)
    """
    try:
        user_message = request.form.get("message", "").strip()
        uploaded_file = request.files.get("file")

        if not user_message and not uploaded_file:
            return jsonify({"error": "Please enter a message or attach a supported file."}), 400

        # Retrieve rolling conversation history for session or client-provided history
        history = []
        custom_history = request.form.get("history")
        if custom_history:
            try:
                import json
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
                return jsonify({"error": str(e)}), 400

            file_name = uploaded_file.filename
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
            uploaded_file.save(save_path)
            logger.info("Processed file upload: %s", file_name)

            if is_image_file(file_name):
                # Image file: read bytes and pass to multimodal vision
                try:
                    with open(save_path, "rb") as f:
                        image_bytes = f.read()
                    image_mime = uploaded_file.mimetype or "image/png"
                except Exception as e:
                    logger.error("Failed to read uploaded image: %s", e)
                    return jsonify({"error": f"Could not read uploaded image: {str(e)}"}), 400
            else:
                # Document file (PDF, TXT, DOCX): extract text
                try:
                    file_context = extract_text_from_file(save_path)
                except Exception as e:
                    logger.error("Failed to extract document text: %s", e)
                    return jsonify({"error": f"Could not process document: {str(e)}"}), 400

        # If user uploaded a file without custom prompt, generate standard prompt
        if not user_message and uploaded_file:
            if image_bytes:
                user_message = "Please analyze and describe this image in detail."
            else:
                user_message = "Please provide a comprehensive summary and key takeaways from this uploaded document."

        # Extract optional model selection and reasoning effort level
        model_param = request.form.get("model", "").strip() or None
        effort_param = request.form.get("effort", "medium").strip() or "medium"

        # Request reply from OpenRouter / Gemini
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
            logger.warning("AI Client error (%d): %s", e.status_code, e.message)
            return jsonify({"error": e.message}), e.status_code

        # Update session history (store only text to prevent cookie size overflow)
        history_item_user = user_message
        if file_name:
            history_item_user += f" [Attached file: {file_name}]"

        history.append({"role": "user", "text": history_item_user})
        history.append({"role": "model", "text": reply})
        session["history"] = history[-20:]  # Retain last 20 conversation turns
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


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    """Clears conversation history from session."""
    session.pop("history", None)
    return jsonify({"status": "cleared", "message": "Conversation history cleared successfully."}), 200


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
