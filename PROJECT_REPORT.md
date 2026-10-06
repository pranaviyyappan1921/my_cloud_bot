# 📋 Comprehensive Project Handoff & Technical Specification Report

> **Project Title:** Cloud-Based AI Chatbot with Multimodal File Analysis, Mathematical Reasoning Engine, Scheduled Tasks, and AI Plugin Marketplace  
> **Course / Context:** High Performance Cloud Computing (HPCC) — College Mini-Project  
> **Target Audience:** AI Large Language Models (LLMs), Software Engineers, Cloud Architects, and Technical Evaluators  
> **Repository Root:** `c:/cloud-ai-chatbot`

---

## 📑 Table of Contents
1. [Executive Summary & Project Identity](#1-executive-summary--project-identity)
2. [Technology Stack & Dependency Breakdown](#2-technology-stack--dependency-breakdown)
3. [System Architecture & Data Flow Diagrams](#3-system-architecture--data-flow-diagrams)
4. [Complete File & Directory Map](#4-complete-file--directory-map)
5. [Backend Architecture & Core Services](#5-backend-architecture--core-services)
   - [5.1 Main Flask Server & REST API Catalog](#51-main-flask-server--rest-api-catalog)
   - [5.2 AI Gateway & LLM Orchestration (`gemini_client.py`)](#52-ai-gateway--llm-orchestration)
   - [5.3 Document & Multimodal Ingestion Engine (`file_processor.py`)](#53-document--multimodal-ingestion-engine)
   - [5.4 Advanced Mathematical Analysis Engine (`math_analyzer.py`)](#54-advanced-mathematical-analysis-engine)
   - [5.5 Autonomous Task Scheduler (`scheduler.py`)](#55-autonomous-task-scheduler)
   - [5.6 Multilingual Translation Engine (`translator.py`)](#56-multilingual-translation-engine)
   - [5.7 Multimodal Generation Engines (Image & Video)](#57-multimodal-generation-engines)
   - [5.8 Microsoft Azure Cloud Persistence Layer](#58-microsoft-azure-cloud-persistence-layer)
6. [AI Plugin Marketplace & Sandboxed Tool Execution](#6-ai-plugin-marketplace--sandboxed-tool-execution)
7. [Frontend Architecture & UI/UX Design System](#7-frontend-architecture--uiux-design-system)
8. [Configuration & Environment Variables](#8-configuration--environment-variables)
9. [Deployment & Cloud DevOps Runbook](#9-deployment--cloud-devops-runbook)
10. [Automated Verification & Test Suite](#10-automated-verification--test-suite)

---

## 1. Executive Summary & Project Identity

The **Cloud-Based AI Chatbot** is a production-grade, cloud-native conversational AI application built with **Python (Flask)**, **Modern Vanilla JavaScript**, and **Microsoft Azure Cloud Services**.

### Core Value Proposition
- **Hybrid AI Engine**: Routes requests to Google's state-of-the-art **Gemini 2.5 / 3.7 Flash** models via OpenRouter or direct Google AI Studio API with Server-Sent Events (SSE) streaming.
- **Multimodal Document Intelligence**: Extracts and analyzes text and tables from **PDF, DOCX, TXT**, and inspects diagrams/photos via **Multimodal Base64 Vision**.
- **Real-Time Web Search Grounding**: Automatically detects time-sensitive queries and injects live search context with URL citations.
- **Cross-Domain Mathematical Reasoning**: Recognizes formulas, solves step-by-step equations, formats with **KaTeX LaTeX**, and highlights applications across High Performance Computing (HPC), AI/ML, Data Science, Control Systems, and Physics.
- **Background Task Scheduling**: Features natural language scheduling (e.g., *"Remind me every Monday at 9 AM to review AI news"*), local polling daemon, and Azure Function webhook integration.
- **Multilingual Translation Suite**: Translates text and uploaded documents across 20+ languages with tone adaptation (Natural, Formal, Casual, Literal) and Web Speech API synthesis.
- **Extensible AI Plugin Marketplace**: Sandboxed execution runtime with granular permission controls for Calculator, Web Search, Document Analyzer, Azure Blob Storage, GitHub, and enterprise SaaS connectors.

---

## 2. Technology Stack & Dependency Breakdown

### 2.1 Core Frameworks & Runtimes
| Layer | Technologies Used | Description / Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+ / Flask 3.0.3 | WSGI web application server, REST APIs, SSE endpoints |
| **WSGI Production Runner** | Gunicorn 22.0.0 | High-concurrency WSGI HTTP server for Azure App Service Linux |
| **Frontend Core** | HTML5, CSS3 (Vanilla), ES6+ JS | Single Page Application (SPA), Dark-Themed Glassmorphism UI |
| **Markdown & Formatting** | Marked.js, Highlight.js | Real-time Markdown rendering with syntax-highlighted code blocks |
| **Mathematical Typesetting** | KaTeX 0.16.9 | Client-side LaTeX formula rendering ($...$ and $$...$$) |
| **Speech Services** | Web Speech API | Client-side Speech-to-Text (STT) and Text-to-Speech (TTS) |

### 2.2 Python Dependencies (`requirements.txt`)
```text
Flask==3.0.3               # Web framework & routing engine
openai>=1.30.0             # Official OpenAI SDK (configured for OpenRouter OpenAI-compatible endpoint)
pypdf==4.3.1               # PDF page parsing and textual extraction
python-docx==1.1.2         # Word document paragraph and table extraction
python-dotenv==1.0.1       # Local .env secret and environment configuration loader
gunicorn==22.0.0           # Production WSGI server for Azure deployment
requests==2.34.2           # Synchronous HTTP client for APIs and fallback services
certifi>=2024.2.2          # SSL Certificate verification bundle
sqlalchemy                 # SQL ORM & query builder for database persistence
pyodbc                     # ODBC driver for Microsoft Azure SQL Database connectivity
azure-storage-blob         # Azure Blob Storage SDK for cloud object storage
```

---

## 3. System Architecture & Data Flow Diagrams

### 3.1 High-Level Cloud Architecture Diagram

```
                                  +-------------------------------------------------------------------------+
                                  |                         Client Browser (SPA UI)                         |
                                  |  - Dark Glassmorphic Theme        - SSE Live Streaming Message Renderer |
                                  |  - Marked.js + KaTeX Rendering    - Multi-Tab Views (Chat, Tasks, Trans)|
                                  |  - Audio Speech-to-Text & TTS     - Pre-Send Drag & Drop Attachment Chip|
                                  +------------------------------------+------------------------------------+
                                                                       | HTTP REST / SSE (multipart/form-data)
                                                                       v
+-----------------------------------------------------------------------------------------------------------------------------------+
|                                                 Flask Application Server (app.py)                                                 |
|                                                                                                                                   |
|   +--------------------------+    +--------------------------+    +--------------------------+    +---------------------------+   |
|   |   Session / Auth Mgmt    |    |   Document & Vision      |    |   AI Plugin Sandbox      |    |    Autonomous Scheduler   |   |
|   | - Rolling 20-turn buffer |    |   - pypdf (PDFs)         |    |   - Calculator Engine    |    | - Background Daemon (30s) |   |
|   | - Session ID isolation   |    |   - python-docx (DOCX)   |    |   - Web Search Plugin    |    | - NL Schedule Parser      |   |
|   | - Local / Azure logging  |    |   - Multi-encoding TXT   |    |   - Azure Blob / GitHub  |    | - Azure Function Webhook  |   |
|   +--------------------------+    +--------------------------+    +--------------------------+    +---------------------------+   |
+---------------------------------------------------+-------------------------------------------------------------------------------+
                                                    |
                         +--------------------------+--------------------------+
                         |                                                     |
                         v                                                     v
+--------------------------------------------------+        +--------------------------------------------------+
|          AI Gateway (gemini_client.py)           |        |          Azure Cloud Services Subsystem          |
|                                                  |        |                                                  |
|  - OpenRouter Gateway (google/gemini-3.7-flash)  |        |  - Azure App Service (Linux Web Hosting)         |
|  - Direct Google AI Studio Fallback              |        |  - Azure Blob Storage (Document Backups)         |
|  - Real-time Web Search Grounding Plugin         |        |  - Azure SQL Database (Conversations & Logs)     |
|  - Mathematical Reasoning Prompt Scaffolding     |        |  - Azure Application Insights & Key Vault        |
+--------------------------------------------------+        +--------------------------------------------------+
```

---

## 4. Complete File & Directory Map

```
c:/cloud-ai-chatbot/
├── .env                              # Active runtime environment secrets (Local only, Git-ignored)
├── .env.example                      # Production template of required environment keys
├── .gitignore                        # Git exclusion rules (venv, uploads, .env, pycache)
├── README.md                         # Project documentation and deployment guide
├── requirements.txt                  # Python dependencies manifest
├── pyrightconfig.json                # Python language server and type checking config
├── app.py                            # Primary Flask server, REST routing, and middleware
├── test_verification.py              # Automated test suite (9 core verification test cases)
├── test_math_analysis.py             # Math analyzer unit and integration test suite
├── test_plugin_marketplace.py        # Plugin ecosystem and sandbox test suite
├── check_tables.py                   # Diagnostic script to inspect Azure SQL database tables
│
├── data/                             # Persistent JSON state storage
│   ├── plugin_state.json             # Enabled/connected state and permissions for plugins
│   ├── plugin_logs.json              # Historical tool invocation telemetry logs
│   ├── scheduled_tasks.json          # Task definitions, recurrence configs, and execution logs
│   └── translation_history.json      # Recent translation cache
│
├── plugins/                          # AI Plugin Architecture & Sandbox Engine
│   ├── __init__.py                   # Package exports
│   ├── base_plugin.py                # Abstract BasePlugin class, ToolPermission, ToolDefinition
│   ├── plugin_manager.py             # Registry, execution sandbox, audit logs, auto-trigger
│   ├── calculator_plugin.py          # Math engine, arithmetic, trigonometry, calculus, stats
│   ├── web_search_plugin.py          # Live web search query executor
│   ├── file_analysis_plugin.py       # Document summarizer, key takeaways, metadata extractor
│   ├── azure_blob_plugin.py          # Cloud storage explorer (list, upload, download, delete)
│   ├── github_plugin.py              # GitHub API repository search, issues, commits, README
│   └── integrations_catalog.py       # Enterprise connectors (Gmail, Slack, Drive, Notion, SQL)
│
├── static/                           # Client static assets
│   ├── css/
│   │   └── style.css                 # Complete stylesheet: dark theme, KaTeX styling, modals, animations
│   ├── js/
│   │   └── script.js                 # Complete client controller: state, SSE, audio, UI switching
│   └── generated/                    # Storage for locally generated media artifacts
│
├── templates/                        # Jinja2 HTML templates
│   └── index.html                    # Single-Page Application (SPA) layout with all 4 views & modals
│
├── uploads/                          # Temporary local directory for uploaded files
│   └── .gitkeep                      # Git directory placeholder
│
└── utils/                            # Core service helper modules
    ├── __init__.py                   # Package exports
    ├── azure_blob.py                 # Azure Blob Storage container and upload helpers
    ├── database.py                   # SQLAlchemy connection pooling for Azure SQL
    ├── init_db.py                    # Database schema table creation scripts
    ├── file_processor.py             # Secure file validator, parsers (PDF/DOCX/TXT/Vision), and fallback
    ├── gemini_client.py              # Dual OpenRouter/Gemini client, SSE generator, live web search
    ├── math_analyzer.py              # Mathematical regex detector, concept registry, LaTeX scaffolding
    ├── scheduler.py                  # TaskManager, BackgroundScheduler thread, NL schedule parser
    ├── translator.py                 # Multilingual translation service, tones, document translation
    ├── image_generator.py            # AI image generation engine with fallback
    └── video_generator.py            # Asynchronous AI video generation job state machine
```

---

## 5. Backend Architecture & Core Services

### 5.1 Main Flask Server & REST API Catalog (`app.py`)

`app.py` serves as the primary gateway, orchestrating all RESTful endpoints, SSE streaming, file handling, session states, and integration bridges.

#### Complete REST API Specification Table
| Method | Endpoint | Description | Request Payload | Response Schema / Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves the SPA frontend | None | `text/html` (200) |
| `GET` | `/api/health` | Service health & telemetry probe | None | `{"status": "ok", "model": "...", "azure_blob_connected": bool, ...}` (200) |
| `POST` | `/api/chat` | Synchronous chat turn | `multipart/form-data` (`message`, `file`, `model`, `effort`, `web_search`) | `{"reply": str, "file_name": str, "plugin_used": dict, ...}` (200) |
| `POST` | `/api/chat/stream` | **SSE Streaming** chat turn | `multipart/form-data` (same as `/api/chat`) | `text/event-stream` chunks (`data: {"type": "chunk", "text": "..."}`) |
| `POST` | `/api/clear` | Clears user session history | None | `{"status": "cleared"}` (200) |
| `POST` | `/api/generate-image` | Synthesizes an AI image | `{"prompt": str}` | `{"success": true, "image_url": str, "prompt": str}` (200) |
| `POST` | `/api/generate-video` | Starts async video job | `{"prompt": str}` | `{"success": true, "job_id": str, "status": "processing"}` (200) |
| `GET` | `/api/video/status/<id>`| Polls video job status | URL Param `<id>` | `{"job_id": str, "status": "completed", "video_url": str}` (200) |
| `GET` | `/scheduled` | Direct route to Scheduled View | None | `text/html` (200) |
| `GET` | `/api/tasks` | Lists scheduled tasks | Query: `?status=active` | `{"tasks": [...], "total": int}` (200) |
| `POST` | `/api/tasks` | Creates a scheduled task | JSON: `{"title", "prompt", "recurrence", "time", "days"}` | `{"status": "success", "task": {...}}` (201) |
| `GET` | `/api/tasks/<id>` | Retrieves task & execution log | URL Param `<id>` | `{task_details}` (200) |
| `PUT` | `/api/tasks/<id>` | Updates an existing task | JSON: updated fields | `{"status": "success", "task": {...}}` (200) |
| `DELETE`| `/api/tasks/<id>`| Deletes a scheduled task | URL Param `<id>` | `{"status": "deleted", "id": str}` (200) |
| `POST` | `/api/tasks/<id>/pause` | Pauses task execution | URL Param `<id>` | `{"status": "success", "task": {...}}` (200) |
| `POST` | `/api/tasks/<id>/resume`| Resumes task execution | URL Param `<id>` | `{"status": "success", "task": {...}}` (200) |
| `POST` | `/api/tasks/<id>/run` | Triggers immediate execution | URL Param `<id>` | `{"status": "completed", "result": str, "duration_seconds": float}` (200) |
| `POST` | `/api/tasks/parse-nl` | Parses NL schedule text | JSON: `{"text": "Every Fri at 5 PM..."}` | `{"status": "success", "parsed": {...}}` (200) |
| `POST` | `/api/tasks/tick` | Webhook for Azure Functions | None | `{"status": "ok", "executed_count": int, "results": [...]}` (200) |
| `GET` | `/translation` | Direct route to Translation View| None | `text/html` (200) |
| `GET` | `/api/languages` | Returns supported languages | None | `{"success": true, "languages": [...], "total": 21}` (200) |
| `POST` | `/api/translate` | Translates text string | JSON: `{"text", "target_language", "source_language", "mode"}` | `{"success": true, "translated_text": str, "detected_source": str}` (200) |
| `POST` | `/api/translate/file`| Translates uploaded document | `multipart/form-data` (`file`, `target_language`, `mode`) | `{"success": true, "translated_text": str, "filename": str}` (200) |
| `GET` | `/plugins` | Direct route to Plugins View | None | `text/html` (200) |
| `GET` | `/api/plugins` | Lists marketplace plugins | Query: `?category=...&q=...&connected=true` | `{"success": true, "plugins": [...], "stats": {...}}` (200) |
| `GET` | `/api/plugins/<id>` | Gets plugin details & tools | URL Param `<id>` | `{"success": true, "plugin": {...}}` (200) |
| `POST` | `/api/plugins/<id>/connect` | Connects a plugin | JSON: `{"config": {...}}` | `{"success": true, "message": str, "plugin": {...}}` (200) |
| `POST` | `/api/plugins/<id>/disconnect` | Disconnects a plugin | URL Param `<id>` | `{"success": true, "message": str}` (200) |
| `POST` | `/api/plugins/<id>/enable` | Enables plugin tool use | URL Param `<id>` | `{"success": true, "plugin": {...}}` (200) |
| `POST` | `/api/plugins/<id>/disable`| Disables plugin tool use | URL Param `<id>` | `{"success": true, "plugin": {...}}` (200) |
| `PUT` | `/api/plugins/<id>/permissions` | Updates permissions | JSON: `{"permissions": {"perm_id": bool}}` | `{"success": true, "plugin": {...}}` (200) |
| `POST` | `/api/plugins/<id>/execute` | Sandboxed direct execution | JSON: `{"tool_name": str, "params": dict}` | `{"success": bool, "data": Any, "duration_ms": float}` (200/400) |
| `GET` | `/api/plugins/logs` | Fetches audit telemetry | Query: `?plugin_id=...&status=...&limit=100` | `{"success": true, "logs": [...]}` (200) |
| `DELETE`| `/api/plugins/logs` | Clears audit logs | Query: `?plugin_id=...` | `{"success": true, "cleared_count": int}` (200) |
| `GET` | `/api/plugins/stats` | Analytics summary | None | `{"success": true, "stats": {...}}` (200) |

---

### 5.2 AI Gateway & LLM Orchestration (`utils/gemini_client.py`)

The `GeminiClient` class provides a high-reliability gateway connecting to LLM providers:
1. **Dual Routing Engine**:
   - Primary: Uses OpenAI Python SDK client targeting OpenRouter (`https://openrouter.ai/api/v1`) with model `google/gemini-3.7-flash` (or user-selected `gemini-3.6-flash`, `gemini-3.1-flash-lite`, `gemini-2.5-flash`).
   - Alternative: Native Google AI Studio API (`GEMINI_API_KEY`) with generous free-tier capacity.
2. **Real-time Web Search Grounding**:
   - Detects live query intents via compiled regular expressions matching words like *latest*, *today*, *scores*, *stock price*, *news*, *weather*.
   - Injects OpenRouter web plugin payload: `extra_body={"plugins": [{"id": "web"}]}`.
   - Extracts and renders cited sources with markdown hyperlinks.
3. **Multimodal Payload Encoding**:
   - Formats visual attachments as Base64 Data URLs: `data:{image_mime};base64,{base64_str}` inside OpenAI-compatible `image_url` content blocks.
4. **Token & Marker Sanitization**:
   - Strips raw internal model artifacts like `<|tool_call_start|>`, `<|thought|>...<|thought_end|>`, and `[google(query=...)]` before streaming to clients.
5. **Streaming Generator (`generate_reply_stream`)**:
   - Yields delta text tokens using Python generators, handling connection drops with exponential backoff retries.

---

### 5.3 Document & Multimodal Ingestion Engine (`utils/file_processor.py`)

Handles secure validation, virus/path sanitization, text extraction, and offline fallback generation.

1. **Security & Size Enforcement**:
   - Enforces **10 MB max file size** (`app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024`).
   - Restricts extensions to `.pdf`, `.txt`, `.docx`, `.png`, `.jpg`, `.jpeg`, `.webp`.
   - Prevents path traversal via `werkzeug.utils.secure_filename`.
2. **Text Extraction Pipelines**:
   - **PDF Parsing**: Iterates pages with `pypdf.PdfReader`, concatenating non-empty text buffers. Throws clear error if PDF is empty or purely scanned.
   - **DOCX Parsing**: Utilizes `docx.Document` to extract both paragraph text and tabular content formatted cleanly as `Col1 | Col2 | Col3`.
   - **Plain Text Parsing**: Robust multi-encoding reader trying UTF-8, Latin-1, CP1252, and UTF-16.
3. **Deterministic Fallback Generator (`generate_document_analysis_report`)**:
   - If AI quota/credits are exhausted (HTTP 402/429), the engine automatically computes word counts, paragraph statistics, character distributions, and generates a structured executive summary fallback.

---

### 5.4 Advanced Mathematical Analysis Engine (`utils/math_analyzer.py`)

A dedicated mathematical detection and scaffolding engine that transforms mathematical inquiries into comprehensive scientific breakdowns.

1. **Detection Engine**:
   - Uses regex filters to detect formulas, LaTeX delimiters (`$...$`, `$$...$$`), calculus operators ($\int, \frac{d}{dx}, \nabla, \partial$), matrix expressions, statistical functions, and speedup formulas.
2. **Concept Registry**:
   - Maps inputs to 6 foundational computational domains:
     - **Parallel Speedup & Scalability**: $S = \frac{T_s}{T_p}$, Amdahl’s Law, Gustafson’s Law, Parallel Efficiency $E = \frac{S}{N}$.
     - **Linear Equations & Regression**: $y = mx + c$, Ordinary Least Squares $\mathbf{w} = (\mathbf{X}^T\mathbf{X})^{-1}\mathbf{X}^T\mathbf{y}$.
     - **Quadratic Discriminant & Stability**: $D = b^2 - 4ac$, Root classification, Ray-tracing intersection, 2nd-order system damping.
     - **Linear Algebra & Matrix Transformations**: $\mathbf{Y} = \mathbf{W}\mathbf{X} + \mathbf{B}$, SVD, Eigenvalues, 3D affine rotations.
     - **Differential Calculus & Optimization**: $\nabla f(\mathbf{x})$, Gradient descent update $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \nabla L(\mathbf{w}_t)$, Backpropagation chain rule.
     - **Bayesian Inference & Probability**: $P(A|B) = \frac{P(B|A)P(A)}{P(B)}$, Kalman filters, SLAM, ML classification.
3. **Scaffolding Format**:
   - Enforces 7-section structured outputs: **Concept Identification**, **Variable & Symbol Breakdown**, **Mathematical Formulation**, **Step-by-Step Derivation / Solution**, **Result Verification**, **Real-World Cross-Domain Applications**, and **Visualization / Code Example**.

---

### 5.5 Autonomous Task Scheduler (`utils/scheduler.py`)

Enables automated scheduling, cron recurrence evaluation, and background AI execution.

1. **Storage & Isolation**:
   - Persists tasks to `data/scheduled_tasks.json`, indexed by `session_id` to guarantee user isolation.
2. **Recurrence Types**:
   - `once` (one-time date/time), `daily` (every day at HH:MM), `weekly` (selected weekdays), `weekdays` (Mon-Fri), and `custom`.
3. **Execution Modes**:
   - **Local Background Thread**: `BackgroundScheduler` daemon polling every 30 seconds.
   - **Azure Cloud Webhook**: `POST /api/tasks/tick` triggered by external Azure Functions Timer Trigger or Azure WebJobs.
4. **Natural Language Parser (`parse_natural_language_schedule`)**:
   - Uses Gemini Flash (with regex fallback) to convert user phrases like *"Every Friday at 5 PM generate my summary"* into structured JSON: `{"title": "Weekly Summary", "recurrence": "weekly", "days": ["Friday"], "time": "17:00"}`.

---

### 5.6 Multilingual Translation Engine (`utils/translator.py`)

A dedicated translation service supporting 21 major global and Indian regional languages:
- **Languages**: English, Spanish, French, German, Mandarin Chinese, Japanese, Korean, Arabic, Russian, Portuguese, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Urdu, Italian.
- **Translation Tones**:
  - `Natural`: Idiomatic and smooth.
  - `Formal`: Professional language for business and academic papers.
  - `Casual`: Conversational language for chats.
  - `Literal`: Direct grammatical structure translation.
- **Document Translation**: Directly accepts PDF, DOCX, or TXT files, extracts content, translates it, and presents preview side-by-side with original text.

---

### 5.7 Multimodal Generation Engines

1. **AI Image Generation (`utils/image_generator.py`)**:
   - Generates high-resolution images via Pollinations / DALL-E / Flux API endpoints.
   - Saves generated assets into `static/generated/` and provides instant client preview and download.
2. **AI Video Generation (`utils/video_generator.py`)**:
   - Implements an asynchronous job queue state machine (`queued` -> `processing` -> `completed` / `failed`).
   - Returns a `job_id` immediately; client polls `GET /api/video/status/<job_id>` until video rendering completes.

---

### 5.8 Microsoft Azure Cloud Persistence Layer

1. **Azure Blob Storage (`utils/azure_blob.py`)**:
   - Uploads files securely to Azure Blob container `chatbot-uploads` using `azure-storage-blob`.
   - Generates SAS URLs for secure, expiring document downloads.
2. **Azure SQL Database (`utils/database.py`, `utils/init_db.py`)**:
   - SQLAlchemy engine with ODBC Driver 18 for SQL Server.
   - Relational Tables:
     - `conversations` (`id`, `session_id`, `title`, `created_at`, `updated_at`)
     - `messages` (`id`, `conversation_id`, `role`, `content`, `created_at`)
     - `uploaded_files` (`id`, `session_id`, `file_name`, `blob_name`, `file_type`, `uploaded_at`)

---

## 6. AI Plugin Marketplace & Sandboxed Tool Execution

The application contains a dynamic **Plugin Ecosystem** located in `plugins/`.

```
                    +---------------------------------------+
                    |      PluginManager (Coordinator)      |
                    +-------------------+-------------------+
                                        |
      +---------------------------------+---------------------------------+
      |                                 |                                 |
      v                                 v                                 v
+------------------+          +-------------------+             +-------------------+
| Active Plugins   |          | Future Connectors |             | Security & Logs   |
| - Calculator     |          | - Gmail / Outlook |             | - Permission Check|
| - Web Search     |          | - Slack / Notion  |             | - Argument Valid. |
| - File Analyzer  |          | - Google Drive    |             | - Telemetry Logs  |
| - Azure Blob     |          | - SQL Databases   |             | - State Save/Load |
| - GitHub Client  |          +-------------------+             +-------------------+
+------------------+
```

### 6.1 Plugin Architecture Core Classes (`plugins/base_plugin.py`)
- **`ToolPermission`**: Defines granular permission nodes (e.g., `read_files`, `calculate`, `execute_search`, `write_blob`, `read_repos`). Users can toggle individual permissions on/off.
- **`ToolDefinition`**: Standardized JSON Schema defining tool name, description, parameters, required fields, and required permission keys.
- **`BasePlugin`**: Abstract interface mandating `register_tools()`, `register_permissions()`, `execute_tool()`, `can_handle_message()`, and `to_dict()`.

### 6.2 Registered Plugins & Exposed Tools
1. **`CalculatorPlugin` (`calculator`)**:
   - Tools: `calculate(expression)`, `solve_equation(equation, variable)`, `statistics(numbers)`, `unit_converter(value, from_unit, to_unit)`.
2. **`WebSearchPlugin` (`web_search`)**:
   - Tools: `search_web(query, max_results)`.
3. **`FileAnalysisPlugin` (`file_analysis`)**:
   - Tools: `summarize_document(text)`, `extract_key_points(text)`, `analyze_structure(text)`.
4. **`AzureBlobPlugin` (`azure_blob`)**:
   - Tools: `list_blobs(prefix)`, `get_blob_info(blob_name)`, `delete_blob(blob_name)`.
5. **`GitHubPlugin` (`github`)**:
   - Tools: `search_repositories(query)`, `get_repository(owner, repo)`, `list_issues(owner, repo)`, `get_file_contents(owner, repo, path)`.
6. **Enterprise Integrations Catalog**:
   - Pre-configured connectable adapters for **Gmail**, **Google Drive**, **Microsoft Outlook**, **Google Calendar**, **Slack**, **Dropbox**, **Notion**, and **Relational Databases**.

---

## 7. Frontend Architecture & UI/UX Design System

### 7.1 Single Page Application (SPA) 4-View Structure
The frontend (`templates/index.html` and `static/js/script.js`) is divided into 4 primary views switched without page reloads:
1. **Chat View (`#chatView`)**: The core ChatGPT/Claude style conversation interface with rolling message log, auto-resizing composer, pre-send attachment previews, and model selector popover.
2. **Scheduled Tasks View (`#scheduledView`)**: Interface for managing automated AI tasks with natural language input bar, 6 recommended quick-start templates, status filters, and execution history modal.
3. **Translation View (`#translationView`)**: Two-panel side-by-side translation suite with language dropdowns, document translation uploader, speech controls, and tone mode pills.
4. **Apps / Plugins Marketplace View (`#pluginsView`)**: App store interface displaying installed/available plugins, category filters, connection modals, permission management dialogs, test sandboxes, and audit logs.

### 7.2 Styling & Aesthetics (`static/css/style.css`)
- **Design Tokens**: Tailored CSS custom properties for dark glassmorphic mode (`--bg-primary: #0f172a`, `--card-bg: rgba(30, 41, 59, 0.7)`, `--accent-blue: #2563eb`).
- **Typography**: Uses **Inter** for clean UI typography and **JetBrains Mono** for code snippets and mathematical formulas.
- **Mathematical Rendering**: Built-in CSS overrides for **KaTeX** math equations ensuring high-contrast display equations and fraction bars.
- **Micro-Animations**: Shimmering skeleton loaders, bouncing typing dots, pulsing live recording mic buttons, and smooth modal fade-ins.

### 7.3 Frontend Features Matrix
| Feature | Implementation Mechanism | User Experience |
| :--- | :--- | :--- |
| **SSE Streaming** | `EventSource` / `fetch` readable stream | Instant token-by-token text generation with auto-scroll |
| **Voice Input (STT)** | `webkitSpeechRecognition` / `SpeechRecognition` | Tap microphone icon to speak prompts directly |
| **Voice Read Aloud (TTS)** | `window.speechSynthesis.speak()` | Natural voice reading of translations and AI responses |
| **KaTeX Math Engine** | `renderMathInElement()` auto-render extension | Instant crisp LaTeX formula formatting in real-time |
| **File Drag & Drop** | Fullscreen `#dropzoneOverlay` event listeners | Drag files anywhere on the window to trigger attachment preview |
| **Session Persistence** | `localStorage` + Flask Session Cookies | Chats, pinned items, and draft states persist across reloads |
| **Export Formats** | Dynamic Blob Generation | One-click copy transcript or export conversation |

---

## 8. Configuration & Environment Variables

The project uses `.env` (`.env.example`) to manage all configuration parameters.

### Environment Variable Reference
```ini
# =============================================================================
# Cloud-Based AI Chatbot - Environment Configuration Template
# =============================================================================

# Option 1: Google AI Studio Key (100% Free - https://aistudio.google.com/apikey)
GEMINI_API_KEY=AIzaSy...your_google_ai_studio_api_key_here

# Option 2: OpenRouter API Key (https://openrouter.ai/keys)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here

# AI Model Identifier
OPENROUTER_MODEL=google/gemini-3.7-flash

# Enable Web Search Grounding for current live data (true / false)
ENABLE_WEB_SEARCH=true

# Flask Session Security Secret Key
FLASK_SECRET_KEY=production-crypto-random-secret-key-hpcc-2026

# Server Host Port & Debug Mode
FLASK_DEBUG=False
PORT=5000

# Multimodal Generation Settings (Image & Video)
IMAGE_GENERATION_PROVIDER=auto
VIDEO_GENERATION_PROVIDER=auto

# Microsoft Azure Cloud Services Integration (Optional)
# AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;
# AZURE_STORAGE_CONTAINER_NAME=chatbot-uploads
# APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
# AZURE_SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:...;Database=...;
```

---

## 9. Deployment & Cloud DevOps Runbook

### 9.1 Local Development Setup

#### 1. Clone & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/<your-username>/cloud-ai-chatbot.git
cd cloud-ai-chatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Linux / macOS / WSL)
source venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure `.env`
```bash
# Copy example template
copy .env.example .env     # On Windows
cp .env.example .env       # On Linux/macOS
```
*Open `.env` and set `GEMINI_API_KEY` or `OPENROUTER_API_KEY`.*

#### 4. Run Verification Tests & Start Server
```bash
python test_verification.py
python app.py
```
*Open your browser and navigate to `http://localhost:5000`.*

---

### 9.2 Microsoft Azure App Service Deployment (Linux Python 3.11)

#### 1. Azure CLI Provisioning Commands
```bash
# 1. Authenticate with Azure
az login

# 2. Create Resource Group
az group create --name rg-cloud-ai-chatbot --location eastus

# 3. Create Linux App Service Plan (Basic B1 or Free F1)
az appservice plan create --name plan-cloud-ai-chatbot --resource-group rg-cloud-ai-chatbot --sku B1 --is-linux

# 4. Create Web App with Python 3.11 Runtime
az webapp create --resource-group rg-cloud-ai-chatbot --plan plan-cloud-ai-chatbot --name cloud-ai-chatbot-app --runtime "PYTHON:3.11"

# 5. Configure Gunicorn Startup Command
az webapp config set --resource-group rg-cloud-ai-chatbot --name cloud-ai-chatbot-app --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"

# 6. Configure Production Environment Variables
az webapp config appsettings set --resource-group rg-cloud-ai-chatbot --name cloud-ai-chatbot-app --settings \
    OPENROUTER_API_KEY="sk-or-v1-your-key" \
    OPENROUTER_MODEL="google/gemini-3.7-flash" \
    ENABLE_WEB_SEARCH="true" \
    FLASK_SECRET_KEY="secure-production-random-secret-key" \
    FLASK_DEBUG="False"
```

#### 2. Deploy Code via Azure ZIP Deployment
```bash
# Create deployment package (excluding venv, cache, and .env)
git archive -o deployment.zip HEAD

# Deploy ZIP to Azure App Service
az webapp deploy --resource-group rg-cloud-ai-chatbot --name cloud-ai-chatbot-app --src-path deployment.zip --type zip
```

---

## 10. Automated Verification & Test Suite

The project includes 3 comprehensive automated test suites:

### 10.1 Core System Verification (`test_verification.py`)
- `test_01_health_endpoint`: Asserts `/api/health` returns HTTP 200, status `ok`, and provider metadata.
- `test_02_index_page`: Verifies HTML layout, meta tags, and SPA DOM nodes.
- `test_03_txt_file_processing`: Validates multi-encoding string extraction from `.txt`.
- `test_04_docx_file_processing`: Tests paragraph and table extraction from `.docx`.
- `test_05_pdf_file_processing`: Tests PDF page extraction and blank PDF rejection.
- `test_06_image_file_detection`: Verifies MIME type classification for PNG, JPG, WEBP.
- `test_07_invalid_file_rejection`: Asserts `.exe` and `.zip` uploads return HTTP 400.
- `test_08_oversized_file_rejection`: Asserts files > 10MB trigger HTTP 413.
- `test_09_clear_conversation`: Tests session reset via `/api/clear`.

### 10.2 Mathematical Reasoning Verification (`test_math_analysis.py`)
- Validates equation pattern recognition for Parallel Speedup ($S = T_s/T_p$), Linear Equations ($y=mx+c$), Quadratic Discriminants ($D=b^2-4ac$), Matrix operations, and Calculus Gradients.
- Verifies prompt augmentation scaffolding and fallback report generation.

### 10.3 Plugin Ecosystem & Sandbox Verification (`test_plugin_marketplace.py`)
- Tests plugin listing, category filtering, search filtering.
- Validates permission checks, unauthorized tool blocking, and execution logging in `data/plugin_logs.json`.
- Tests Calculator, Web Search, and File Analysis tools in sandboxed runtime.
