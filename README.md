# Cloud-Based AI Chatbot with File Analysis Using Gemini and Microsoft Azure

> **Subject:** High Performance Cloud Computing (HPCC) — College Mini-Project  
> **Tech Stack:** Python (Flask), OpenRouter API (Gemini Flash), OpenAI Python SDK, HTML5 / CSS3 / JavaScript (Vanilla Modern UI), Gunicorn, Microsoft Azure (App Service, Blob Storage, Application Insights, Key Vault).

---

## 📌 1. Project Overview

This project is a high-performance, cloud-native conversational AI web application designed to demonstrate cloud computing principles, serverless/managed platform deployment, and advanced multimodal artificial intelligence.

The application allows users to:
1. Conduct real-time natural language conversations with Google's state-of-the-art **Gemini 2.0 Flash** model routed securely via the **OpenRouter OpenAI-compatible API**.
2. Perform **Live Web Search Grounding** to answer time-sensitive and recent questions (e.g., current sports events, recent news regarding Lionel Messi / Argentina, emerging technology updates) directly from the live web.
3. Upload and analyze **PDF, TXT, and Word (.docx)** documents with automatic server-side text and table extraction.
4. Upload and analyze **Images (.png, .jpg, .jpeg, .webp)** using multimodal base64 vision processing.
5. Deploy seamlessly to **Microsoft Azure App Service** using Gunicorn as the production WSGI server.

---

## 🏗️ 2. System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                        Client Browser (Modern Responsive UI)                      |
|  - Dark-Themed Glassmorphism Interface (ChatGPT / Claude style)                   |
|  - Real-time Markdown Rendering (Marked.js) + Code Highlighting (Highlight.js)    |
|  - Auto-Growing Textarea + Enter-to-Send + Shift+Enter for Newline                |
|  - File Pre-Send Attachment Preview with Type Badges & Remove Button              |
|  - Animated Bouncing Dots Typing Indicator                                        |
+-----------------------------------------+-----------------------------------------+
                                          | HTTP REST (FormData / JSON)
                                          v
+-----------------------------------------------------------------------------------+
|                     Flask Web Server (Backend / app.py)                          |
|  - Endpoints: / (UI), /api/chat (POST), /api/clear (POST), /api/health (GET)      |
|  - Rolling 20-turn Session-based Conversation History                             |
|  - Maximum 10MB File Size Enforcement & Path Traversal Sanitation                 |
|  - Azure App Service Ready with Gunicorn WSGI runner                              |
+--------------------+------------------------------------+-------------------------+
                     |                                    |
                     v                                    v
+------------------------------------+   +------------------------------------------+
|      utils/file_processor.py       |   |          utils/gemini_client.py          |
|  - PDF: Page text extraction       |   |  - OpenAI-compatible Python SDK Client   |
|    using pypdf                     |   |  - Base URL: https://openrouter.ai/api/v1|
|  - DOCX: Paragraphs & tables using |   |  - Model: google/gemini-2.0-flash-001    |
|    python-docx                     |   |  - Base64 Multimodal Vision Payload      |
|  - TXT: Multi-encoding safe reader |   |  - Live Web Search Grounding Plugin      |
|  - Image: Format validation        |   |  - Safe Error Handlers (401, 429, 404)   |
+------------------------------------+   +--------------------+---------------------+
                                                              |
                                                              v
                                         +------------------------------------------+
                                         |         OpenRouter Cloud Gateway         |
                                         |     (Routes to Google Gemini Flash)      |
                                         +------------------------------------------+
```

---

## 📁 3. Project Structure & Components

```
c:/cloud-ai-chatbot/
├── app.py                     # Main Flask web application, routing, and session management
├── test_verification.py       # Automated unit and integration test suite
├── requirements.txt           # Python dependencies (Flask, openai, pypdf, python-docx, gunicorn)
├── .env.example               # Template for environment variables and secrets
├── .env                       # Local environment configuration (NEVER committed to Git)
├── .gitignore                 # Excludes .env, uploads/, venv/, and cache files from Git
├── README.md                  # Comprehensive project documentation and cloud deployment guide
├── static/
│   ├── css/
│   │   └── style.css          # Modern dark-mode responsive styling, glassmorphism, animations
│   └── js/
│       └── script.js          # Client controller (auto-resize, attachment preview, markdown, errors)
├── templates/
│   └── index.html             # Single-page HTML5 chat layout
├── utils/
│   ├── __init__.py            # Package initializer
│   ├── file_processor.py      # Secure file validator and text extractor (PDF/DOCX/TXT/Images)
│   └── gemini_client.py       # OpenRouter client with OpenAI SDK, Gemini Flash, Web Search, Vision
└── uploads/
    └── .gitkeep               # Directory for temporary upload processing
```

### Component Details:
1. **`app.py`**:
   - Exposes `GET /` to serve the single-page application.
   - Exposes `GET /api/health` for Azure health probes and service status verification.
   - Exposes `POST /api/chat` supporting both multipart form data (files + text) and plain text queries.
   - Exposes `POST /api/clear` to reset the user's session history.
2. **`utils/gemini_client.py`**:
   - Initializes an `OpenAI` client pointing to `https://openrouter.ai/api/v1`.
   - Uses `google/gemini-3.7-flash` (or `google/gemini-2.5-flash`).
   - Supports OpenRouter's live web search plugin (`plugins: [{"id": "web"}]`) for real-time information retrieval.
   - Formats images as base64 data URLs (`data:image/png;base64,...`) for vision models.
   - Implements defensive error handling for authentication (401), rate limits / quotas (429), unavailable models (404), and network drops (503).
3. **`utils/file_processor.py`**:
   - Enforces 10 MB upload limits and verifies allowed extensions (`.pdf`, `.txt`, `.docx`, `.png`, `.jpg`, `.jpeg`, `.webp`).
   - Extracts plain text from PDFs using `pypdf` across all pages.
   - Extracts paragraphs and tables from Word documents using `python-docx`.
   - Reads text files using UTF-8, Latin-1, and CP1252 fallbacks.

---

## 🚀 4. Local Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed
- Git installed
- An OpenRouter API Key from [https://openrouter.ai/keys](https://openrouter.ai/keys)

### Step 1: Clone the Repository
```bash
git clone https://github.com/<your-username>/cloud-ai-chatbot.git
cd cloud-ai-chatbot
```

### Step 2: Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If script execution is restricted on Windows PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

**On Linux / macOS / WSL:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to create `.env`:
```powershell
# Windows PowerShell:
Copy-Item .env.example .env

# Linux / macOS / WSL:
cp .env.example .env
```

Open `.env` in any text editor and fill in your OpenRouter API key:
```ini
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=google/gemini-2.0-flash-001
ENABLE_WEB_SEARCH=true
FLASK_SECRET_KEY=your-random-session-secret-key-12345
FLASK_DEBUG=True
PORT=5000
```

### Step 5: Run Automated Verification Tests
```bash
python test_verification.py
```
*Expected Output: `Ran 9 tests in 0.18s ... OK`*

### Step 6: Start the Local Development Server
```bash
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## 🧪 5. Testing Every Feature

| Feature | How to Test | Expected Result |
| :--- | :--- | :--- |
| **Normal AI Conversation** | Type *"Explain the difference between IaaS, PaaS, and SaaS"* and press <kbd>Enter</kbd> | Clean response with Markdown formatting, bullet points, and definitions. |
| **Enter-to-Send & Shift+Enter** | Type line 1, press <kbd>Shift</kbd>+<kbd>Enter</kbd>, type line 2, press <kbd>Enter</kbd> | New line created without sending; Enter submits the multiline message. |
| **Live Web Search Grounding** | Type *"What is the latest news and current match status of Lionel Messi with the Argentina national team?"* | Live web-grounded answer containing recent dates and match events. |
| **PDF Analysis** | Click 📎, select a PDF document, type *"Summarize this document"*, click Send | Extracts PDF pages, analyzes content, and provides a structured summary. |
| **Word (.docx) Analysis** | Attach a `.docx` file containing text or tables, ask *"What does this file cover?"* | Extracts paragraphs and tables, answering questions accurately. |
| **Plain Text (.txt) Analysis** | Attach a `.txt` file and ask questions about its content | Instant analysis without upload delays. |
| **Image Vision Analysis** | Attach a `.png` or `.jpg` photo/diagram and ask *"Describe this image in detail"* | Multimodal vision model inspects visual elements and describes them. |
| **File Pre-Send Preview & Remove** | Click 📎, select any file, observe the preview card above the input, then click ✕ | File is removed and composer resets cleanly. |
| **Clear Conversation** | Click the **"🗑️ Clear Chat"** or **"+ New Chat"** button | Conversation history resets and returns to empty state greeting. |
| **Invalid File Type Rejection** | Attempt to attach an unsupported file (e.g. `.exe`, `.zip`) | Clear error: *"Unsupported file type. Allowed formats: .docx, .jpeg, .jpg, .pdf, .png, .txt, .webp"*. |
| **Oversized File Rejection** | Attempt to attach a file larger than 10 MB | Clear error: *"File is too large. Maximum allowed size is 10 MB."* |
| **Invalid / Missing Key Error** | Set `OPENROUTER_API_KEY=your_key_here` in `.env` and send a message | Clear error: *"OPENROUTER_API_KEY is not configured... (401)"* without server crash. |

---

## 🔒 6. Safe Git & GitHub Upload Instructions

To ensure API keys and user uploads are never exposed publicly:

1. **Verify `.gitignore` is active:**
   ```bash
   git status
   ```
   *Ensure `.env`, `venv/`, and `uploads/` (except `.gitkeep`) are NOT listed in untracked files.*

2. **Commit and Push Safely:**
   ```bash
   git add .
   git commit -m "feat: complete Cloud AI Chatbot with OpenRouter, Gemini Flash, Web Search, and modern UI"
   git branch -M main
   git remote add origin https://github.com/<your-username>/cloud-ai-chatbot.git
   git push -u origin main
   ```

---

## ☁️ 7. Microsoft Azure App Service Deployment

### Method A: Deploy via Azure CLI (Recommended)

1. **Login to Azure:**
   ```bash
   az login
   ```

2. **Create a Resource Group:**
   ```bash
   az group create --name rg-cloud-chatbot --location eastus
   ```

3. **Create an App Service Linux Plan (B1 or Free F1):**
   ```bash
   az appservice plan create --name plan-cloud-chatbot --resource-group rg-cloud-chatbot --sku B1 --is-linux
   ```

4. **Create the Web App (Python 3.11):**
   ```bash
   az webapp create --resource-group rg-cloud-chatbot --plan plan-cloud-chatbot --name cloud-ai-chatbot-app --runtime "PYTHON:3.11"
   ```

5. **Configure Gunicorn Startup Command:**
   ```bash
   az webapp config set --resource-group rg-cloud-chatbot --name cloud-ai-chatbot-app --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
   ```

6. **Set Environment Variables on Azure:**
   ```bash
   az webapp config appsettings set --resource-group rg-cloud-chatbot --name cloud-ai-chatbot-app --settings \
       OPENROUTER_API_KEY="sk-or-v1-your-actual-key" \
       OPENROUTER_MODEL="google/gemini-2.0-flash-001" \
       ENABLE_WEB_SEARCH="true" \
       FLASK_SECRET_KEY="production-secret-key-hpcc" \
       FLASK_DEBUG="False"
   ```

7. **Deploy Code via ZIP or Git:**
   ```bash
   az webapp up --resource-group rg-cloud-chatbot --name cloud-ai-chatbot-app
   ```

---

## 🗺️ 8. Cloud Architecture Roadmap (20% to 100%)

```
[ Phase 1: 20% (COMPLETED) ]
  • Modern ChatGPT/Claude UI + Responsive dark theme
  • OpenRouter OpenAI-SDK Integration with Gemini 2.0 Flash
  • Live Web Search Grounding for current information
  • PDF, DOCX, TXT and Multimodal Image analysis
  • Gunicorn WSGI + Health check endpoint (/api/health)
       │
       ▼
[ Phase 2: 40% (Azure Blob Storage Integration) ]
  • Replace local /uploads folder with Azure Blob Storage container
  • Upload files directly to Azure Blob using `azure-storage-blob` SDK
  • Generate secure SAS (Shared Access Signature) tokens for temporary file URLs
       │
       ▼
[ Phase 3: 60% (Azure Application Insights) ]
  • Add `opencensus-ext-azure` / Azure Monitor OpenTelemetry
  • Track API latency, request rates, 429 rate limit telemetry, and error rates in real-time
       │
       ▼
[ Phase 4: 80% (Azure Key Vault & Managed Identity) ]
  • Eliminate API keys from App Service configuration
  • Enable Azure System-Assigned Managed Identity
  • Fetch OPENROUTER_API_KEY securely from Azure Key Vault at runtime
       │
       ▼
[ Phase 5: 100% (Enterprise Scalability & Vector RAG) ]
  • Azure Cosmos DB for persistent user conversation history & auth
  • Azure AI Search (Cognitive Search) vector index for semantic document search (RAG)
```

---

## 🛠️ 9. Common Errors & Troubleshooting

| Error | Cause | Solution |
| :--- | :--- | :--- |
| **401 Unauthorized** | Missing or invalid `OPENROUTER_API_KEY` in `.env` | Ensure your key in `.env` starts with `sk-or-v1-...` and has available credits on OpenRouter. |
| **429 Rate Limit / Quota Exceeded** | OpenRouter rate limit reached or zero credit balance | Wait a few moments or verify your OpenRouter account balance at [openrouter.ai/credits](https://openrouter.ai/credits). |
| **404 Model Not Found** | Outdated or misspelled `OPENROUTER_MODEL` | Set `OPENROUTER_MODEL=google/gemini-2.0-flash-001` in `.env`. |
| **503 Network Error** | Client unable to connect to OpenRouter servers | Check your local internet connection, firewall, or proxy settings. |
| **Unsupported File Type (400)** | User uploaded unsupported format (e.g. `.zip`, `.exe`) | Upload only `.pdf`, `.txt`, `.docx`, `.png`, `.jpg`, `.jpeg`, `.webp`. |
| **413 File Too Large** | Uploaded file exceeds 10 MB | Compress or crop the file before uploading. |
| **ModuleNotFoundError: No module named 'openai'** | Dependencies not installed in the active virtual environment | Run `pip install -r requirements.txt` inside your virtual environment (`venv`). |

---

## 🎓 10. College Review Summary

This project demonstrates:
- **Cloud Computing Principles**: Stateless application architecture suitable for horizontal auto-scaling on cloud platforms.
- **Modern AI Integration**: Decoupled AI client abstraction using the industry-standard OpenAI SDK connecting to OpenRouter.
- **Multimodal Computing**: Handling both text documents (PDF/DOCX/TXT) and vision inputs (PNG/JPG/WEBP).
- **Web Grounding**: Dynamic retrieval of current events using real-time search plugins.
- **Security Best Practices**: Strict exclusion of API keys from source control, input sanitation, path traversal protection, and environment variable configuration.
