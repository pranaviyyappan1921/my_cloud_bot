"""
OpenRouter / Gemini API client for the Cloud-Based AI Chatbot.
Provides:
- OpenAI-compatible Python SDK connected to OpenRouter API (https://openrouter.ai/api/v1)
- Real-time Web Search Grounding via OpenRouter web plugin (plugins=[{"id": "web"}])
- Intelligent live-query / current-information intent detection
- Tool-call sanitization (stripping raw internal <|tool_call_start|> markers)
- Multi-tier resilient fallback: Web Search -> Normal Model -> Clean Free Fallback Models -> Direct Gemini
- Safe exponential backoff retries for transient errors (429, 408, 500, 502, 503, 504, network drops)
- Full multimodal vision support (base64 image data URLs)
- Document text context integration for PDF, TXT, and DOCX files
- Universal general-purpose AI assistant system instruction (programming, math, engineering, cloud, documents)
- Clean extraction and preservation of web search citations/sources
- Streaming (SSE) and synchronous chat generation
"""

import os
import re
import time
import base64
import logging
from typing import List, Dict, Optional, Any, Generator, Tuple, cast

from dotenv import load_dotenv
load_dotenv()

import openai
from openai import (
    OpenAI,
    OpenAIError,
    APIError,
    RateLimitError,
    AuthenticationError,
    APIConnectionError,
    NotFoundError,
    APIStatusError,
    APITimeoutError,
)

logger = logging.getLogger("chatbot.client")

# Active verified OpenRouter default model
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-3.7-flash")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
REQUEST_TIMEOUT_SECONDS = 45.0
MAX_RETRIES = 2

# General-purpose AI Assistant instruction
SYSTEM_INSTRUCTION = """You are a highly capable, intelligent, and helpful general-purpose AI assistant.

Core Capabilities:
1. General Knowledge & Reasoning:
   - Provide accurate, comprehensive, and well-reasoned answers across science, history, arts, philosophy, and daily life.
   - For complex questions, provide structured step-by-step explanations.
2. Programming & Technical Computing:
   - Provide clean, efficient, bug-free code with explanations in Python, JavaScript, TypeScript, C, C++, Java, Rust, Go, SQL, HTML/CSS, Bash, and modern frameworks.
   - Use standard Markdown fenced code blocks with appropriate language tags.
3. Mathematics & Engineering:
   - Solve mathematical, physical, engineering, and data science problems with explicit derivations and formulas.
4. Cloud Computing & DevOps:
   - Deep expertise in Microsoft Azure, AWS, Google Cloud, Docker, Kubernetes, Linux, CI/CD, and microservices architecture.
5. Writing & Summarization:
   - Produce concise summaries, essays, translations, reports, and clear bullet-point takeaways.
6. Current Events & Live Information:
   - When web-grounded search data is provided, use the most up-to-date facts and cite relevant sources accurately.
7. Document & Multimodal Analysis:
   - When a document is attached under [ATTACHED DOCUMENT], answer directly based on the uploaded content.
   - When an image is attached, inspect visual features, diagrams, text (OCR), charts, and design elements.

Interaction Style:
- Answer the user's question directly in fluent natural language.
- For simple greetings ("hello", "hi", "hey"), respond with a friendly, natural greeting (1-2 sentences).
- Never output raw tool-calling tags or code tokens like <|tool_call_start|> directly to the user.
- Present information with clean Markdown (headings, bullet points, bold key terms).
"""

# Regex patterns for live / current information queries
LIVE_QUERY_PATTERNS = [
    r"\b(latest|today|current|currently|recent|recently|breaking|trending)\b",
    r"\b(this week|this month|this year|yesterday|tomorrow|tonight)\b",
    r"\b(news|headlines|updates?|announcements?|press release|developments?)\b",
    r"\b(weather|forecast|temperature|climate today)\b",
    r"\b(stock price|share price|market cap|exchange rate|crypto price|bitcoin price|sensex|nifty|nasdaq)\b",
    r"\b(score|scores|match|cricket match|football match|premier league|ipl|world cup|nba|nfl|who won|who is winning)\b",
    r"\b(election|polls|cabinet|minister|president|prime minister now)\b",
    r"\b(new version|release date|latest release|patch notes|changelog)\b",
    r"\b(what happened|what's happening|whats happening)\b",
    r"\b(latest ai news|latest tech news|latest technology news)\b",
]

LIVE_QUERY_REGEX = re.compile("|".join(f"(?:{p})" for p in LIVE_QUERY_PATTERNS), re.IGNORECASE)


def is_live_query(message: str) -> bool:
    """Detects whether a user prompt requires real-time / current web information."""
    if not message:
        return False
    msg = message.strip()
    return bool(LIVE_QUERY_REGEX.search(msg))


def clean_ai_output(text: Optional[str]) -> str:
    """
    Cleans internal tool-call markers, raw google query syntaxes, or internal tokens
    so the end-user always receives clean, human-readable natural language.
    """
    if not text:
        return ""
    # Strip tool call blocks: <|tool_call_start|>...<|tool_call_end|>
    cleaned = re.sub(r"<\|tool_call_start\|>.*?<\|tool_call_end\|>", "", text, flags=re.DOTALL)
    # Strip thoughts: <|thought|>...<|thought_end|> or <thought>...</thought>
    cleaned = re.sub(r"<\|thought\|>.*?<\|thought_end\|>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<thought>.*?</thought>", "", cleaned, flags=re.DOTALL)
    # Strip standalone tool call representations like [google(query=...)] or [read_document(...)]
    cleaned = re.sub(r"\[(?:google|read_document|news|search)\([^\]]*\)[^\]]*\]", "", cleaned, flags=re.DOTALL)
    # Strip remaining special tokens
    cleaned = re.sub(r"<\|[^>]*\|>", "", cleaned)
    return cleaned.strip()


def extract_sources_from_response(response_obj: Any) -> List[Dict[str, str]]:
    """Extracts citations and source metadata from OpenRouter response object if available."""
    sources = []
    try:
        if not response_obj or not getattr(response_obj, "choices", None):
            return sources

        choice = response_obj.choices[0]
        msg = getattr(choice, "message", None)
        if not msg:
            return sources

        # Check for annotations / citations in OpenRouter message object
        annotations = getattr(msg, "annotations", None) or getattr(msg, "citations", None)
        if isinstance(annotations, list):
            for item in annotations:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("link")
                    title = item.get("title") or url
                    if url:
                        sources.append({"title": title, "url": url})

        # Check for plugins output in response metadata
        extra = getattr(response_obj, "extra", None) or getattr(response_obj, "model_extra", None)
        if isinstance(extra, dict):
            citations = extra.get("citations") or []
            for c in citations:
                if isinstance(c, dict) and c.get("url"):
                    sources.append({"title": c.get("title") or c.get("url"), "url": c["url"]})

    except Exception as e:
        logger.debug("Source extraction debug: %s", e)

    return sources


class GeminiClientError(Exception):
    """Custom exception raised when the AI client encounters an issue."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiClient:
    """
    Resilient client for interacting with Google Gemini models hosted on OpenRouter
    using the official OpenAI-compatible Python SDK with real web search grounding,
    safe exponential backoff, and multi-tier fallbacks.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL
        self.enable_web_search = os.getenv("ENABLE_WEB_SEARCH", "true").lower() in ("true", "1", "yes")

        # Direct Google GenerativeAI fallback if GEMINI_API_KEY is provided
        self.gemini_direct_key = os.getenv("GEMINI_API_KEY")
        self._genai_model: Optional[Any] = None
        if self.gemini_direct_key and self.gemini_direct_key.startswith("AIzaSy"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_direct_key)
                self._genai_model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=SYSTEM_INSTRUCTION,
                )
                logger.info("Configured direct Google Gemini API client fallback.")
            except Exception as e:
                logger.warning("Failed to initialize direct Google Gemini: %s", e)

        self._client: Optional[OpenAI] = None
        self._init_openai_client()

    def _get_api_key(self) -> Optional[str]:
        """Dynamically resolve API key from instance or environment."""
        # Prioritize GEMINI_API_KEY first for Google AI Studio
        gemini_k = os.getenv("GEMINI_API_KEY")
        if gemini_k:
            gemini_k = str(gemini_k).strip().strip("\"'").strip()
            if not gemini_k.startswith("your_") and "change-me" not in gemini_k and gemini_k:
                return gemini_k

        key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if key:
            key = str(key).strip().strip("\"'").strip()
            if key.startswith("your_") or "change-me" in key or not key:
                return None
        return key

    def _is_google_key(self, key: Optional[str]) -> bool:
        """Determines if a given API key is a Google AI Studio key."""
        if not key:
            return False
        k = key.strip()
        if k.startswith("AIzaSy") or k.startswith("AQ.") or not k.startswith("sk-"):
            return True
        return False

    @property
    def is_google_direct(self) -> bool:
        """Determines if the active client is using Google AI Studio."""
        active_key = self._get_api_key()
        return self._is_google_key(active_key)

    def _init_openai_client(self):
        """Initializes or updates the OpenAI SDK client for OpenRouter or Google AI Studio."""
        active_key = self._get_api_key()
        if active_key:
            try:
                # Auto-detect Google AI Studio API Key (starts with AIzaSy or AQ. or GEMINI_API_KEY)
                if self.is_google_direct:
                    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
                    default_headers = None
                    logger.info("Auto-detected Google AI Studio key. Pointing to Google Gemini endpoint.")
                else:
                    base_url = OPENROUTER_BASE_URL
                    default_headers = {
                        "HTTP-Referer": "https://github.com/cloud-ai-chatbot",
                        "X-Title": "Cloud-Based AI Chatbot",
                    }

                self._client = OpenAI(
                    base_url=base_url,
                    api_key=active_key,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    max_retries=0,  # We handle retries defensively with custom backoff
                    default_headers=default_headers,
                )
            except Exception as e:
                logger.error("Failed to initialize OpenAI client: %s", e)

    def _get_gemini_direct_client(self) -> Optional[OpenAI]:
        """Creates an OpenAI client pointing to Google's official Gemini endpoint if GEMINI_API_KEY is available."""
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            candidate = self._get_api_key()
            if self._is_google_key(candidate):
                key = candidate
        if key and self._is_google_key(key):
            try:
                return OpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=key.strip(),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            except Exception as e:
                logger.warning("Could not create direct Google Gemini OpenAI client: %s", e)
        return None

    def _get_client(self) -> OpenAI:
        """Lazily initialize or return client with validation."""
        active_key = self._get_api_key()
        if not active_key and not self._genai_model and not self._get_gemini_direct_client():
            raise GeminiClientError(
                "GEMINI_API_KEY or OPENROUTER_API_KEY is not configured. Please add your API key in your .env file or Azure settings.",
                status_code=401,
            )

        expected_base = "https://generativelanguage.googleapis.com/v1beta/openai/" if self.is_google_direct else OPENROUTER_BASE_URL
        curr_base = str(getattr(self._client, "base_url", "")) if self._client else ""
        if active_key and (self._client is None or getattr(self._client, "api_key", None) != active_key or expected_base not in curr_base):
            self._init_openai_client()

        if self._client is None and not self._genai_model and not self._get_gemini_direct_client():
            raise GeminiClientError("Could not initialize AI client.", status_code=500)

        return self._client

    def is_current_query(self, message: str) -> bool:
        """Exposes live query detection method."""
        return is_live_query(message)

    def _prepare_messages(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        file_text_context: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Constructs chat completion messages list."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_INSTRUCTION}
        ]

        # Append rolling history
        if history:
            for turn in history:
                role = "user" if turn.get("role") == "user" else "assistant"
                text = turn.get("text", "").strip()
                if text:
                    messages.append({"role": role, "content": text})

        # Construct current user turn
        if image_bytes and image_mime:
            try:
                b64_img = base64.b64encode(image_bytes).decode("utf-8")
                image_data_url = f"data:{image_mime};base64,{b64_img}"
                content_parts: List[Dict[str, Any]] = []
                if file_text_context:
                    content_parts.append({
                        "type": "text",
                        "text": f"[ATTACHED DOCUMENT]\n{file_text_context}\n[END ATTACHED DOCUMENT]\n\n"
                    })
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": image_data_url, "detail": "auto"}
                })
                content_parts.append({"type": "text", "text": message})
                messages.append({"role": "user", "content": content_parts})
            except Exception as e:
                logger.error("Error encoding image to base64: %s", e)
                raise GeminiClientError("Failed to process attached image for AI analysis.", status_code=400)
        else:
            combined_text = ""
            if file_text_context:
                combined_text += f"[ATTACHED DOCUMENT]\n{file_text_context}\n[END ATTACHED DOCUMENT]\n\n"
            combined_text += message
            messages.append({"role": "user", "content": combined_text})

        return messages

    def _resolve_model(self, requested_model: Optional[str]) -> str:
        """Resolves model string adhering to configured defaults."""
        raw = requested_model or self.model or os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL
        raw = raw.strip()
        if getattr(self, "is_google_direct", False):
            # Google AI Studio expects model names without "google/" prefix
            if raw.startswith("google/"):
                raw = raw[7:]
            # Map preview/unsupported names to active Google AI Studio models
            if raw in ("gemini-3.1-flash-lite", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.0-flash"):
                raw = "gemini-2.5-flash"
            return raw
        if raw in ("google/gemini-2.0-flash-001", "gemini-2.0-flash-001"):
            return "google/gemini-2.5-flash"
        return raw

    def _determine_web_search(
        self,
        message: str,
        use_web_search_override: Optional[bool],
        file_text_context: Optional[str],
        image_bytes: Optional[bytes],
    ) -> bool:
        """
        Determines whether web search grounding should be enabled.
        """
        if self.is_google_direct:
            return False

        if use_web_search_override is not None:
            return bool(use_web_search_override)

        if file_text_context or image_bytes:
            return False

        if not self.enable_web_search:
            return False

        return is_live_query(message)

    def _call_openrouter(
        self,
        client: OpenAI,
        model_to_use: str,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        effort_level: str,
        enable_web_plugin: bool,
    ) -> Any:
        """Executes a single chat completion request with OpenRouter or Google AI Studio."""
        extra_body: Dict[str, Any] = {}

        if not getattr(self, "is_google_direct", False):
            if effort_level in ("low", "medium", "high"):
                extra_body["reasoning"] = {"effort": effort_level}

            if enable_web_plugin:
                extra_body["plugins"] = [{"id": "web"}]

        return client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens,
            extra_body=extra_body if extra_body else None,
        )

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
        Generates an AI response for the user request with real web search grounding,
        retry handling, output sanitization, and graceful multi-tier fallbacks.
        """
        client = self._get_client()
        model_to_use = self._resolve_model(model)
        messages = self._prepare_messages(
            message=message,
            history=history,
            file_text_context=file_text_context,
            image_bytes=image_bytes,
            image_mime=image_mime,
        )

        should_web_search = self._determine_web_search(
            message=message,
            use_web_search_override=use_web_search_override,
            file_text_context=file_text_context,
            image_bytes=image_bytes,
        )

        valid_efforts = ("low", "medium", "high")
        effort_level = effort.lower() if (effort and effort.lower() in valid_efforts) else "medium"

        if max_tokens_override:
            max_tokens = max_tokens_override
        else:
            base_tokens = {"low": 600, "medium": 1000, "high": 1500}.get(effort_level, 1000)
            max_tokens = base_tokens

        logger.info(
            "Generating reply via OpenRouter (model=%s, web_search=%s, effort=%s, max_tokens=%d)",
            model_to_use, should_web_search, effort_level, max_tokens,
        )

        # -----------------------------------------------------------------------
        # Step 1: Attempt web-grounded or standard request with retry backoff
        # -----------------------------------------------------------------------
        web_search_succeeded = False
        attempt_web_plugin = should_web_search

        last_error_str = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = cast(
                    Any,
                    self._call_openrouter(
                        client=client,
                        model_to_use=model_to_use,
                        messages=messages,
                        max_tokens=max_tokens,
                        effort_level=effort_level,
                        enable_web_plugin=attempt_web_plugin,
                    )
                )

                if response and response.choices:
                    choice_msg = response.choices[0].message
                    reply_text = getattr(choice_msg, "content", None)
                    if not reply_text and hasattr(choice_msg, "reasoning"):
                        reply_text = choice_msg.reasoning

                    clean_text = clean_ai_output(reply_text)
                    if clean_text:
                        if attempt_web_plugin:
                            web_search_succeeded = True

                        # Extract citations / sources if present
                        sources = extract_sources_from_response(response)
                        final_text = clean_text

                        if sources:
                            source_links = [f"- [{s['title']}]({s['url']})" for s in sources]
                            final_text += "\n\n### 🌐 Sources\n" + "\n".join(source_links)

                        return final_text
                    elif attempt_web_plugin:
                        # Raw tool call emitted without answer, fallback to non-plugin call
                        logger.info("Web plugin returned raw tool tokens without answer. Falling back to non-web request...")
                        attempt_web_plugin = False
                        continue

            except AuthenticationError as auth_err:
                provider_name = "Google AI Studio" if self.is_google_direct else "OpenRouter"
                var_name = "GEMINI_API_KEY" if self.is_google_direct else "OPENROUTER_API_KEY"
                logger.error("%s Authentication Error (401)", provider_name)
                raise GeminiClientError(
                    f"Invalid or expired {provider_name} API Key (401). Please verify {var_name} in your .env file or Cloud/Azure settings.",
                    status_code=401,
                ) from auth_err

            except RateLimitError as rl_err:
                last_error_str = f"RateLimitError: {rl_err}"
                if attempt < MAX_RETRIES:
                    wait_time = 1.0 * (2 ** attempt)
                    logger.warning("Rate limited (429). Backing off for %.1fs (attempt %d/%d)...", wait_time, attempt + 1, MAX_RETRIES)
                    time.sleep(wait_time)
                    continue
                logger.error("Rate Limit Exceeded (429)")
                raise GeminiClientError(
                    f"API rate limit or credit quota exceeded (429): {rl_err}",
                    status_code=429,
                ) from rl_err

            except (APITimeoutError, APIConnectionError) as net_err:
                last_error_str = f"NetworkError: {net_err}"
                if attempt < MAX_RETRIES:
                    wait_time = 1.0 * (2 ** attempt)
                    logger.warning("Connection/Timeout error (%s). Retrying in %.1fs...", net_err, wait_time)
                    time.sleep(wait_time)
                    continue
                logger.error("Network connection error: %s", net_err)
                if attempt_web_plugin:
                    logger.info("Web search request timed out. Falling back to non-web model request...")
                    attempt_web_plugin = False
                    continue
                raise GeminiClientError(
                    f"Connection to AI provider timed out or failed ({net_err}).",
                    status_code=504 if isinstance(net_err, APITimeoutError) else 503,
                ) from net_err

            except (NotFoundError, APIStatusError) as status_err:
                last_error_str = f"APIStatusError({getattr(status_err, 'status_code', 500)}): {status_err}"
                status_code = getattr(status_err, "status_code", 500)
                err_str = str(status_err).lower()
                logger.warning("AI Provider API error (%d): %s", status_code, status_err)

                # If web search failed due to budget or plugin, fall back to standard model call immediately
                if attempt_web_plugin and (status_code in (400, 402, 404, 500, 502, 503) or "plugin" in err_str or "web" in err_str or "afford" in err_str):
                    logger.info("Web search plugin call failed (%s). Retrying standard model request...", status_err)
                    attempt_web_plugin = False
                    continue

                # 402 Budget limit handling
                if status_code == 402 or "credit" in err_str or "afford" in err_str:
                    return self._handle_budget_fallback(client, messages, max_tokens, file_text_context, should_web_search)

                # Transient 500/502/503 errors -> retry with backoff
                if status_code in (500, 502, 503, 504) and attempt < MAX_RETRIES:
                    wait_time = 1.0 * (2 ** attempt)
                    logger.warning("Server status error (%d). Retrying in %.1fs...", status_code, wait_time)
                    time.sleep(wait_time)
                    continue

                break

            except Exception as e:
                last_error_str = f"{type(e).__name__}: {str(e)}"
                logger.exception("Unexpected error during AI generation attempt %d: %s", attempt, e)
                if attempt_web_plugin:
                    attempt_web_plugin = False
                    continue
                if attempt < MAX_RETRIES:
                    time.sleep(1.0)
                    continue
                break

        # -----------------------------------------------------------------------
        # Step 2: Resilient Fallback Models
        # -----------------------------------------------------------------------
        if self.is_google_direct:
            fallback_models = [
                "gemini-2.5-flash",
            ]
        else:
            fallback_models = [
                "google/gemini-2.5-flash",
                "google/gemini-3.7-flash",
                "google/gemini-3.6-flash",
                "google/gemini-3.1-flash-lite",
                "inclusionai/ling-3.0-flash-vl:free",
                "dots-studio/dots-3-note-preview:free",
                "nex-agi/nex-n2.5-mini:free",
                "nex-agi/nex-n2.5-pro:free",
            ]

        for fb_model in fallback_models:
            if fb_model == model_to_use:
                continue
            try:
                logger.info("Attempting fallback model: %s", fb_model)
                fb_resp = cast(
                    Any,
                    client.chat.completions.create(
                        model=fb_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=min(max_tokens, 700),
                    )
                )
                if fb_resp and fb_resp.choices:
                    content = (
                        getattr(fb_resp.choices[0].message, "content", None)
                        or getattr(fb_resp.choices[0].message, "reasoning", None)
                    )
                    clean_content = clean_ai_output(content)
                    if clean_content:
                        result = clean_content
                        if should_web_search and not web_search_succeeded:
                            result += "\n\n> ℹ️ *Note: Live web search grounding was temporarily unavailable from the provider. This answer is based on internal model knowledge.*"
                        return result
            except Exception as fb_err:
                logger.warning("Fallback model %s failed: %s", fb_model, fb_err)

        raise GeminiClientError(
            f"The AI service could not complete the request with model '{model_to_use}' ({last_error_str or 'Please verify your API key and network connection'}).",
            status_code=502,
        )

    def _handle_budget_fallback(
        self,
        client: OpenAI,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        file_text_context: Optional[str],
        should_web_search: bool = False,
    ) -> str:
        """
        Handles low credit state by routing through direct Gemini API, clean free tier models,
        or returning clear user guidance without crashing.
        """
        # 1. Try direct Google Gemini API if configured
        direct_client = self._get_gemini_direct_client()
        if direct_client:
            try:
                logger.info("Attempting direct Google Gemini API for budget fallback...")
                for g_mod in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"):
                    try:
                        g_resp = cast(
                            Any,
                            direct_client.chat.completions.create(
                                model=g_mod,
                                messages=messages,
                                temperature=0.7,
                                max_tokens=max_tokens,
                            )
                        )
                        if g_resp and g_resp.choices:
                            content = getattr(g_resp.choices[0].message, "content", None)
                            ans = clean_ai_output(content)
                            if ans:
                                return ans
                    except Exception as mod_err:
                        logger.debug("Direct Gemini model %s attempt: %s", g_mod, mod_err)
            except Exception as g_err:
                logger.warning("Direct Google Gemini OpenAI fallback failed: %s", g_err)

        if self._genai_model:
            try:
                logger.info("Attempting direct Google GenerativeAI fallback...")
                prompt_text = "\n".join(
                    m.get("content", "") if isinstance(m.get("content"), str) else str(m.get("content"))
                    for m in messages if m.get("role") != "system"
                )
                res = self._genai_model.generate_content(prompt_text)
                if res and res.text:
                    ans = clean_ai_output(res.text)
                    if ans:
                        return ans
            except Exception as g_err:
                logger.warning("Direct Gemini fallback failed: %s", g_err)

        # 2. Try proven clean conversational free fallback models
        logger.info("Attempting clean conversational free fallback models...")
        clean_free_models = [
            "inclusionai/ling-3.0-flash-vl:free",
            "dots-studio/dots-3-note-preview:free",
            "nex-agi/nex-n2.5-mini:free",
            "nex-agi/nex-n2.5-pro:free",
            "nvidia/nemotron-3.5-lightning:free",
        ]
        for fm in clean_free_models:
            for attempt in range(2):
                try:
                    fb_resp = cast(
                        Any,
                        client.chat.completions.create(
                            model=fm,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=min(max_tokens, 600),
                        )
                    )
                    if fb_resp and fb_resp.choices:
                        raw_txt = (
                            getattr(fb_resp.choices[0].message, "content", None)
                            or getattr(fb_resp.choices[0].message, "reasoning", None)
                        )
                        clean_txt = clean_ai_output(raw_txt)
                        if clean_txt:
                            if should_web_search:
                                clean_txt += "\n\n> ℹ️ *Note: Live web search grounding was temporarily unavailable from the provider. This answer is based on internal model knowledge.*"
                            return clean_txt
                except Exception as e:
                    err_s = str(e).lower()
                    if "429" in err_s and attempt == 0:
                        time.sleep(0.6)
                        continue
                    logger.warning("Free model fallback %s failed: %s", fm, e)
                    break

        # 3. If file context was present, provide structured document report
        if file_text_context:
            user_msg = messages[-1].get("content", "") if messages else ""
            if isinstance(user_msg, list):
                user_msg = "Summarize document"
            return generate_document_analysis_report("Uploaded Document", file_text_context, str(user_msg))

        # 4. Return user-friendly guidance notice
        return (
            "⚠️ **OpenRouter Credit Balance Notice**\n\n"
            "Your OpenRouter API account currently has zero remaining token credits (Status 402).\n\n"
            "**How to continue chatting:**\n"
            "1. **Option 1 (Free Gemini Key)**: Get a 100% free Gemini API key with 1,500 requests/day at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and add `GEMINI_API_KEY=AIzaSy...` in your `.env` file.\n"
            "2. **Option 2 (Top Up Credits)**: Add credits to your OpenRouter account at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits).\n"
            "3. **Option 3**: Wait a brief moment and retry as public free models become available."
        )

    def generate_reply_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        file_text_context: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
        model: Optional[str] = None,
        effort: Optional[str] = "medium",
        use_web_search_override: Optional[bool] = None,
    ) -> Generator[str, None, None]:
        """
        Streams AI response chunks in real-time, filtering raw tool tokens.
        """
        client = self._get_client()
        model_to_use = self._resolve_model(model)
        messages = self._prepare_messages(
            message=message,
            history=history,
            file_text_context=file_text_context,
            image_bytes=image_bytes,
            image_mime=image_mime,
        )

        should_web_search = self._determine_web_search(
            message=message,
            use_web_search_override=use_web_search_override,
            file_text_context=file_text_context,
            image_bytes=image_bytes,
        )

        valid_efforts = ("low", "medium", "high")
        effort_level = effort.lower() if (effort and effort.lower() in valid_efforts) else "medium"
        base_tokens = {"low": 600, "medium": 1000, "high": 1500}.get(effort_level, 1000)

        extra_body: Dict[str, Any] = {}
        if not getattr(self, "is_google_direct", False):
            if effort_level in ("low", "medium", "high"):
                extra_body["reasoning"] = {"effort": effort_level}
            if should_web_search:
                extra_body["plugins"] = [{"id": "web"}]

        logger.info(
            "Streaming via %s (model=%s, web_search=%s, effort=%s)",
            "Google AI Studio" if getattr(self, "is_google_direct", False) else "OpenRouter",
            model_to_use,
            should_web_search,
            effort_level,
        )

        has_yielded = False
        raw_accumulated = ""
        try:
            stream_response = cast(
                Any,
                client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=base_tokens,
                    extra_body=extra_body if extra_body else None,
                    stream=True,
                )
            )

            for chunk in stream_response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None) or ""
                    if not content and hasattr(delta, "reasoning"):
                        content = getattr(delta, "reasoning", "") or ""
                    if content:
                        raw_accumulated += content
                        # If raw tool call token is being emitted, don't yield it
                        if "<|tool_call_" not in content and "[google(" not in content:
                            has_yielded = True
                            yield content

        except Exception as stream_err:
            logger.warning("Streaming call failed: %s. Falling back to generate_reply...", stream_err)

        # If stream yielded raw tool tokens or failed, fallback to clean generate_reply
        if not has_yielded or "<|tool_call_" in raw_accumulated:
            reply = self.generate_reply(
                message=message,
                history=history,
                file_text_context=file_text_context,
                image_bytes=image_bytes,
                image_mime=image_mime,
                model=model,
                effort=effort,
                use_web_search_override=use_web_search_override,
            )
            yield reply