"""
OpenRouter / Gemini API client for the Cloud-Based AI Chatbot.
High Performance Cloud Computing Project.

Features:
- OpenAI-compatible Python SDK connected to OpenRouter API (https://openrouter.ai/api/v1)
- Currently supported Google Gemini Flash model: google/gemini-2.5-flash
- Smart Web search grounding for live facts when no document is attached (avoids 402 in-flight budget exhaustion)
- Multimodal image question-answering via base64 data URLs
- Document text context integration for PDF, TXT, and DOCX files
- Defensive error handling: 401 Auth, 402 Budget, 429 Rate Limits, 404 Model, Network errors
"""

import os
import base64
import logging
from typing import List, Dict, Optional, Any, cast

from dotenv import load_dotenv
load_dotenv()

import openai
from openai import OpenAI, OpenAIError, APIError, RateLimitError, AuthenticationError, APIConnectionError, NotFoundError, APIStatusError

logger = logging.getLogger("chatbot.client")

# Active verified OpenRouter model for Gemini Flash.
DEFAULT_MODEL = "google/gemini-3.7-flash"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_INSTRUCTION = """You are a modern, helpful, smart, and friendly AI assistant.

Interaction Rules:
1. Natural Greetings:
   - For simple greetings (such as "hello", "hi", "hey", "good morning", "how are you"), respond ONLY with a short, warm, and natural greeting (e.g., "Hello! 👋 How can I help you today?").
   - NEVER introduce yourself with long project titles, college project descriptions, or unsolicited disclaimers. Keep greetings strictly to 1 or 2 concise sentences.
2. Direct Answers:
   - Answer the user's specific request directly and concisely without conversational filler.
3. Technical & General Knowledge:
   - Provide clear, well-structured explanations using clean Markdown (bold text, bullet points, syntax-highlighted code blocks).
4. Current Events & Live Information:
   - For recent facts, news, sports, politics, or time-sensitive events, provide accurate, up-to-date information.
5. Attached Document & Multimodal Analysis:
   - When a document is attached under [ATTACHED DOCUMENT], answer directly based on the uploaded content.
   - When an image is attached, inspect the image and describe or answer questions about its visual elements.
"""


class GeminiClientError(Exception):
    """Custom exception raised when the AI client encounters an issue."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiClient:
    """
    Client for interacting with Google Gemini models hosted on OpenRouter
    using the official OpenAI-compatible Python SDK.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        self.enable_web_search = os.getenv("ENABLE_WEB_SEARCH", "true").lower() in ("true", "1", "yes")

        self.gemini_direct_key = os.getenv("GEMINI_API_KEY")
        self._genai_model: Optional[Any] = None
        if self.gemini_direct_key and self.gemini_direct_key.startswith("AIzaSy"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_direct_key)
                self._genai_model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=SYSTEM_INSTRUCTION
                )
                logger.info("Configured direct Google Gemini API client (Gemini 2.0 Flash).")
            except Exception as e:
                logger.warning("Failed to initialize direct Google Gemini: %s", e)

        self._client: Optional[OpenAI] = None
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                self._client = OpenAI(
                    base_url=OPENROUTER_BASE_URL,
                    api_key=self.api_key,
                    default_headers={
                        "HTTP-Referer": "https://github.com/cloud-ai-chatbot",
                        "X-Title": "Cloud-Based AI Chatbot Mini Project",
                    },
                )
            except Exception as e:
                logger.error("Failed to initialize OpenAI client for OpenRouter: %s", type(e).__name__)

    def _get_client(self) -> OpenAI:
        """Lazily initialize or return client with validation."""
        if not self.api_key or self.api_key.startswith("your_") or "change-me" in self.api_key:
            if not self._genai_model:
                raise GeminiClientError(
                    "OPENROUTER_API_KEY or GEMINI_API_KEY is not configured. Please add a valid API key to your .env file.",
                    status_code=401,
                )

        if self._client is None and self.api_key:
            try:
                self._client = OpenAI(
                    base_url=OPENROUTER_BASE_URL,
                    api_key=self.api_key,
                    default_headers={
                        "HTTP-Referer": "https://github.com/cloud-ai-chatbot",
                        "X-Title": "Cloud-Based AI Chatbot Mini Project",
                    },
                )
            except Exception as e:
                if not self._genai_model:
                    raise GeminiClientError(f"Could not initialize OpenRouter client: {str(e)}", status_code=500)

        return self._client

        return self._client

    def _prepare_request(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        file_text_context: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
        model: Optional[str] = None,
        effort: Optional[str] = "medium",
        max_tokens_override: Optional[int] = None,
        use_web_search_override: Optional[bool] = None,
    ):
        """Prepares client, messages, parameters, and tokens for OpenAI-compatible request."""
        client = self._get_client()

        # Build OpenAI chat completion messages array
        messages: List[Dict] = [
            {"role": "system", "content": SYSTEM_INSTRUCTION}
        ]

        # Append past conversation history
        if history:
            for turn in history:
                role = "user" if turn.get("role") == "user" else "assistant"
                text = turn.get("text", "").strip()
                if text:
                    messages.append({"role": role, "content": text})

        # Construct current user message content
        user_content_parts = []

        # 1. Document Context (if PDF/TXT/DOCX attached)
        if file_text_context:
            doc_context_text = (
                "[ATTACHED DOCUMENT]\n"
                "The user has uploaded a document for analysis. Use the content below to answer their request:\n\n"
                f"{file_text_context}\n\n"
                "[END ATTACHED DOCUMENT]\n\n"
            )
            user_content_parts.append({"type": "text", "text": doc_context_text})

        # 2. Multimodal Image (if image file attached)
        if image_bytes and image_mime:
            try:
                b64_img = base64.b64encode(image_bytes).decode("utf-8")
                image_data_url = f"data:{image_mime};base64,{b64_img}"
                user_content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url,
                        "detail": "auto",
                    }
                })
            except Exception as e:
                logger.error("Error encoding image to base64: %s", e)
                raise GeminiClientError("Failed to process attached image for AI analysis.", status_code=400)

        # 3. User question / prompt text
        user_content_parts.append({"type": "text", "text": message})

        # Add current user message to conversation list
        if not (image_bytes and image_mime):
            combined_text = ""
            if file_text_context:
                combined_text += (
                    f"[ATTACHED DOCUMENT]\n{file_text_context}\n[END ATTACHED DOCUMENT]\n\n"
                )
            combined_text += message
            messages.append({"role": "user", "content": combined_text})
        else:
            messages.append({"role": "user", "content": user_content_parts})

        # Configure OpenRouter model selection
        model_map = {
            "gemini-3.7-flash": "google/gemini-3.7-flash",
            "gemini-3.6-flash": "google/gemini-3.6-flash",
            "gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite",
            "gemini-2.5-flash": "google/gemini-2.5-flash",
            "google/gemini-3.7-flash": "google/gemini-3.7-flash",
            "google/gemini-3.6-flash": "google/gemini-3.6-flash",
            "google/gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite",
            "google/gemini-2.5-flash": "google/gemini-2.5-flash",
        }
        model_to_use = model_map.get(model, model) if model else self.model
        extra_body = {}

        # Configure Reasoning Effort (low, medium, high)
        valid_efforts = ("low", "medium", "high")
        effort_level = effort.lower() if (effort and effort.lower() in valid_efforts) else "medium"
        extra_body["reasoning"] = {"effort": effort_level}
        
        # SMART WEB SEARCH: Only enable web search plugin for text queries when NO document or image is attached.
        if use_web_search_override is not None:
            use_web_search = use_web_search_override
        else:
            use_web_search = self.enable_web_search and not file_text_context and not image_bytes

        if use_web_search:
            extra_body["plugins"] = [{"id": "web"}]

        # Token cap tailored to effort level or override
        if max_tokens_override:
            max_tokens = max_tokens_override
        else:
            base_tokens = {"low": 500, "medium": 700, "high": 850}.get(effort_level, 700)
            max_tokens = min(base_tokens, 700) if (file_text_context or image_bytes) else base_tokens

        return client, model_to_use, messages, extra_body, max_tokens, effort_level, use_web_search

    def generate_reply(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        file_text_context: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
        model: Optional[str] = None,
        effort: Optional[str] = "medium",
        max_tokens_override: Optional[int] = None,
        use_web_search_override: Optional[bool] = None,
    ) -> str:
        """
        Generates an AI response given a user message, optional conversation history,
        optional document context, optional image bytes, optional model override,
        and optional reasoning effort ("low", "medium", "high").

        Returns:
            str: AI response text in Markdown format.
        """
        client, model_to_use, messages, extra_body, max_tokens, effort_level, use_web_search = self._prepare_request(
            message=message,
            history=history,
            file_text_context=file_text_context,
            image_bytes=image_bytes,
            image_mime=image_mime,
            model=model,
            effort=effort,
            max_tokens_override=max_tokens_override,
            use_web_search_override=use_web_search_override,
        )

        try:
            logger.info("Sending request to OpenRouter (model: %s, effort: %s, web_search: %s, max_tokens: %d)", model_to_use, effort_level, use_web_search, max_tokens)
            
            response = cast(
                Any,
                client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens,
                    extra_body=extra_body if extra_body else None,
                )
            )

            if not response or not response.choices:
                raise GeminiClientError("The AI model returned an empty response. Please try again.", status_code=502)

            choice_msg = response.choices[0].message
            reply_text = choice_msg.content

            # Handle models where response content is inside reasoning or message attributes
            if not reply_text:
                if hasattr(choice_msg, "reasoning") and choice_msg.reasoning:
                    reply_text = choice_msg.reasoning
                else:
                    raise GeminiClientError("The AI returned no text content.", status_code=502)

            return reply_text.strip()

        except AuthenticationError as e:
            logger.error("OpenRouter Authentication Error (401)")
            raise GeminiClientError(
                "Invalid or expired OpenRouter API Key (401). Please check OPENROUTER_API_KEY in your .env file.",
                status_code=401,
            ) from e

        except RateLimitError as e:
            logger.warning("OpenRouter Rate Limit Exceeded (429)")
            raise GeminiClientError(
                "AI rate limit or credit quota exceeded (429). Please wait a moment or check your OpenRouter account balance at openrouter.ai/settings/credits.",
                status_code=429,
            ) from e

        except NotFoundError as e:
            logger.error("OpenRouter Model Not Found (404): %s", model_to_use)
            raise GeminiClientError(
                f"The AI model '{model_to_use}' was not found or is unavailable on OpenRouter (404). Check OPENROUTER_MODEL in .env.",
                status_code=404,
            ) from e

        except APIConnectionError as e:
            logger.error("OpenRouter API Connection Error: %s", e)
            raise GeminiClientError(
                "Could not connect to OpenRouter servers. Please verify your internet connection and network settings.",
                status_code=503,
            ) from e

        except APIStatusError as e:
            status_code = getattr(e, "status_code", 502)
            err_str = str(e).lower()
            if status_code == 402 or "credits" in err_str or "in_flight" in err_str or "afford" in err_str:
                logger.warning("OpenRouter Credit/Budget Limit (402): %s. Attempting self-healing recovery...", e)
                
                # 1. Check if OpenRouter specified exact affordable tokens
                import re
                afford_match = re.search(r"can only afford (\d+)", str(e))
                if afford_match:
                    affordable = int(afford_match.group(1))
                    reduced_tokens = max(10, affordable - 1)
                else:
                    reduced_tokens = 50
                
                try:
                    logger.info("Retrying with affordable max_tokens=%d without web plugin...", reduced_tokens)
                    retry_resp = cast(
                        Any,
                        client.chat.completions.create(
                            model=model_to_use,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=reduced_tokens,
                        )
                    )
                    if retry_resp and retry_resp.choices and retry_resp.choices[0].message.content:
                        return retry_resp.choices[0].message.content.strip()
                except Exception as retry_err:
                    logger.warning("Budget reduction retry failed: %s", retry_err)

                # 2. Fallback to free OpenRouter models if credits are completely exhausted (skip for documents to avoid 15s delay)
                if not (image_bytes and image_mime) and not file_text_context:
                    free_models = [
                        "nvidia/nemotron-3.5-lightning:free",
                        "liquid/lfm-2.5-2.6b:free",
                    ]
                    for fallback_model in free_models:
                        try:
                            logger.info("Attempting free fallback model: %s", fallback_model)
                            fb_resp = cast(
                                Any,
                                client.chat.completions.create(
                                    model=fallback_model,
                                    messages=messages,
                                    temperature=0.7,
                                    max_tokens=350,
                                )
                            )
                            if fb_resp and fb_resp.choices:
                                raw_text = (
                                    getattr(fb_resp.choices[0].message, "content", None)
                                    or getattr(fb_resp.choices[0].message, "reasoning", None)
                                )
                                if raw_text and raw_text.strip():
                                    return raw_text.strip()
                        except Exception as fb_err:
                            logger.warning("Fallback model %s failed: %s", fallback_model, fb_err)

                # Try Google Gemini direct API if configured
                if self._genai_model:
                    try:
                        logger.info("Falling back to direct Google Gemini API...")
                        prompt_content = []
                        if file_text_context:
                            prompt_content.append(f"[ATTACHED DOCUMENT CONTENT]:\n{file_text_context}")
                        prompt_content.append(f"User Request: {message}")
                        res = self._genai_model.generate_content(prompt_content)
                        if res and res.text:
                            return res.text.strip()
                    except Exception as g_err:
                        logger.warning("Google Gemini direct fallback failed: %s", g_err)

                raise GeminiClientError(
                    "OpenRouter credit budget limit reached (402). Your account balance is low. Please wait a moment for in-flight requests to settle, or top up credits at openrouter.ai/settings/credits.",
                    status_code=402,
                ) from e

            logger.error("OpenRouter API Status Error (%d): %s", status_code, getattr(e, "message", str(e)))
            raise GeminiClientError(
                f"OpenRouter service error ({status_code}): {getattr(e, 'message', str(e))}",
                status_code=status_code,
            ) from e

        except GeminiClientError:
            raise

        except Exception as e:
            logger.exception("Unexpected error in OpenRouter AI client")
            raise GeminiClientError(
                f"Unexpected error communicating with AI: {str(e)}",
                status_code=500,
            ) from e

    def generate_reply_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        file_text_context: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
        model: Optional[str] = None,
        effort: Optional[str] = "medium",
    ):
        """
        Streams AI response chunks in real-time.
        Yields:
            str: incremental response delta text chunks.
        """
        client, model_to_use, messages, extra_body, max_tokens, effort_level, use_web_search = self._prepare_request(
            message=message,
            history=history,
            file_text_context=file_text_context,
            image_bytes=image_bytes,
            image_mime=image_mime,
            model=model,
            effort=effort,
        )

        try:
            logger.info(
                "Sending streaming request to OpenRouter (model: %s, effort: %s, web_search: %s, max_tokens: %d)",
                model_to_use, effort_level, use_web_search, max_tokens
            )
            stream_response = cast(
                Any,
                client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens,
                    extra_body=extra_body if extra_body else None,
                    stream=True,
                )
            )

            has_yielded = False
            for chunk in stream_response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None) or ""
                    if not content and hasattr(delta, "reasoning"):
                        content = getattr(delta, "reasoning", "") or ""
                    if content:
                        has_yielded = True
                        yield content

            if not has_yielded:
                # If stream returned no content, try single call fallback
                reply = self.generate_reply(
                    message=message,
                    history=history,
                    file_text_context=file_text_context,
                    image_bytes=image_bytes,
                    image_mime=image_mime,
                    model=model,
                    effort=effort,
                )
                yield reply

        except GeminiClientError:
            raise
        except Exception as e:
            logger.warning("Streaming encountered an issue: %s. Trying direct reply fallback...", e)
            try:
                reply = self.generate_reply(
                    message=message,
                    history=history,
                    file_text_context=file_text_context,
                    image_bytes=image_bytes,
                    image_mime=image_mime,
                    model=model,
                    effort=effort,
                )
                if reply and reply.strip():
                    yield reply
            except Exception as fb_err:
                if isinstance(fb_err, GeminiClientError):
                    raise fb_err
                status_code = getattr(e, "status_code", 500)
                raise GeminiClientError(f"Streaming error: {str(e)}", status_code=status_code) from fb_err