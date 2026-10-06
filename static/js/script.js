/**
 * Cloud AI Chatbot - Modern Multimodal AI Assistant & Scheduler Controller
 * 
 * Features:
 * 1. Chat Experience:
 *    - Real-time SSE streaming with typing cursor & Stop Generating button
 *    - Animated thinking / analyzing indicator
 *    - Smart auto-scrolling (does not force scroll when user reads history)
 *    - Markdown rendering with code blocks and copy buttons
 *    - Pinned, Recent, Archived conversations with search filter
 *    - Message timestamps & Inline edit and resend
 *    - Multimodal Image & Asynchronous Video generation modes
 *    - Speech-to-Text (Web Speech API) & Read Aloud (TTS)
 *    - Model & Reasoning Effort selector flyouts
 * 2. Scheduled Tasks Interface:
 *    - Dedicated Scheduled view seamlessly switchable from sidebar
 *    - Large ChatGPT-style Natural Language schedule input bar with voice & submit
 *    - Interactive Recommended task cards (Email, Briefing, Study, Website, Price, Report)
 *    - Task Confirmation & Configuration modal with recurrence (Once, Daily, Weekly, Weekdays, Custom)
 *    - Task Card list with status badges (Active, Paused, Completed, Failed)
 *    - Status filter dropdown [ Active ▼ ] (All, Active, Paused, Completed, Failed)
 *    - Immediate "Run Now" execution with loading state & history logging
 *    - Execution History modal with duration, status, and rendered Markdown outputs
 *    - Settings modal with Azure Webhook /api/tasks/tick documentation
 *    - Session isolation ensuring private tasks per user
 */

document.addEventListener("DOMContentLoaded", () => {
  // ---------------------------------------------------------------------------
  // View Router State & Elements
  // ---------------------------------------------------------------------------
  const chatView = document.getElementById("chatView");
  const scheduledView = document.getElementById("scheduledView");
  const translationView = document.getElementById("translationView");
  const pluginsView = document.getElementById("pluginsView");
  const sidebarScheduledBtn = document.getElementById("sidebarScheduledBtn");
  const sidebarTranslationBtn = document.getElementById("sidebarTranslationBtn");
  const sidebarPluginsBtn = document.getElementById("sidebarPluginsBtn");
  const sidebarSettingsBtn = document.getElementById("sidebarSettingsBtn");
  const taskSettingsModal = document.getElementById("taskSettingsModal");
  const closeSettingsModalBtn = document.getElementById("closeSettingsModalBtn");

  let currentView = "chat"; // "chat" | "scheduled" | "translation" | "plugins"

  // Unique session ID for isolating scheduled tasks per user/browser
  let userSessionId = localStorage.getItem("cloud_ai_user_session_id");
  if (!userSessionId) {
    userSessionId = "usr_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("cloud_ai_user_session_id", userSessionId);
  }

  function switchToView(viewName) {
    currentView = viewName;

    if (chatView) chatView.classList.toggle("hidden", viewName !== "chat");
    if (scheduledView) scheduledView.classList.toggle("hidden", viewName !== "scheduled");
    if (translationView) translationView.classList.toggle("hidden", viewName !== "translation");
    if (pluginsView) pluginsView.classList.toggle("hidden", viewName !== "plugins");

    if (sidebarScheduledBtn) sidebarScheduledBtn.classList.toggle("active", viewName === "scheduled");
    if (sidebarTranslationBtn) sidebarTranslationBtn.classList.toggle("active", viewName === "translation");
    if (sidebarPluginsBtn) sidebarPluginsBtn.classList.toggle("active", viewName === "plugins");

    if (viewName === "chat") {
      const current = getActiveSession();
      if (current) {
        document.querySelectorAll(".chat-item").forEach((el) => {
          el.classList.toggle("active", el.dataset.id === current.id);
        });
      }
    } else {
      document.querySelectorAll(".chat-item").forEach((el) => el.classList.remove("active"));
    }

    closeMobileSidebar();

    if (viewName === "scheduled") {
      loadScheduledTasks();
    } else if (viewName === "translation") {
      initTranslationView();
    } else if (viewName === "plugins") {
      loadPluginsMarketplace();
    }
  }

  if (sidebarScheduledBtn) {
    sidebarScheduledBtn.addEventListener("click", () => switchToView("scheduled"));
  }

  if (sidebarTranslationBtn) {
    sidebarTranslationBtn.addEventListener("click", () => switchToView("translation"));
  }

  if (sidebarPluginsBtn) {
    sidebarPluginsBtn.addEventListener("click", () => switchToView("plugins"));
  }

  if (sidebarSettingsBtn) {
    sidebarSettingsBtn.addEventListener("click", () => {
      if (taskSettingsModal) {
        taskSettingsModal.classList.remove("hidden");
        taskSettingsModal.style.display = "flex";
      }
    });
  }

  if (closeSettingsModalBtn && taskSettingsModal) {
    closeSettingsModalBtn.addEventListener("click", () => {
      taskSettingsModal.classList.add("hidden");
      taskSettingsModal.style.display = "none";
    });
    taskSettingsModal.addEventListener("click", (e) => {
      if (e.target === taskSettingsModal) {
        taskSettingsModal.classList.add("hidden");
        taskSettingsModal.style.display = "none";
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Chat View Elements & State
  // ---------------------------------------------------------------------------
  const messagesEl = document.getElementById("messages");
  const emptyStateEl = document.getElementById("emptyState");
  const composerForm = document.getElementById("composerForm");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const stopBtn = document.getElementById("stopBtn");
  const attachBtn = document.getElementById("attachBtn");
  const fileInput = document.getElementById("fileInput");

  // Plus Dropdown Menu & Modes
  const plusDropdownMenu = document.getElementById("plusDropdownMenu");
  const plusUploadFileBtn = document.getElementById("plusUploadFileBtn");
  const plusGenerateImageBtn = document.getElementById("plusGenerateImageBtn");
  const plusGenerateVideoBtn = document.getElementById("plusGenerateVideoBtn");

  const activeModeChip = document.getElementById("activeModeChip");
  const activeModeIcon = document.getElementById("activeModeIcon");
  const activeModeLabel = document.getElementById("activeModeLabel");
  const clearModeBtn = document.getElementById("clearModeBtn");

  // File Preview & Drag-and-drop
  const filePreview = document.getElementById("filePreview");
  const filePreviewIcon = document.getElementById("filePreviewIcon");
  const filePreviewName = document.getElementById("filePreviewName");
  const filePreviewSize = document.getElementById("filePreviewSize");
  const fileUploadProgressBar = document.getElementById("fileUploadProgressBar");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const dropzoneOverlay = document.getElementById("dropzoneOverlay");
  const closeDropzoneBtn = document.getElementById("closeDropzoneBtn");

  // Sidebar & Search
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const mobileSidebarToggle = document.getElementById("mobileSidebarToggle");
  const newChatBtn = document.getElementById("newChatBtn");
  const mobileNewChatBtn = document.getElementById("mobileNewChatBtn");
  const chatSearchInput = document.getElementById("chatSearchInput");
  const clearSearchBtn = document.getElementById("clearSearchBtn");

  // Chat Lists
  const pinnedChatList = document.getElementById("pinnedChatList");
  const recentChatList = document.getElementById("recentChatList");
  const archivedChatList = document.getElementById("archivedChatList");
  const pinnedCountEl = document.getElementById("pinnedCount");
  const recentCountEl = document.getElementById("recentCount");
  const archivedCountEl = document.getElementById("archivedCount");
  const archivedToggleBtn = document.getElementById("archivedToggleBtn");
  const archivedChevron = document.getElementById("archivedChevron");

  // Header Options
  const chatTitleDisplay = document.getElementById("chatTitleDisplay");
  const shareBtn = document.getElementById("shareBtn");
  const shareDropdownMenu = document.getElementById("shareDropdownMenu");
  const shareCopyTranscriptBtn = document.getElementById("shareCopyTranscriptBtn");
  const shareCopyLinkBtn = document.getElementById("shareCopyLinkBtn");

  const headerMenuBtn = document.getElementById("headerMenuBtn");
  const headerDropdownMenu = document.getElementById("headerDropdownMenu");
  const headerRenameBtn = document.getElementById("headerRenameBtn");
  const headerPinBtn = document.getElementById("headerPinBtn");
  const headerArchiveBtn = document.getElementById("headerArchiveBtn");
  const headerViewFilesBtn = document.getElementById("headerViewFilesBtn");
  const headerClearBtn = document.getElementById("headerClearBtn");
  const headerDeleteBtn = document.getElementById("headerDeleteBtn");

  // Model Selector & Microphone
  const modelMenuBtn = document.getElementById("modelMenuBtn");
  const modelMenuLabel = document.getElementById("modelMenuLabel");
  const modelPopoverMenu = document.getElementById("modelPopoverMenu");
  const micBtn = document.getElementById("micBtn");
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const webSearchToggleBtn = document.getElementById("webSearchToggleBtn");

  // Web Search State (Persistent)
  const WEB_SEARCH_STORAGE_KEY = "cloud_ai_web_search_enabled";
  let isWebSearchEnabled = localStorage.getItem(WEB_SEARCH_STORAGE_KEY) !== "false";

  function updateWebSearchUI() {
    if (webSearchToggleBtn) {
      webSearchToggleBtn.classList.toggle("active", isWebSearchEnabled);
      webSearchToggleBtn.title = isWebSearchEnabled
        ? "Web Search: Enabled (Grounding with live web data)"
        : "Web Search: Disabled (Using model knowledge)";
    }
  }
  updateWebSearchUI();

  if (webSearchToggleBtn) {
    webSearchToggleBtn.addEventListener("click", () => {
      isWebSearchEnabled = !isWebSearchEnabled;
      localStorage.setItem(WEB_SEARCH_STORAGE_KEY, isWebSearchEnabled ? "true" : "false");
      updateWebSearchUI();
      showToast(isWebSearchEnabled ? "Web Search Enabled 🌐" : "Web Search Disabled 🌐");
    });
  }

  // Chat Context Menu & Toast
  const chatContextMenu = document.getElementById("chatItemContextMenu");
  const ctxPinBtn = document.getElementById("ctxPinBtn");
  const ctxRenameBtn = document.getElementById("ctxRenameBtn");
  const ctxArchiveBtn = document.getElementById("ctxArchiveBtn");
  const ctxDeleteBtn = document.getElementById("ctxDeleteBtn");
  const toastNotification = document.getElementById("toastNotification");

  // Model & Reasoning Effort Constants
  const MODEL_STORAGE_KEY = "cloud_ai_selected_model";
  const EFFORT_STORAGE_KEY = "cloud_ai_selected_effort";

  const MODEL_NAMES = {
    "google/gemini-3.7-flash": "Gemini 3.7 Flash",
    "google/gemini-3.6-flash": "Gemini 3.6 Flash",
    "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
  };

  const EFFORT_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
  };

  let selectedModel = localStorage.getItem(MODEL_STORAGE_KEY) || "google/gemini-3.7-flash";
  if (!MODEL_NAMES[selectedModel]) selectedModel = "google/gemini-3.7-flash";

  let selectedEffort = localStorage.getItem(EFFORT_STORAGE_KEY) || "medium";
  if (!EFFORT_LABELS[selectedEffort]) selectedEffort = "medium";

  // Application State
  let composerMode = "chat"; // "chat" | "image" | "video"
  let selectedFile = null;
  let isSending = false;
  let currentAbortController = null;
  let activeChatId = null;
  let contextTargetChatId = null;
  let activeSpeechUtterance = null;
  let activeSpeechBtn = null;
  let isArchivedOpen = false;
  let searchQuery = "";

  // ---------------------------------------------------------------------------
  // LocalStorage Sessions Management
  // ---------------------------------------------------------------------------
  const STORAGE_KEY = "cloud_ai_chatbot_user_conversations";

  function loadSessions() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          return parsed.filter((s) => s.messages && s.messages.length > 0);
        }
      }
    } catch (e) {
      console.warn("Could not load sessions", e);
    }
    return [];
  }

  function saveSessions() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (e) {
      console.warn("Could not save sessions", e);
    }
  }

  function getActiveSession() {
    return sessions.find((s) => s.id === activeChatId) || null;
  }

  let sessions = loadSessions();
  activeChatId = sessions.length > 0 ? sessions[0].id : null;

  // ---------------------------------------------------------------------------
  // Configure Marked.js
  // ---------------------------------------------------------------------------
  if (window.marked) {
    marked.setOptions({
      gfm: true,
      breaks: true,
      highlight: function (code, lang) {
        if (window.hljs && lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(code, { language: lang }).value;
          } catch (e) {}
        }
        return code;
      },
    });
  }

  // ---------------------------------------------------------------------------
  // Model Selector Setup
  // ---------------------------------------------------------------------------
  function updateModelButtonLabel() {
    if (!modelMenuLabel) return;
    const mName = MODEL_NAMES[selectedModel] || "Gemini 3.7 Flash";
    const eName = EFFORT_LABELS[selectedEffort] || "Medium";
    modelMenuLabel.textContent = `${mName} ${eName}`;

    if (modelPopoverMenu) {
      modelPopoverMenu.querySelectorAll(".model-entry").forEach((entry) => {
        const isThisModel = entry.dataset.model === selectedModel;
        entry.classList.toggle("selected", isThisModel);

        const effortPill = entry.querySelector(".model-entry-effort");
        if (effortPill) {
          effortPill.textContent = isThisModel ? (EFFORT_LABELS[selectedEffort] || "Medium") : "Medium";
        }

        entry.querySelectorAll(".effort-option").forEach((opt) => {
          if (isThisModel) {
            opt.classList.toggle("active", opt.dataset.effort === selectedEffort);
          } else {
            opt.classList.toggle("active", opt.dataset.effort === "medium");
          }
        });
      });
    }
  }

  updateModelButtonLabel();

  if (modelMenuBtn) {
    modelMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isHidden = modelPopoverMenu.classList.contains("hidden");
      if (isHidden) {
        modelPopoverMenu.classList.remove("hidden");
        modelMenuBtn.classList.add("active");
      } else {
        modelPopoverMenu.classList.add("hidden");
        modelMenuBtn.classList.remove("active");
      }
    });
  }

  if (modelPopoverMenu) {
    modelPopoverMenu.querySelectorAll(".model-entry").forEach((entry) => {
      const modelId = entry.dataset.model;

      entry.addEventListener("click", (e) => {
        if (e.target.closest(".effort-option")) return;
        selectedModel = modelId;
        localStorage.setItem(MODEL_STORAGE_KEY, selectedModel);
        updateModelButtonLabel();
        modelPopoverMenu.classList.add("hidden");
        if (modelMenuBtn) modelMenuBtn.classList.remove("active");
        showToast(`Model set to ${MODEL_NAMES[selectedModel]} (${EFFORT_LABELS[selectedEffort]}) ✦`);
      });

      entry.querySelectorAll(".effort-option").forEach((opt) => {
        opt.addEventListener("click", (e) => {
          e.stopPropagation();
          const effort = opt.dataset.effort;
          selectedModel = modelId;
          selectedEffort = effort;
          localStorage.setItem(MODEL_STORAGE_KEY, selectedModel);
          localStorage.setItem(EFFORT_STORAGE_KEY, selectedEffort);
          updateModelButtonLabel();
          modelPopoverMenu.classList.add("hidden");
          if (modelMenuBtn) modelMenuBtn.classList.remove("active");
          showToast(`${MODEL_NAMES[selectedModel]} (${EFFORT_LABELS[effort]} effort) selected! ✦`);
        });
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Speech-to-Text Microphone (Web Speech API)
  // ---------------------------------------------------------------------------
  const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

  function setupSpeechRecognition(buttonEl, targetInputEl, onFinish) {
    if (!buttonEl) return;
    let recognizer = null;
    let isRecording = false;

    buttonEl.addEventListener("click", () => {
      if (!SpeechRecognitionAPI) {
        showToast("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
        return;
      }
      if (isRecording) {
        stopRec();
      } else {
        startRec();
      }
    });

    function startRec() {
      try {
        recognizer = new SpeechRecognitionAPI();
        recognizer.continuous = true;
        recognizer.interimResults = true;
        recognizer.lang = "en-US";

        let initialText = targetInputEl.value;
        if (initialText && !initialText.endsWith(" ")) initialText += " ";

        recognizer.onstart = () => {
          isRecording = true;
          buttonEl.classList.add("listening");
          buttonEl.title = "Listening... Click to stop";
          showToast("Listening... Speak into your microphone 🎙️");
        };

        recognizer.onresult = (event) => {
          let transcript = "";
          for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          targetInputEl.value = initialText + transcript;
          if (onFinish) onFinish();
        };

        recognizer.onerror = (event) => {
          console.warn("Speech error:", event.error);
          if (event.error === "not-allowed") {
            showToast("Microphone access denied. Please allow microphone permissions.");
          }
          stopRec();
        };

        recognizer.onend = () => stopRec();
        recognizer.start();
      } catch (err) {
        stopRec();
        showToast("Could not start speech recognition.");
      }
    }

    function stopRec() {
      isRecording = false;
      buttonEl.classList.remove("listening");
      buttonEl.title = "Voice input (Click to speak)";
      if (recognizer) {
        try { recognizer.stop(); } catch (e) {}
        recognizer = null;
      }
    }
  }

  setupSpeechRecognition(micBtn, messageInput, adjustTextareaHeight);

  // ---------------------------------------------------------------------------
  // Dark / Light Theme Controller
  // ---------------------------------------------------------------------------
  const THEME_STORAGE_KEY = "cloud_ai_theme";
  const SUN_ICON = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
  const MOON_ICON = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

  function applyTheme(theme) {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      document.body.classList.add("dark-theme");
      if (themeToggleBtn) {
        themeToggleBtn.innerHTML = MOON_ICON;
        themeToggleBtn.title = "Switch to light theme (currently Dark)";
      }
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      document.body.classList.remove("dark-theme");
      if (themeToggleBtn) {
        themeToggleBtn.innerHTML = SUN_ICON;
        themeToggleBtn.title = "Switch to dark theme (currently Light)";
      }
    }
  }

  const currentTheme = localStorage.getItem(THEME_STORAGE_KEY) || "light";
  applyTheme(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const isCurrentlyDark = document.documentElement.getAttribute("data-theme") === "dark";
      const nextTheme = isCurrentlyDark ? "light" : "dark";
      localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      applyTheme(nextTheme);
      showToast(nextTheme === "dark" ? "Switched to Dark Theme 🌙" : "Switched to Light Theme ☀️");
    });
  }

  // ---------------------------------------------------------------------------
  // Modes & Composer Controls
  // ---------------------------------------------------------------------------
  function setComposerMode(mode) {
    composerMode = mode;
    if (mode === "image") {
      activeModeChip.classList.remove("hidden");
      activeModeIcon.textContent = "🖼️";
      activeModeLabel.textContent = "Image Generation Mode";
      messageInput.placeholder = "Describe the image you want to generate (e.g. A futuristic city at night)...";
      showToast("Switched to Image Generation Mode 🖼️");
    } else if (mode === "video") {
      activeModeChip.classList.remove("hidden");
      activeModeIcon.textContent = "🎬";
      activeModeLabel.textContent = "Video Generation Mode";
      messageInput.placeholder = "Describe the video you want to generate (e.g. 10-second drone view of mountains)...";
      showToast("Switched to Video Generation Mode 🎬");
    } else {
      composerMode = "chat";
      activeModeChip.classList.add("hidden");
      messageInput.placeholder = "Ask anything, @ to mention, / for actions";
    }
    messageInput.focus();
  }

  if (clearModeBtn) {
    clearModeBtn.addEventListener("click", () => setComposerMode("chat"));
  }

  // Plus Menu (+) Trigger
  if (attachBtn) {
    attachBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      plusDropdownMenu.classList.toggle("hidden");
    });
  }

  if (plusUploadFileBtn) {
    plusUploadFileBtn.addEventListener("click", () => {
      plusDropdownMenu.classList.add("hidden");
      fileInput.click();
    });
  }

  if (plusGenerateImageBtn) {
    plusGenerateImageBtn.addEventListener("click", () => {
      plusDropdownMenu.classList.add("hidden");
      setComposerMode("image");
    });
  }

  if (plusGenerateVideoBtn) {
    plusGenerateVideoBtn.addEventListener("click", () => {
      plusDropdownMenu.classList.add("hidden");
      setComposerMode("video");
    });
  }

  // ---------------------------------------------------------------------------
  // Sidebar Search & Rendering
  // ---------------------------------------------------------------------------
  if (chatSearchInput) {
    chatSearchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      if (clearSearchBtn) {
        clearSearchBtn.classList.toggle("hidden", !searchQuery);
      }
      renderSidebar();
    });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
      searchQuery = "";
      chatSearchInput.value = "";
      clearSearchBtn.classList.add("hidden");
      renderSidebar();
    });
  }

  if (archivedToggleBtn) {
    archivedToggleBtn.addEventListener("click", () => {
      isArchivedOpen = !isArchivedOpen;
      archivedChevron.classList.toggle("open", isArchivedOpen);
      archivedChatList.classList.toggle("hidden", !isArchivedOpen);
    });
  }

  function renderSidebar() {
    pinnedChatList.innerHTML = "";
    recentChatList.innerHTML = "";
    archivedChatList.innerHTML = "";

    const filterFn = (s) => {
      // Do not list empty chats with 0 messages in the sidebar history
      if (!s.messages || s.messages.length === 0) return false;
      if (!searchQuery) return true;
      const titleMatch = (s.title || "").toLowerCase().includes(searchQuery);
      const msgMatch = (s.messages || []).some((m) => (m.text || "").toLowerCase().includes(searchQuery));
      return titleMatch || msgMatch;
    };

    const filtered = sessions.filter(filterFn);
    const pinned = filtered.filter((s) => s.pinned && !s.archived);
    const recent = filtered.filter((s) => !s.pinned && !s.archived);
    const archived = filtered.filter((s) => s.archived);

    if (pinnedCountEl) pinnedCountEl.textContent = pinned.length;
    if (recentCountEl) recentCountEl.textContent = recent.length;
    if (archivedCountEl) archivedCountEl.textContent = archived.length;

    // Hide pinned section if there are no pinned chats
    const pinnedSectionEl = document.getElementById("pinnedSection");
    if (pinnedSectionEl) {
      pinnedSectionEl.style.display = pinned.length > 0 ? "block" : "none";
    }

    // Hide archived section if there are no archived chats
    const archivedSectionEl = document.getElementById("archivedSection");
    if (archivedSectionEl) {
      archivedSectionEl.style.display = archived.length > 0 ? "block" : "none";
    }

    pinned.forEach((c) => pinnedChatList.appendChild(createChatItemEl(c)));

    if (recent.length === 0) {
      const notice = document.createElement("div");
      notice.className = "empty-section-notice";
      notice.textContent = searchQuery ? "No matching chats found" : "No previous chats yet";
      recentChatList.appendChild(notice);
    } else {
      recent.forEach((c) => recentChatList.appendChild(createChatItemEl(c)));
    }

    archived.forEach((c) => archivedChatList.appendChild(createChatItemEl(c, true)));

    // Update active chat title in header
    const current = getActiveSession();
    if (chatTitleDisplay) {
      chatTitleDisplay.textContent = current ? current.title : "Cloud AI Chatbot";
    }
  }

  function createChatItemEl(chat, isArchived = false) {
    const item = document.createElement("div");
    item.className = `chat-item ${chat.id === activeChatId && currentView === "chat" ? "active" : ""} ${isArchived ? "archived" : ""}`;
    item.dataset.id = chat.id;

    const icon = isArchived ? "📦" : (chat.pinned ? "📌" : "💬");

    item.innerHTML = `
      <div class="chat-item-left">
        <span class="chat-icon">${icon}</span>
        <span class="chat-title-text" title="${escapeHtml(chat.title)}">${escapeHtml(chat.title)}</span>
      </div>
      <div class="chat-item-actions">
        ${isArchived
          ? `<button class="chat-item-unarchive-btn" title="Unarchive conversation">↩️</button>`
          : `<button class="chat-item-pin-btn" title="${chat.pinned ? "Unpin chat" : "Pin to top"}">${chat.pinned ? "✖" : "📌"}</button>`
        }
        <button class="chat-item-menu-btn" title="Chat options">•••</button>
      </div>
    `;

    item.addEventListener("click", (e) => {
      if (e.target.closest(".chat-item-actions")) return;
      selectChat(chat.id);
    });

    if (isArchived) {
      const unarchiveBtn = item.querySelector(".chat-item-unarchive-btn");
      if (unarchiveBtn) {
        unarchiveBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          chat.archived = false;
          saveSessions();
          renderSidebar();
          showToast(`Unarchived "${chat.title}" 📦`);
        });
      }
    } else {
      const pinBtn = item.querySelector(".chat-item-pin-btn");
      if (pinBtn) {
        pinBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          chat.pinned = !chat.pinned;
          saveSessions();
          renderSidebar();
          showToast(chat.pinned ? `Pinned "${chat.title}" 📌` : `Unpinned "${chat.title}"`);
        });
      }
    }

    const menuBtn = item.querySelector(".chat-item-menu-btn");
    if (menuBtn) {
      menuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        openChatContextMenu(e, chat.id);
      });
    }

    return item;
  }

  function selectChat(id) {
    switchToView("chat");
    if (activeChatId === id && currentView === "chat") return;
    stopSpeech();
    activeChatId = id;
    renderSidebar();
    loadActiveChat();
    closeMobileSidebar();
  }

  // ---------------------------------------------------------------------------
  // + New Chat Button
  // ---------------------------------------------------------------------------
  function createNewChat() {
    switchToView("chat");
    stopSpeech();
    if (currentAbortController) {
      currentAbortController.abort();
    }

    // Clean up empty sessions
    sessions = sessions.filter((s) => s.messages && s.messages.length > 0);
    saveSessions();

    const newId = "chat_" + Date.now();
    const newSession = {
      id: newId,
      title: "New chat",
      pinned: false,
      archived: false,
      createdAt: Date.now(),
      messages: [],
    };

    sessions.unshift(newSession);
    activeChatId = newId;
    saveSessions();
    renderSidebar();
    loadActiveChat();

    fetch("/api/clear", { method: "POST" }).catch(() => {});
    clearAttachment();
    setComposerMode("chat");
    messageInput.value = "";
    messageInput.style.height = "auto";
    messageInput.focus();
    closeMobileSidebar();
    showToast("Started a new conversation 💬");
  }

  if (newChatBtn) newChatBtn.addEventListener("click", createNewChat);
  if (mobileNewChatBtn) mobileNewChatBtn.addEventListener("click", createNewChat);

  // ---------------------------------------------------------------------------
  // Load & Render Active Conversation
  // ---------------------------------------------------------------------------
  function loadActiveChat() {
    messagesEl.innerHTML = "";
    const session = getActiveSession();

    if (!session || session.messages.length === 0) {
      messagesEl.appendChild(emptyStateEl);
      emptyStateEl.style.display = "flex";
    } else {
      emptyStateEl.style.display = "none";
      session.messages.forEach((msg, idx) => {
        if (msg.role === "user") {
          appendUserMessageDOM(msg.text, msg.fileName, msg.timestamp, idx);
        } else {
          let promptText = "";
          let attachedFileName = null;
          for (let i = idx - 1; i >= 0; i--) {
            if (session.messages[i].role === "user") {
              promptText = session.messages[i].text;
              attachedFileName = session.messages[i].fileName;
              break;
            }
          }

          if (msg.type === "image" && msg.imageUrl) {
            appendImageMessageDOM(msg.imageUrl, msg.text, promptText, msg.timestamp, idx);
          } else if (msg.type === "video" && msg.videoUrl) {
            appendVideoMessageDOM(msg.videoUrl, msg.text, promptText, msg.timestamp, idx);
          } else {
            appendAiMessageDOM(msg.text, msg.isError, promptText, attachedFileName, idx, msg.timestamp);
          }
        }
      });
    }
    scrollToBottom(false, true);
  }

  // ---------------------------------------------------------------------------
  // Auto-scrolling Helpers
  // ---------------------------------------------------------------------------
  function isUserScrolledNearBottom() {
    return messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 120;
  }

  function scrollToBottom(smooth = true, force = false) {
    if (force || isUserScrolledNearBottom()) {
      messagesEl.scrollTo({
        top: messagesEl.scrollHeight,
        behavior: smooth ? "smooth" : "auto",
      });
    }
  }

  function formatTime(timestamp) {
    if (!timestamp) timestamp = Date.now();
    try {
      return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return "";
    }
  }

  // ---------------------------------------------------------------------------
  // Chat Context Menu & Header Options
  // ---------------------------------------------------------------------------
  function openChatContextMenu(e, chatId) {
    contextTargetChatId = chatId;
    const targetSession = sessions.find((s) => s.id === chatId);
    if (!targetSession) return;

    ctxPinBtn.textContent = targetSession.pinned ? "📌 Unpin chat" : "📌 Pin to top";
    ctxArchiveBtn.textContent = targetSession.archived ? "📦 Unarchive" : "📦 Archive";

    const rect = e.target.getBoundingClientRect();
    chatContextMenu.style.top = `${rect.bottom + 4}px`;
    chatContextMenu.style.left = `${Math.min(rect.left, window.innerWidth - 170)}px`;
    chatContextMenu.classList.remove("hidden");
  }

  document.addEventListener("click", (e) => {
    if (chatContextMenu && !chatContextMenu.contains(e.target)) chatContextMenu.classList.add("hidden");
    if (headerDropdownMenu && !headerMenuBtn.contains(e.target) && !headerDropdownMenu.contains(e.target)) headerDropdownMenu.classList.add("hidden");
    if (shareDropdownMenu && !shareBtn.contains(e.target) && !shareDropdownMenu.contains(e.target)) shareDropdownMenu.classList.add("hidden");
    if (plusDropdownMenu && !attachBtn.contains(e.target) && !plusDropdownMenu.contains(e.target)) plusDropdownMenu.classList.add("hidden");
    if (modelPopoverMenu && modelMenuBtn && !modelMenuBtn.contains(e.target) && !modelPopoverMenu.contains(e.target)) {
      modelPopoverMenu.classList.add("hidden");
      modelMenuBtn.classList.remove("active");
    }
    if (taskFilterMenu && taskFilterBtn && !taskFilterBtn.contains(e.target) && !taskFilterMenu.contains(e.target)) {
      taskFilterMenu.classList.add("hidden");
    }
    if (taskItemContextMenu && !taskItemContextMenu.contains(e.target)) {
      taskItemContextMenu.classList.add("hidden");
    }
  });

  ctxPinBtn.addEventListener("click", () => {
    const s = sessions.find((s) => s.id === contextTargetChatId);
    if (s) {
      s.pinned = !s.pinned;
      saveSessions();
      renderSidebar();
      showToast(s.pinned ? "Chat pinned 📌" : "Chat unpinned");
    }
    chatContextMenu.classList.add("hidden");
  });

  ctxRenameBtn.addEventListener("click", () => {
    renameConversation(contextTargetChatId);
    chatContextMenu.classList.add("hidden");
  });

  ctxArchiveBtn.addEventListener("click", () => {
    const s = sessions.find((s) => s.id === contextTargetChatId);
    if (s) {
      s.archived = !s.archived;
      saveSessions();
      renderSidebar();
      showToast(s.archived ? "Chat archived 📦" : "Chat unarchived");
    }
    chatContextMenu.classList.add("hidden");
  });

  ctxDeleteBtn.addEventListener("click", () => {
    deleteChat(contextTargetChatId);
    chatContextMenu.classList.add("hidden");
  });

  function renameConversation(chatId) {
    const s = sessions.find((s) => s.id === chatId);
    if (!s) return;
    const newTitle = prompt("Enter new title for this chat:", s.title);
    if (newTitle && newTitle.trim()) {
      s.title = newTitle.trim();
      saveSessions();
      renderSidebar();
      showToast("Chat renamed ✏️");
    }
  }

  function deleteChat(chatId) {
    const chatIndex = sessions.findIndex((s) => s.id === chatId);
    if (chatIndex === -1) return;

    const chatTitle = sessions[chatIndex].title;
    sessions.splice(chatIndex, 1);

    if (activeChatId === chatId) {
      activeChatId = sessions.length > 0 ? sessions[0].id : null;
    }

    saveSessions();
    renderSidebar();
    loadActiveChat();
    showToast(`Deleted "${chatTitle}" 🗑️`);
  }

  // Header Dropdown Actions
  if (headerRenameBtn) {
    headerRenameBtn.addEventListener("click", () => {
      if (activeChatId) renameConversation(activeChatId);
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerPinBtn) {
    headerPinBtn.addEventListener("click", () => {
      const s = getActiveSession();
      if (s) {
        s.pinned = !s.pinned;
        saveSessions();
        renderSidebar();
        showToast(s.pinned ? "Chat pinned 📌" : "Chat unpinned");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerArchiveBtn) {
    headerArchiveBtn.addEventListener("click", () => {
      const s = getActiveSession();
      if (s) {
        s.archived = !s.archived;
        saveSessions();
        renderSidebar();
        showToast(s.archived ? "Chat archived 📦" : "Chat unarchived");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerViewFilesBtn) {
    headerViewFilesBtn.addEventListener("click", () => {
      const s = getActiveSession();
      const files = s ? s.messages.filter((m) => m.fileName).map((m) => m.fileName) : [];
      if (files.length > 0) {
        alert("Files attached in this chat:\n• " + files.join("\n• "));
      } else {
        showToast("No files uploaded in this chat yet.");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerClearBtn) {
    headerClearBtn.addEventListener("click", () => {
      const s = getActiveSession();
      if (s) {
        s.messages = [];
        saveSessions();
        loadActiveChat();
        fetch("/api/clear", { method: "POST" }).catch(() => {});
        showToast("Conversation cleared 🗑️");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerDeleteBtn) {
    headerDeleteBtn.addEventListener("click", () => {
      if (activeChatId) deleteChat(activeChatId);
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerMenuBtn) {
    headerMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      headerDropdownMenu.classList.toggle("hidden");
    });
  }

  // Share Actions
  if (shareBtn) {
    shareBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      shareDropdownMenu.classList.toggle("hidden");
    });
  }

  if (shareCopyTranscriptBtn) {
    shareCopyTranscriptBtn.addEventListener("click", () => {
      const session = getActiveSession();
      if (!session || session.messages.length === 0) {
        showToast("No conversation to share yet.");
        shareDropdownMenu.classList.add("hidden");
        return;
      }
      let transcript = `=== Cloud AI Chatbot: ${session.title} ===\n\n`;
      session.messages.forEach((m) => {
        const sender = m.role === "user" ? "User" : "AI";
        const fileInfo = m.fileName ? ` [Attached: ${m.fileName}]` : "";
        transcript += `[${sender}${fileInfo}]:\n${m.text}\n\n`;
      });
      navigator.clipboard.writeText(transcript.trim()).then(() => {
        showToast("Conversation copied to clipboard! 📋");
      }).catch(() => showToast("Could not copy transcript."));
      shareDropdownMenu.classList.add("hidden");
    });
  }

  if (shareCopyLinkBtn) {
    shareCopyLinkBtn.addEventListener("click", () => {
      const shareUrl = `${window.location.origin}${window.location.pathname}#chat=${encodeURIComponent(activeChatId || "")}`;
      navigator.clipboard.writeText(shareUrl).then(() => {
        showToast("Share link copied to clipboard! 🔗");
      }).catch(() => showToast("Could not copy link."));
      shareDropdownMenu.classList.add("hidden");
    });
  }

  // ---------------------------------------------------------------------------
  // Interactive 6 Welcome Prompt Cards
  // ---------------------------------------------------------------------------
  document.querySelectorAll(".example-card").forEach((card) => {
    card.addEventListener("click", () => {
      const action = card.getAttribute("data-action");
      const prompt = card.getAttribute("data-prompt");

      if (action === "upload") {
        fileInput.click();
      } else if (action === "summarize") {
        fileInput.click();
        if (prompt) {
          messageInput.value = prompt;
          adjustTextareaHeight();
        }
      } else if (action === "image") {
        setComposerMode("image");
        if (prompt) {
          messageInput.value = prompt;
          adjustTextareaHeight();
        }
      } else if (action === "video") {
        setComposerMode("video");
        if (prompt) {
          messageInput.value = prompt;
          adjustTextareaHeight();
        }
      } else if (prompt) {
        messageInput.value = prompt;
        adjustTextareaHeight();
        messageInput.focus();
      }
    });
  });

  // ---------------------------------------------------------------------------
  // Drag and Drop File Upload
  // ---------------------------------------------------------------------------
  function hideDropzone() {
    if (dropzoneOverlay) {
      dropzoneOverlay.classList.add("hidden");
      dropzoneOverlay.style.display = "none";
    }
  }

  function showDropzone() {
    if (dropzoneOverlay) {
      dropzoneOverlay.classList.remove("hidden");
      dropzoneOverlay.style.display = "flex";
    }
  }

  hideDropzone();

  if (closeDropzoneBtn) {
    closeDropzoneBtn.addEventListener("click", hideDropzone);
  }

  if (dropzoneOverlay) {
    dropzoneOverlay.addEventListener("click", (e) => {
      if (e.target === dropzoneOverlay || e.target.closest("#closeDropzoneBtn")) {
        hideDropzone();
      }
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      hideDropzone();
    }
  });

  let dragCounter = 0;
  window.addEventListener("dragenter", (e) => {
    if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes("Files")) {
      e.preventDefault();
      dragCounter++;
      showDropzone();
    }
  });

  window.addEventListener("dragover", (e) => {
    if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes("Files")) {
      e.preventDefault();
    }
  });

  window.addEventListener("dragleave", (e) => {
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      hideDropzone();
    }
  });

  window.addEventListener("drop", (e) => {
    e.preventDefault();
    dragCounter = 0;
    hideDropzone();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file) return;

    const maxSizeBytes = 10 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      alert(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max allowed size is 10 MB.`);
      fileInput.value = "";
      return;
    }

    selectedFile = file;
    const ext = file.name.split(".").pop().toLowerCase();
    let icon = "📄";
    if (["png", "jpg", "jpeg", "webp"].includes(ext)) icon = "🖼️";
    else if (["txt"].includes(ext)) icon = "📝";
    else if (["docx"].includes(ext)) icon = "📃";

    filePreviewIcon.textContent = icon;
    filePreviewName.textContent = file.name;
    filePreviewSize.textContent = formatBytes(file.size);
    filePreview.classList.remove("hidden");
    messageInput.focus();
    showToast(`File attached: ${file.name} ✓`);
  }

  removeFileBtn.addEventListener("click", clearAttachment);

  function clearAttachment() {
    selectedFile = null;
    fileInput.value = "";
    filePreview.classList.add("hidden");
    if (fileUploadProgressBar) fileUploadProgressBar.classList.add("hidden");
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    const kb = bytes / 1024;
    if (kb < 1024) return kb.toFixed(1) + " KB";
    return (kb / 1024).toFixed(1) + " MB";
  }

  // ---------------------------------------------------------------------------
  // Message Composer & Auto-resize
  // ---------------------------------------------------------------------------
  function adjustTextareaHeight() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + "px";
  }

  messageInput.addEventListener("input", adjustTextareaHeight);

  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isSending) {
        composerForm.requestSubmit();
      }
    }
  });

  // Stop Generating Button Trigger
  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
        showToast("Generation stopped ⏹️");
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Dispatch: Submit Turn (Chat, Image, or Video)
  // ---------------------------------------------------------------------------
  composerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isSending) return;

    const text = messageInput.value.trim();
    if (!text && !selectedFile) return;

    if (composerMode === "image") {
      await handleImageGeneration(text);
    } else if (composerMode === "video") {
      await handleVideoGeneration(text);
    } else {
      await handleChatStreaming(text);
    }
  });

  function ensureActiveSession(userText, attachedName) {
    let session = getActiveSession();
    if (!session) {
      const newId = "chat_" + Date.now();
      session = {
        id: newId,
        title: "New chat",
        pinned: false,
        archived: false,
        createdAt: Date.now(),
        messages: [],
      };
      sessions.unshift(session);
      activeChatId = newId;
    }

    if (session.messages.length === 0 || session.title === "New chat") {
      let raw = userText || (attachedName ? `File: ${attachedName}` : "New chat");
      session.title = raw.slice(0, 32) + (raw.length > 32 ? "..." : "");
      renderSidebar();
    }
    return session;
  }

  // ---------------------------------------------------------------------------
  // 1. Streaming Chat Handler
  // ---------------------------------------------------------------------------
  async function handleChatStreaming(text) {
    emptyStateEl.style.display = "none";
    const attachedName = selectedFile ? selectedFile.name : null;
    const attachedObj = selectedFile;
    const session = ensureActiveSession(text, attachedName);

    const userDisplayText = text || "Please analyze the attached document.";
    const userTimestamp = Date.now();

    session.messages.push({
      role: "user",
      text: userDisplayText,
      fileName: attachedName,
      timestamp: userTimestamp,
    });
    saveSessions();

    appendUserMessageDOM(userDisplayText, attachedName, userTimestamp, session.messages.length - 1);

    // Prepare FormData
    const formData = new FormData();
    if (text) formData.append("message", text);
    if (attachedObj) formData.append("file", attachedObj);
    formData.append("model", selectedModel);
    formData.append("effort", selectedEffort);
    formData.append("web_search", isWebSearchEnabled ? "true" : "false");

    const rolling = session.messages.slice(0, -1).map((m) => ({
      role: m.role === "user" ? "user" : "model",
      text: m.text,
    }));
    formData.append("history", JSON.stringify(rolling.slice(-20)));

    messageInput.value = "";
    messageInput.style.height = "auto";
    clearAttachment();

    setSendingState(true);
    currentAbortController = new AbortController();

    const indicatorText = attachedObj
      ? "Analyzing attached file with Gemini..."
      : (isWebSearchEnabled ? "Searching web and synthesizing response..." : "AI is thinking...");
    const typingIndicator = appendTypingIndicatorDOM(indicatorText);

    let accumulatedText = "";
    let aiBubbleEl = null;
    let aiRowEl = null;
    let aiWrapEl = null;
    let cursorSpan = null;

    try {
      let streamSucceeded = false;
      let streamError = null;

      try {
        const response = await fetch("/api/chat/stream", {
          method: "POST",
          body: formData,
          signal: currentAbortController.signal,
        });

        if (!response.ok) {
          let errDetail = null;
          try {
            const errJson = await response.json();
            if (errJson && errJson.error) {
              errDetail = errJson.error;
            }
          } catch (_) {}

          if (!errDetail) {
            if (response.status === 401) errDetail = "Authentication error: Invalid or missing OPENROUTER_API_KEY.";
            else if (response.status === 402) errDetail = "Credit limit reached (402). Your OpenRouter credit balance is low.";
            else if (response.status === 408 || response.status === 504) errDetail = "Request timed out. The server or AI provider took too long to respond.";
            else if (response.status === 429) errDetail = "Rate limit exceeded (429). Please wait a moment before sending another message.";
            else if (response.status >= 500) errDetail = `AI provider service error (${response.status}).`;
            else errDetail = `Server returned error (${response.status}).`;
          }
          throw new Error(errDetail);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop();

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const jsonStr = trimmed.replace(/^data:\s*/, "");

            let data;
            try {
              data = JSON.parse(jsonStr);
            } catch (jsonErr) {
              continue;
            }

            if (data.type === "chunk" && data.text) {
              if (typingIndicator && typingIndicator.parentElement) {
                typingIndicator.remove();
              }

              if (!aiBubbleEl) {
                const aiDOM = createStreamingAiMessageDOM(userDisplayText, attachedName);
                aiRowEl = aiDOM.row;
                aiBubbleEl = aiDOM.bubble;
                aiWrapEl = aiDOM.contentWrap;
                cursorSpan = aiDOM.cursor;
                messagesEl.appendChild(aiRowEl);
              }

              accumulatedText += data.text;
              const renderedHtml = renderMarkdown(accumulatedText);
              aiBubbleEl.innerHTML = `<div class="markdown-body">${renderedHtml}</div>`;
              aiBubbleEl.appendChild(cursorSpan);
              scrollToBottom(false, false);
            } else if (data.type === "done") {
              if (data.reply && !accumulatedText) {
                accumulatedText = data.reply;
              }
              streamSucceeded = true;
            } else if (data.type === "error") {
              streamError = data.error || "An error occurred during streaming.";
              break;
            }
          }

          if (streamError) {
            break;
          }
        }

        if (streamError) {
          throw new Error(streamError);
        }

      } catch (streamErr) {
        if (streamErr.name === "AbortError") {
          throw streamErr;
        }

        // If stream failed before any chunks were received, attempt automatic fallback to synchronous /api/chat
        if (!accumulatedText) {
          console.warn("SSE stream failed or unavailable, falling back to /api/chat...", streamErr);
          const syncRes = await fetch("/api/chat", {
            method: "POST",
            body: formData,
            signal: currentAbortController.signal,
          });

          const syncData = await syncRes.json();
          if (!syncRes.ok) {
            let msg = syncData.error;
            if (!msg) {
              if (syncRes.status === 401) msg = "Invalid or missing OPENROUTER_API_KEY.";
              else if (syncRes.status === 402) msg = "OpenRouter credit limit reached (402).";
              else if (syncRes.status === 429) msg = "AI rate limit exceeded (429). Please wait a moment.";
              else msg = `Server error (${syncRes.status}).`;
            }
            throw new Error(msg);
          }
          accumulatedText = syncData.reply || "";
        } else {
          throw streamErr;
        }
      }

      if (cursorSpan && cursorSpan.parentElement) cursorSpan.remove();
      if (typingIndicator && typingIndicator.parentElement) typingIndicator.remove();

      if (!accumulatedText) {
        accumulatedText = "⚠️ **Notice:** The AI server did not return a response. Please verify your OpenRouter configuration or try again.";
      }

      const aiTimestamp = Date.now();
      session.messages.push({
        role: "ai",
        text: accumulatedText,
        isError: false,
        timestamp: aiTimestamp,
      });
      saveSessions();

      if (aiBubbleEl) {
        aiBubbleEl.innerHTML = `<div class="markdown-body">${renderMarkdown(accumulatedText)}</div>`;
        attachCodeCopyButtons(aiBubbleEl);
        const actionsBar = createAiActionsBar(accumulatedText, userDisplayText, attachedName, aiRowEl, aiBubbleEl, session.messages.length - 1);
        aiWrapEl.appendChild(actionsBar);
      } else {
        appendAiMessageDOM(accumulatedText, false, userDisplayText, attachedName, session.messages.length - 1, aiTimestamp);
      }

      scrollToBottom(true, false);
    } catch (err) {
      if (typingIndicator && typingIndicator.parentElement) typingIndicator.remove();
      if (cursorSpan && cursorSpan.parentElement) cursorSpan.remove();
      if (aiRowEl && aiRowEl.parentElement) aiRowEl.remove();
      if (typingIndicator && typingIndicator.parentElement) typingIndicator.remove();
      if (cursorSpan && cursorSpan.parentElement) cursorSpan.remove();

      if (err.name === "AbortError") {
        if (accumulatedText) {
          session.messages.push({
            role: "ai",
            text: accumulatedText + " *(Generation stopped)*",
            isError: false,
            timestamp: Date.now(),
          });
          saveSessions();
          if (aiBubbleEl) {
            aiBubbleEl.innerHTML = `<div class="markdown-body">${renderMarkdown(accumulatedText + " *(Generation stopped)*")}</div>`;
            attachCodeCopyButtons(aiBubbleEl);
            const actionsBar = createAiActionsBar(accumulatedText, userDisplayText, attachedName, aiRowEl, aiBubbleEl, session.messages.length - 1);
            aiWrapEl.appendChild(actionsBar);
          }
        }
      } else {
        console.error("Chat error:", err);
        const errText = `⚠️ **Error:** ${err.message || "Failed to communicate with AI server."}`;
        session.messages.push({ role: "ai", text: errText, isError: true, timestamp: Date.now() });
        saveSessions();
        appendAiMessageDOM(errText, true, userDisplayText, attachedName, session.messages.length - 1);
        showToast("Error occurred during request ✕");
      }
    } finally {
      setSendingState(false);
      currentAbortController = null;
      messageInput.focus();
    }
  }

  // ---------------------------------------------------------------------------
  // 2. Image Generation Handler
  // ---------------------------------------------------------------------------
  async function handleImageGeneration(prompt) {
    emptyStateEl.style.display = "none";
    const session = ensureActiveSession(prompt, null);
    const userTimestamp = Date.now();

    session.messages.push({
      role: "user",
      text: `🖼️ Generate Image: "${prompt}"`,
      timestamp: userTimestamp,
    });
    saveSessions();

    appendUserMessageDOM(`🖼️ Generate Image: "${prompt}"`, null, userTimestamp, session.messages.length - 1);

    messageInput.value = "";
    messageInput.style.height = "auto";
    setComposerMode("chat");

    setSendingState(true);
    const loadingCard = appendMediaLoadingDOM("🎨 Synthesizing AI image from prompt...", "Generating pixels...");

    try {
      const res = await fetch("/api/generate-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();
      loadingCard.remove();

      if (!res.ok) {
        throw new Error(data.error || "Failed to generate image.");
      }

      const aiTimestamp = Date.now();
      session.messages.push({
        role: "ai",
        type: "image",
        imageUrl: data.image_url,
        text: prompt,
        timestamp: aiTimestamp,
      });
      saveSessions();

      appendImageMessageDOM(data.image_url, prompt, prompt, aiTimestamp, session.messages.length - 1);
      showToast("Image generated successfully! 🖼️");
    } catch (err) {
      loadingCard.remove();
      const errText = `⚠️ **Image Generation Error:** ${err.message}`;
      session.messages.push({ role: "ai", text: errText, isError: true, timestamp: Date.now() });
      saveSessions();
      appendAiMessageDOM(errText, true, prompt, null, session.messages.length - 1);
      showToast("Error generating image ✕");
    } finally {
      setSendingState(false);
      messageInput.focus();
    }
  }

  // ---------------------------------------------------------------------------
  // 3. Asynchronous Video Generation Handler
  // ---------------------------------------------------------------------------
  async function handleVideoGeneration(prompt) {
    emptyStateEl.style.display = "none";
    const session = ensureActiveSession(prompt, null);
    const userTimestamp = Date.now();

    session.messages.push({
      role: "user",
      text: `🎬 Generate Video: "${prompt}"`,
      timestamp: userTimestamp,
    });
    saveSessions();

    appendUserMessageDOM(`🎬 Generate Video: "${prompt}"`, null, userTimestamp, session.messages.length - 1);

    messageInput.value = "";
    messageInput.style.height = "auto";
    setComposerMode("chat");

    setSendingState(true);
    const progressDOM = appendVideoProgressCardDOM("Initiating cinematic video task...");

    try {
      const res = await fetch("/api/generate-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not initiate video task.");

      const jobId = data.job_id;

      const pollInterval = setInterval(async () => {
        try {
          const pollRes = await fetch(`/api/video/status/${jobId}`);
          if (!pollRes.ok) return;

          const jobData = await pollRes.json();
          progressDOM.update(jobData.progress || 10, jobData.step_description || "Rendering motion frames...");

          if (jobData.status === "completed" && jobData.video_url) {
            clearInterval(pollInterval);
            progressDOM.card.remove();

            const aiTimestamp = Date.now();
            session.messages.push({
              role: "ai",
              type: "video",
              videoUrl: jobData.video_url,
              text: prompt,
              timestamp: aiTimestamp,
            });
            saveSessions();

            appendVideoMessageDOM(jobData.video_url, prompt, prompt, aiTimestamp, session.messages.length - 1);
            setSendingState(false);
            showToast("Video generated successfully! 🎬");
          } else if (jobData.status === "failed") {
            clearInterval(pollInterval);
            progressDOM.card.remove();
            throw new Error(jobData.error || "Video processing failed.");
          }
        } catch (pollErr) {
          console.error("Video poll error:", pollErr);
        }
      }, 1500);

    } catch (err) {
      progressDOM.card.remove();
      const errText = `⚠️ **Video Generation Error:** ${err.message}`;
      session.messages.push({ role: "ai", text: errText, isError: true, timestamp: Date.now() });
      saveSessions();
      appendAiMessageDOM(errText, true, prompt, null, session.messages.length - 1);
      setSendingState(false);
      showToast("Error generating video ✕");
    }
  }

  // ---------------------------------------------------------------------------
  // DOM: User Message Bubble with Inline Edit
  // ---------------------------------------------------------------------------
  function appendUserMessageDOM(text, fileName, timestamp = Date.now(), msgIndex = -1) {
    const row = document.createElement("div");
    row.className = "msg-row user";
    row.dataset.index = msgIndex;

    let fileChip = "";
    if (fileName) {
      fileChip = `<div class="msg-file-chip">📎 ${escapeHtml(fileName)}</div><br/>`;
    }

    row.innerHTML = `
      <button class="btn-msg-edit" title="Edit message and resend">✏️</button>
      <div class="avatar user">🧑</div>
      <div class="msg-bubble">
        ${fileChip}<span class="user-text-content">${escapeHtml(text)}</span>
        <span class="msg-timestamp">${formatTime(timestamp)}</span>
      </div>
    `;

    const editBtn = row.querySelector(".btn-msg-edit");
    if (editBtn) {
      editBtn.addEventListener("click", () => {
        openInlineUserEdit(row, text, msgIndex);
      });
    }

    messagesEl.appendChild(row);
    scrollToBottom(true, false);
  }

  function openInlineUserEdit(rowEl, originalText, msgIndex) {
    const bubbleEl = rowEl.querySelector(".msg-bubble");
    if (!bubbleEl || bubbleEl.querySelector(".msg-edit-wrap")) return;

    const originalHTML = bubbleEl.innerHTML;

    bubbleEl.innerHTML = `
      <div class="msg-edit-wrap">
        <textarea class="msg-edit-textarea">${escapeHtml(originalText)}</textarea>
        <div class="msg-edit-actions">
          <button type="button" class="btn-edit-cancel">Cancel</button>
          <button type="button" class="btn-edit-save">Save & Resend</button>
        </div>
      </div>
    `;

    const textarea = bubbleEl.querySelector(".msg-edit-textarea");
    textarea.focus();
    textarea.selectionStart = textarea.value.length;

    const cancelBtn = bubbleEl.querySelector(".btn-edit-cancel");
    cancelBtn.addEventListener("click", () => {
      bubbleEl.innerHTML = originalHTML;
      const reattachBtn = rowEl.querySelector(".btn-msg-edit");
      if (reattachBtn) reattachBtn.addEventListener("click", () => openInlineUserEdit(rowEl, originalText, msgIndex));
    });

    const saveBtn = bubbleEl.querySelector(".btn-edit-save");
    saveBtn.addEventListener("click", () => {
      const newText = textarea.value.trim();
      if (!newText) return;

      const session = getActiveSession();
      if (session && msgIndex >= 0) {
        session.messages = session.messages.slice(0, msgIndex);
        saveSessions();
        loadActiveChat();
        messageInput.value = newText;
        showToast("Message updated & regenerating... 🔄");
        composerForm.requestSubmit();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // DOM: AI Streaming Placeholder & Message Bubble
  // ---------------------------------------------------------------------------
  function createStreamingAiMessageDOM(promptText, attachedFileName) {
    const row = document.createElement("div");
    row.className = "msg-row ai";

    const contentWrap = document.createElement("div");
    contentWrap.className = "msg-content-wrap";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";

    const cursor = document.createElement("span");
    cursor.className = "typing-cursor";

    contentWrap.appendChild(bubble);
    row.innerHTML = `<div class="avatar ai">✦</div>`;
    row.appendChild(contentWrap);

    return { row, bubble, contentWrap, cursor };
  }

  function appendAiMessageDOM(markdownContent, isError = false, promptText = "", attachedFileName = null, msgIndex = -1, timestamp = Date.now()) {
    const row = document.createElement("div");
    row.className = `msg-row ai ${isError ? "error" : ""}`;

    const contentWrap = document.createElement("div");
    contentWrap.className = "msg-content-wrap";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";

    if (isError) {
      bubble.innerHTML = `
        <div class="markdown-body" style="color: #ef4444;">${renderMarkdown(markdownContent)}</div>
        <span class="msg-timestamp">${formatTime(timestamp)}</span>
      `;
    } else {
      bubble.innerHTML = `
        <div class="markdown-body">${renderMarkdown(markdownContent)}</div>
        <span class="msg-timestamp">${formatTime(timestamp)}</span>
      `;
      attachCodeCopyButtons(bubble);
    }

    contentWrap.appendChild(bubble);

    if (!isError) {
      const actionsBar = createAiActionsBar(markdownContent, promptText, attachedFileName, row, bubble, msgIndex);
      contentWrap.appendChild(actionsBar);
    }

    row.innerHTML = `<div class="avatar ai">✦</div>`;
    row.appendChild(contentWrap);

    messagesEl.appendChild(row);
    scrollToBottom(true, false);
  }

  // ---------------------------------------------------------------------------
  // DOM: Image & Video Media Cards
  // ---------------------------------------------------------------------------
  function appendImageMessageDOM(imageUrl, caption, originalPrompt, timestamp = Date.now(), msgIndex = -1) {
    const row = document.createElement("div");
    row.className = "msg-row ai";

    const contentWrap = document.createElement("div");
    contentWrap.className = "msg-content-wrap";

    const card = document.createElement("div");
    card.className = "generated-image-card";
    card.innerHTML = `
      <div class="image-preview-wrapper">
        <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(caption)}" loading="lazy" />
      </div>
      <div class="image-card-footer">
        <span class="image-prompt-caption" title="${escapeHtml(caption)}">"${escapeHtml(caption)}"</span>
        <div class="media-actions">
          <a href="${escapeHtml(imageUrl)}" download="ai-image.jpg" class="btn-media-action" title="Download image">
            ⬇️ Download
          </a>
          <button type="button" class="btn-media-action btn-regen-image" title="Regenerate this image">
            🔄 Regenerate
          </button>
        </div>
      </div>
    `;

    const regenBtn = card.querySelector(".btn-regen-image");
    regenBtn.addEventListener("click", () => {
      setComposerMode("image");
      messageInput.value = originalPrompt;
      composerForm.requestSubmit();
    });

    contentWrap.appendChild(card);
    contentWrap.insertAdjacentHTML("beforeend", `<span class="msg-timestamp">${formatTime(timestamp)}</span>`);

    row.innerHTML = `<div class="avatar ai">✦</div>`;
    row.appendChild(contentWrap);

    messagesEl.appendChild(row);
    scrollToBottom(true, false);
  }

  function appendVideoMessageDOM(videoUrl, caption, originalPrompt, timestamp = Date.now(), msgIndex = -1) {
    const row = document.createElement("div");
    row.className = "msg-row ai";

    const contentWrap = document.createElement("div");
    contentWrap.className = "msg-content-wrap";

    const card = document.createElement("div");
    card.className = "generated-video-card";
    card.innerHTML = `
      <div class="video-player-wrapper">
        <video controls autoplay loop muted playsinline src="${escapeHtml(videoUrl)}"></video>
      </div>
      <div class="image-card-footer">
        <span class="image-prompt-caption" title="${escapeHtml(caption)}">"${escapeHtml(caption)}"</span>
        <div class="media-actions">
          <a href="${escapeHtml(videoUrl)}" download="ai-video.mp4" class="btn-media-action" title="Download video">
            ⬇️ Download
          </a>
          <button type="button" class="btn-media-action btn-regen-video" title="Regenerate this video">
            🔄 Regenerate
          </button>
        </div>
      </div>
    `;

    const regenBtn = card.querySelector(".btn-regen-video");
    regenBtn.addEventListener("click", () => {
      setComposerMode("video");
      messageInput.value = originalPrompt;
      composerForm.requestSubmit();
    });

    contentWrap.appendChild(card);
    contentWrap.insertAdjacentHTML("beforeend", `<span class="msg-timestamp">${formatTime(timestamp)}</span>`);

    row.innerHTML = `<div class="avatar ai">✦</div>`;
    row.appendChild(contentWrap);

    messagesEl.appendChild(row);
    scrollToBottom(true, false);
  }

  function appendMediaLoadingDOM(title, subtitle) {
    const row = document.createElement("div");
    row.className = "msg-row ai";
    row.innerHTML = `
      <div class="avatar ai">✦</div>
      <div class="msg-bubble">
        <div style="display:flex; align-items:center; gap:10px;">
          <div class="typing-dots"><span></span><span></span><span></span></div>
          <span><strong>${escapeHtml(title)}</strong> <span style="font-size:12px; color:var(--text-muted);">${escapeHtml(subtitle)}</span></span>
        </div>
      </div>
    `;
    messagesEl.appendChild(row);
    scrollToBottom(true, false);
    return row;
  }

  function appendVideoProgressCardDOM(initialStep) {
    const row = document.createElement("div");
    row.className = "msg-row ai";

    const card = document.createElement("div");
    card.className = "video-progress-card";
    card.innerHTML = `
      <div class="video-progress-header">
        <span>🎬 Rendering Video</span>
        <span class="video-pct">10%</span>
      </div>
      <div class="video-progress-track">
        <div class="video-progress-indicator" style="width: 10%;"></div>
      </div>
      <div class="video-step-desc">${escapeHtml(initialStep)}</div>
    `;

    row.innerHTML = `<div class="avatar ai">✦</div>`;
    row.appendChild(card);
    messagesEl.appendChild(row);
    scrollToBottom(true, false);

    const pctEl = card.querySelector(".video-pct");
    const indEl = card.querySelector(".video-progress-indicator");
    const descEl = card.querySelector(".video-step-desc");

    return {
      card: row,
      update: (pct, desc) => {
        pctEl.textContent = `${pct}%`;
        indEl.style.width = `${pct}%`;
        if (desc) descEl.textContent = desc;
      },
    };
  }

  // ---------------------------------------------------------------------------
  // Action Buttons Factory: 🔊 Read Aloud, 📋 Copy, 🔄 Try Again
  // ---------------------------------------------------------------------------
  function createAiActionsBar(aiText, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex) {
    const bar = document.createElement("div");
    bar.className = "ai-actions-bar";

    const readBtn = document.createElement("button");
    readBtn.className = "btn-ai-action btn-ai-read";
    readBtn.title = "Read response aloud";
    readBtn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
      </svg>
      <span>Read Aloud</span>
    `;
    readBtn.addEventListener("click", () => toggleSpeech(readBtn, aiText));

    const copyBtn = document.createElement("button");
    copyBtn.className = "btn-ai-action btn-ai-copy";
    copyBtn.title = "Copy clean response";
    copyBtn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      <span>Copy</span>
    `;
    copyBtn.addEventListener("click", () => copyCleanAiText(copyBtn, aiText, bubbleEl));

    const retryBtn = document.createElement("button");
    retryBtn.className = "btn-ai-action btn-ai-retry";
    retryBtn.title = "Regenerate answer with the same prompt";
    retryBtn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"></polyline>
        <polyline points="1 20 1 14 7 14"></polyline>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
      </svg>
      <span>Try Again</span>
    `;
    retryBtn.addEventListener("click", () => {
      regenerateAiResponse(retryBtn, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex);
    });

    bar.appendChild(readBtn);
    bar.appendChild(copyBtn);
    bar.appendChild(retryBtn);

    return bar;
  }

  // ---------------------------------------------------------------------------
  // 🔊 Text-To-Speech (Read Aloud ↔ Stop Reading)
  // ---------------------------------------------------------------------------
  function toggleSpeech(btn, rawContent) {
    if (!("speechSynthesis" in window)) {
      showToast("Speech synthesis is not supported in this browser.");
      return;
    }

    if (activeSpeechBtn === btn) {
      stopSpeech();
      return;
    }

    stopSpeech();

    const cleanSpeechText = sanitizeMarkdownForSpeech(rawContent);
    if (!cleanSpeechText.trim()) {
      showToast("No readable text found in response.");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanSpeechText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      activeSpeechUtterance = utterance;
      activeSpeechBtn = btn;
      btn.classList.add("speaking");
      btn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"></rect></svg>
        <span>Stop Reading</span>
      `;
    };

    utterance.onend = () => {
      resetSpeechBtn(btn);
      activeSpeechUtterance = null;
      activeSpeechBtn = null;
    };

    utterance.onerror = () => {
      resetSpeechBtn(btn);
      activeSpeechUtterance = null;
      activeSpeechBtn = null;
    };

    window.speechSynthesis.speak(utterance);
  }

  function stopSpeech() {
    if ("speechSynthesis" in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    if (activeSpeechBtn) {
      resetSpeechBtn(activeSpeechBtn);
      activeSpeechBtn = null;
    }
    activeSpeechUtterance = null;
  }

  function resetSpeechBtn(btn) {
    if (!btn) return;
    btn.classList.remove("speaking");
    btn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
      </svg>
      <span>Read Aloud</span>
    `;
  }

  function sanitizeMarkdownForSpeech(md) {
    if (!md) return "";
    return md
      .replace(/```[\s\S]*?```/g, " [Code snippet omitted] ")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
      .replace(/[#*_~>]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  // ---------------------------------------------------------------------------
  // 📋 Copy Clean AI Text
  // ---------------------------------------------------------------------------
  function copyCleanAiText(btn, rawText, bubbleEl) {
    let textToCopy = rawText;
    if (bubbleEl) {
      const clone = bubbleEl.cloneNode(true);
      clone.querySelectorAll(".code-header, .msg-timestamp").forEach((el) => el.remove());
      textToCopy = clone.innerText.trim();
    }
    if (!textToCopy) textToCopy = rawText || "";

    navigator.clipboard.writeText(textToCopy).then(() => {
      btn.classList.add("copied");
      btn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>Copied</span>
      `;
      showToast("Response copied to clipboard! 📋");

      setTimeout(() => {
        btn.classList.remove("copied");
        btn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>Copy</span>
        `;
      }, 2000);
    }).catch(() => showToast("Failed to copy response."));
  }

  // ---------------------------------------------------------------------------
  // 🔄 Try Again: Regenerate Response
  // ---------------------------------------------------------------------------
  async function regenerateAiResponse(retryBtn, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex) {
    if (isSending) return;
    const session = getActiveSession();
    if (!session) return;

    if (!promptText) {
      for (let i = (msgIndex >= 0 ? msgIndex - 1 : session.messages.length - 1); i >= 0; i--) {
        if (session.messages[i].role === "user") {
          promptText = session.messages[i].text;
          attachedFileName = session.messages[i].fileName;
          break;
        }
      }
    }

    if (!promptText && !attachedFileName) {
      showToast("Cannot determine prompt for regeneration.");
      return;
    }

    setSendingState(true);
    retryBtn.classList.add("loading");
    retryBtn.innerHTML = `<span>Regenerating...</span>`;

    const typingIndicator = appendTypingIndicatorDOM("Regenerating answer...");

    const formData = new FormData();
    formData.append("message", promptText);
    formData.append("model", selectedModel);
    formData.append("effort", selectedEffort);
    if (attachedFileName) {
      formData.append("attached_file_name", attachedFileName);
    }

    const targetIdx = msgIndex >= 0 ? msgIndex : session.messages.length - 1;
    const historyTurns = session.messages.slice(0, targetIdx).map((m) => ({
      role: m.role === "user" ? "user" : "model",
      text: m.text,
    }));
    formData.append("history", JSON.stringify(historyTurns.slice(-20)));

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      typingIndicator.remove();

      if (!response.ok) {
        const errorMsg = data.error || `Server error (${response.status}).`;
        const formattedErr = `⚠️ **Error:** ${errorMsg}`;
        bubbleEl.innerHTML = `<div class="markdown-body" style="color: #ef4444;">${renderMarkdown(formattedErr)}</div>`;
        if (msgIndex >= 0 && session.messages[msgIndex]) {
          session.messages[msgIndex].text = formattedErr;
          session.messages[msgIndex].isError = true;
          saveSessions();
        }
        showToast("Regeneration error ✕");
      } else {
        const newReply = data.reply || "No response received.";
        bubbleEl.innerHTML = `
          <div class="markdown-body">${renderMarkdown(newReply)}</div>
          <span class="msg-timestamp">${formatTime(Date.now())}</span>
        `;
        attachCodeCopyButtons(bubbleEl);

        if (msgIndex >= 0 && session.messages[msgIndex]) {
          session.messages[msgIndex].text = newReply;
          session.messages[msgIndex].isError = false;
          saveSessions();
        }

        const parentWrap = bubbleEl.parentElement;
        const oldBar = parentWrap.querySelector(".ai-actions-bar");
        if (oldBar) oldBar.remove();
        const newBar = createAiActionsBar(newReply, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex);
        parentWrap.appendChild(newBar);

        showToast("Response regenerated! 🔄");
      }
    } catch (err) {
      typingIndicator.remove();
      showToast("Network error while regenerating.");
    } finally {
      retryBtn.classList.remove("loading");
      retryBtn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"></polyline>
          <polyline points="1 20 1 14 7 14"></polyline>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
        </svg>
        <span>Try Again</span>
      `;
      setSendingState(false);
      messageInput.focus();
    }
  }

  // ---------------------------------------------------------------------------
  // Typing Indicator DOM
  // ---------------------------------------------------------------------------
  function appendTypingIndicatorDOM(text = "AI is thinking...") {
    const row = document.createElement("div");
    row.className = "msg-row ai";
    row.innerHTML = `
      <div class="avatar ai">✦</div>
      <div class="msg-bubble">
        <div style="display:flex; align-items:center; gap:8px;">
          <div class="typing-dots"><span></span><span></span><span></span></div>
          <span style="font-size:12.5px; color:var(--text-muted);">${escapeHtml(text)}</span>
        </div>
      </div>
    `;
    messagesEl.appendChild(row);
    scrollToBottom(true, false);
    return row;
  }

  // ---------------------------------------------------------------------------
  // Markdown Rendering & Code Block Copy
  // ---------------------------------------------------------------------------
  function renderMarkdown(content) {
    if (!content) return "";
    if (window.marked) {
      try {
        return marked.parse(content);
      } catch (e) {
        console.error("Markdown parse error:", e);
      }
    }
    return escapeHtml(content);
  }

  function renderMathInContainer(container) {
    if (!container) return;
    if (window.renderMathInElement) {
      try {
        window.renderMathInElement(container, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "\\[", right: "\\]", display: true },
            { left: "\\(", right: "\\)", display: false },
            { left: "$", right: "$", display: false }
          ],
          throwOnError: false,
          ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"]
        });
      } catch (err) {
        console.warn("KaTeX render error:", err);
      }
    }
  }

  function attachCodeCopyButtons(container) {
    if (!container) return;
    
    // Render LaTeX / Mathematical formulas in container
    renderMathInContainer(container);

    const preBlocks = container.querySelectorAll("pre");
    preBlocks.forEach((pre) => {
      if (pre.querySelector(".code-header")) return;
      const code = pre.querySelector("code");
      if (!code) return;

      const header = document.createElement("div");
      header.className = "code-header";
      header.innerHTML = `
        <span>Code</span>
        <button type="button" class="btn-copy-code" title="Copy code">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>Copy</span>
        </button>
      `;

      const copyBtn = header.querySelector(".btn-copy-code");
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(code.innerText).then(() => {
          copyBtn.innerHTML = `<span>Copied!</span>`;
          setTimeout(() => {
            copyBtn.innerHTML = `
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            `;
          }, 2000);
        });
      });

      pre.insertBefore(header, code);
    });
  }

  // ---------------------------------------------------------------------------
  // Mobile Sidebar Drawer
  // ---------------------------------------------------------------------------
  if (mobileSidebarToggle) {
    mobileSidebarToggle.addEventListener("click", () => {
      sidebar.classList.add("open");
      sidebarOverlay.classList.add("active");
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeMobileSidebar);
  }

  function closeMobileSidebar() {
    if (sidebar) sidebar.classList.remove("open");
    if (sidebarOverlay) sidebarOverlay.classList.remove("active");
  }

  // ---------------------------------------------------------------------------
  // Sending / Generating State & Stop Button Toggle
  // ---------------------------------------------------------------------------
  function setSendingState(state) {
    isSending = state;
    if (sendBtn) sendBtn.disabled = state;

    if (state) {
      if (sendBtn) sendBtn.classList.add("hidden");
      if (stopBtn) stopBtn.classList.remove("hidden");
      document.querySelectorAll(".btn-ai-retry").forEach((b) => (b.disabled = true));
    } else {
      if (sendBtn) sendBtn.classList.remove("hidden");
      if (stopBtn) stopBtn.classList.add("hidden");
      document.querySelectorAll(".btn-ai-retry").forEach((b) => (b.disabled = false));
    }
  }

  // ---------------------------------------------------------------------------
  // Toast Notifications
  // ---------------------------------------------------------------------------
  let toastTimer = null;
  function showToast(msg) {
    if (!toastNotification) return;
    clearTimeout(toastTimer);
    toastNotification.textContent = msg;
    toastNotification.classList.remove("hidden");
    toastTimer = setTimeout(() => {
      toastNotification.classList.add("hidden");
    }, 2800);
  }

  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ===========================================================================
  // SCHEDULED TASKS CONTROLLER & LOGIC
  // ===========================================================================

  const scheduledTasksGrid = document.getElementById("scheduledTasksGrid");
  const scheduledEmptyState = document.getElementById("scheduledEmptyState");
  const tasksCountBadge = document.getElementById("tasksCountBadge");
  const taskFilterBtn = document.getElementById("taskFilterBtn");
  const taskFilterMenu = document.getElementById("taskFilterMenu");
  const currentFilterLabel = document.getElementById("currentFilterLabel");

  const scheduleInput = document.getElementById("scheduleInput");
  const schedulePlusBtn = document.getElementById("schedulePlusBtn");
  const scheduleMicBtn = document.getElementById("scheduleMicBtn");
  const scheduleSubmitBtn = document.getElementById("scheduleSubmitBtn");
  const emptyCreateTaskBtn = document.getElementById("emptyCreateTaskBtn");

  const recommendedToggleBtn = document.getElementById("recommendedToggleBtn");
  const recommendedChevron = document.getElementById("recommendedChevron");
  const recommendedCardsGrid = document.getElementById("recommendedCardsGrid");

  // Modals
  const taskConfirmModal = document.getElementById("taskConfirmModal");
  const confirmModalTitle = document.getElementById("confirmModalTitle");
  const closeConfirmModalBtn = document.getElementById("closeConfirmModalBtn");
  const modalCancelBtn = document.getElementById("modalCancelBtn");
  const taskConfigForm = document.getElementById("taskConfigForm");
  const modalTaskId = document.getElementById("modalTaskId");
  const modalTaskTitle = document.getElementById("modalTaskTitle");
  const modalTaskPrompt = document.getElementById("modalTaskPrompt");
  const modalTaskType = document.getElementById("modalTaskType");
  const modalTaskRecurrence = document.getElementById("modalTaskRecurrence");
  const modalTaskTime = document.getElementById("modalTaskTime");
  const modalTaskTimezone = document.getElementById("modalTaskTimezone");
  const modalDateGroup = document.getElementById("modalDateGroup");
  const modalTaskDate = document.getElementById("modalTaskDate");
  const modalDaysGroup = document.getElementById("modalDaysGroup");
  const modalSaveTaskBtn = document.getElementById("modalSaveTaskBtn");

  const taskHistoryModal = document.getElementById("taskHistoryModal");
  const historyModalTitle = document.getElementById("historyModalTitle");
  const historyModalSchedule = document.getElementById("historyModalSchedule");
  const historyModalIcon = document.getElementById("historyModalIcon");
  const closeHistoryModalBtn = document.getElementById("closeHistoryModalBtn");
  const historyRunNowBtn = document.getElementById("historyRunNowBtn");
  const historyEntriesList = document.getElementById("historyEntriesList");

  const taskItemContextMenu = document.getElementById("taskItemContextMenu");
  const ctxTaskRunNow = document.getElementById("ctxTaskRunNow");
  const ctxTaskHistory = document.getElementById("ctxTaskHistory");
  const ctxTaskEdit = document.getElementById("ctxTaskEdit");
  const ctxTaskPauseResume = document.getElementById("ctxTaskPauseResume");
  const ctxTaskDelete = document.getElementById("ctxTaskDelete");

  let currentTaskFilter = "active";
  let loadedTasks = [];
  let contextTargetTaskId = null;
  let activeHistoryTask = null;

  // Set user timezone in modal
  const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  if (modalTaskTimezone) modalTaskTimezone.value = userTz;

  // Task Type Icon Map
  const TASK_ICONS = {
    reminder: "⏰",
    briefing: "📰",
    web_monitor: "🔎",
    report: "📊",
    study: "📚",
    price_monitor: "💰",
    website_monitor: "🌐",
  };

  // Status Filter Dropdown Toggle
  if (taskFilterBtn) {
    taskFilterBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      taskFilterMenu.classList.toggle("hidden");
    });
  }

  if (taskFilterMenu) {
    taskFilterMenu.querySelectorAll(".filter-option").forEach((btn) => {
      btn.addEventListener("click", () => {
        taskFilterMenu.querySelectorAll(".filter-option").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        currentTaskFilter = btn.dataset.filter;
        currentFilterLabel.textContent = btn.textContent;
        taskFilterMenu.classList.add("hidden");
        loadScheduledTasks();
      });
    });
  }

  // Recommended Tasks Accordion Toggle
  let isRecOpen = true;
  if (recommendedToggleBtn) {
    recommendedToggleBtn.addEventListener("click", () => {
      isRecOpen = !isRecOpen;
      recommendedChevron.classList.toggle("closed", !isRecOpen);
      recommendedCardsGrid.classList.toggle("hidden", !isRecOpen);
    });
  }

  // Recommended Cards Click Handling
  document.querySelectorAll(".rec-task-card").forEach((card) => {
    card.addEventListener("click", () => {
      const title = card.dataset.title || "Scheduled Task";
      const promptText = card.dataset.prompt || "";
      const type = card.dataset.type || "reminder";
      const rec = card.dataset.rec || "daily";
      const timeVal = card.dataset.time || "08:00";
      const days = card.dataset.days ? [card.dataset.days] : [];

      openTaskModal({
        id: "",
        title: title,
        prompt: promptText,
        task_type: type,
        recurrence: rec,
        time: timeVal,
        days_of_week: days,
      });
    });
  });

  // Natural Language Input Auto-resize & Submit
  if (scheduleInput) {
    scheduleInput.addEventListener("input", () => {
      scheduleInput.style.height = "auto";
      scheduleInput.style.height = Math.min(scheduleInput.scrollHeight, 120) + "px";
    });

    scheduleInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleNlSubmit();
      }
    });
  }

  if (scheduleSubmitBtn) {
    scheduleSubmitBtn.addEventListener("click", handleNlSubmit);
  }

  if (schedulePlusBtn) {
    schedulePlusBtn.addEventListener("click", () => {
      openTaskModal({
        id: "",
        title: "",
        prompt: "",
        task_type: "reminder",
        recurrence: "daily",
        time: "08:00",
      });
    });
  }

  if (emptyCreateTaskBtn) {
    emptyCreateTaskBtn.addEventListener("click", () => {
      openTaskModal({
        id: "",
        title: "",
        prompt: "",
        task_type: "briefing",
        recurrence: "daily",
        time: "08:00",
      });
    });
  }

  // Voice recognition for schedule input
  setupSpeechRecognition(scheduleMicBtn, scheduleInput, () => {
    if (scheduleInput) {
      scheduleInput.style.height = "auto";
      scheduleInput.style.height = Math.min(scheduleInput.scrollHeight, 120) + "px";
    }
  });

  // Submit NL schedule text to parse-nl endpoint
  async function handleNlSubmit() {
    const text = scheduleInput ? scheduleInput.value.trim() : "";
    if (!text) return;

    if (scheduleSubmitBtn) scheduleSubmitBtn.disabled = true;
    showToast("Parsing schedule instruction... ⏳");

    try {
      const res = await fetch("/api/tasks/parse-nl", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": userSessionId,
        },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to parse schedule");

      const p = data.parsed;
      scheduleInput.value = "";
      scheduleInput.style.height = "auto";

      // Open confirmation dialog pre-filled (Never silently create ambiguous tasks)
      openTaskModal({
        id: "",
        title: p.title,
        prompt: p.prompt,
        task_type: p.task_type,
        recurrence: p.recurrence,
        time: p.time,
        days_of_week: p.days_of_week || [],
        specific_date: p.specific_date,
      });

    } catch (err) {
      showToast(`Could not parse: ${err.message}`);
    } finally {
      if (scheduleSubmitBtn) scheduleSubmitBtn.disabled = false;
    }
  }

  // ---------------------------------------------------------------------------
  // Task Confirmation & Edit Modal Controller
  // ---------------------------------------------------------------------------
  function openTaskModal(taskData = {}) {
    modalTaskId.value = taskData.id || "";
    modalTaskTitle.value = taskData.title || "";
    modalTaskPrompt.value = taskData.prompt || "";
    modalTaskType.value = taskData.task_type || "reminder";
    modalTaskRecurrence.value = taskData.recurrence || "daily";
    modalTaskTime.value = taskData.time || "08:00";
    modalTaskDate.value = taskData.specific_date || "";

    confirmModalTitle.textContent = taskData.id ? "Edit Scheduled Task" : "Create Scheduled Task";
    modalSaveTaskBtn.textContent = taskData.id ? "Save Changes" : "Create Task";

    updateModalRecurrenceFields();

    // Reset Day buttons
    const activeDays = taskData.days_of_week || [];
    document.querySelectorAll(".btn-day-toggle").forEach((btn) => {
      const isDay = activeDays.includes(btn.dataset.day);
      btn.classList.toggle("selected", isDay);
    });

    taskConfirmModal.classList.remove("hidden");
    taskConfirmModal.style.display = "flex";
    modalTaskTitle.focus();
  }

  function closeTaskModal() {
    taskConfirmModal.classList.add("hidden");
    taskConfirmModal.style.display = "none";
  }

  if (closeConfirmModalBtn) closeConfirmModalBtn.addEventListener("click", closeTaskModal);
  if (modalCancelBtn) modalCancelBtn.addEventListener("click", closeTaskModal);

  if (taskConfirmModal) {
    taskConfirmModal.addEventListener("click", (e) => {
      if (e.target === taskConfirmModal) closeTaskModal();
    });
  }

  // Toggle Days / Date groups based on recurrence dropdown
  function updateModalRecurrenceFields() {
    const rec = modalTaskRecurrence.value;
    if (rec === "once") {
      modalDateGroup.classList.remove("hidden");
      modalDaysGroup.classList.add("hidden");
    } else if (rec === "weekly" || rec === "custom") {
      modalDateGroup.classList.add("hidden");
      modalDaysGroup.classList.remove("hidden");
    } else {
      modalDateGroup.classList.add("hidden");
      modalDaysGroup.classList.add("hidden");
    }
  }

  if (modalTaskRecurrence) {
    modalTaskRecurrence.addEventListener("change", updateModalRecurrenceFields);
  }

  // Days of week toggles
  document.querySelectorAll(".btn-day-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.classList.toggle("selected");
    });
  });

  // Save / Create Task Submission
  if (taskConfigForm) {
    taskConfigForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const selectedDays = [];
      document.querySelectorAll(".btn-day-toggle.selected").forEach((btn) => {
        selectedDays.push(btn.dataset.day);
      });

      const payload = {
        title: modalTaskTitle.value.trim(),
        prompt: modalTaskPrompt.value.trim(),
        task_type: modalTaskType.value,
        recurrence: modalTaskRecurrence.value,
        time: modalTaskTime.value,
        days_of_week: selectedDays,
        specific_date: modalTaskDate.value || null,
        timezone: userTz,
      };

      const taskId = modalTaskId.value;
      const isEdit = !!taskId;

      try {
        const url = isEdit ? `/api/tasks/${taskId}` : "/api/tasks";
        const method = isEdit ? "PUT" : "POST";

        const res = await fetch(url, {
          method: method,
          headers: {
            "Content-Type": "application/json",
            "X-Session-ID": userSessionId,
          },
          body: JSON.stringify(payload),
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to save task");

        closeTaskModal();
        showToast(isEdit ? "Task updated ✓" : "Task created ✓");
        loadScheduledTasks();

      } catch (err) {
        showToast(`Error saving task: ${err.message}`);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Load & Render Scheduled Tasks
  // ---------------------------------------------------------------------------
  async function loadScheduledTasks() {
    try {
      const res = await fetch(`/api/tasks?status=${currentTaskFilter}`, {
        headers: { "X-Session-ID": userSessionId },
      });

      if (!res.ok) throw new Error("Failed to load tasks");
      const data = await res.json();
      loadedTasks = data.tasks || [];

      renderScheduledTasks(loadedTasks);
    } catch (err) {
      console.error("Error loading tasks:", err);
    }
  }

  function renderScheduledTasks(tasks) {
    if (!scheduledTasksGrid) return;
    scheduledTasksGrid.innerHTML = "";

    if (tasksCountBadge) tasksCountBadge.textContent = tasks.length;

    if (tasks.length === 0) {
      if (scheduledEmptyState) scheduledEmptyState.classList.remove("hidden");
      scheduledTasksGrid.classList.add("hidden");
      return;
    }

    if (scheduledEmptyState) scheduledEmptyState.classList.add("hidden");
    scheduledTasksGrid.classList.remove("hidden");

    tasks.forEach((task) => {
      const card = document.createElement("div");
      card.className = "task-card";
      card.dataset.id = task.id;

      const icon = TASK_ICONS[task.task_type] || "⏰";
      const statusClass = (task.status || "active").toLowerCase();
      const statusIcon = statusClass === "active" ? "🟢" : (statusClass === "paused" ? "⏸" : (statusClass === "completed" ? "✓" : "❌"));
      const statusLabel = statusClass.charAt(0).toUpperCase() + statusClass.slice(1);

      let scheduleText = formatRecurrenceLabel(task);
      let nextRunText = formatNextRun(task.next_run, task.status);

      card.innerHTML = `
        <div class="task-card-header">
          <div class="task-card-title-group">
            <span class="task-type-badge-icon">${icon}</span>
            <div>
              <h4 class="task-card-title">${escapeHtml(task.title)}</h4>
              <span class="task-card-schedule">${escapeHtml(scheduleText)}</span>
            </div>
          </div>
          <button type="button" class="btn-task-menu" title="Task actions">•••</button>
        </div>

        <div class="task-card-prompt">${escapeHtml(task.prompt)}</div>

        <div class="task-card-footer">
          <span class="task-status-pill ${statusClass}">${statusIcon} ${statusLabel}</span>
          <span class="task-next-run">${escapeHtml(nextRunText)}</span>
        </div>
      `;

      // ⋯ Options button click
      const menuBtn = card.querySelector(".btn-task-menu");
      menuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        openTaskContextMenu(e, task);
      });

      // Card click opens history
      card.addEventListener("click", (e) => {
        if (e.target.closest(".btn-task-menu")) return;
        openTaskHistoryModal(task);
      });

      scheduledTasksGrid.appendChild(card);
    });
  }

  function formatRecurrenceLabel(task) {
    const rec = task.recurrence || "daily";
    const time = task.time || "08:00";
    const formattedTime = formatHourMinute(time);

    if (rec === "daily") return `Every day at ${formattedTime}`;
    if (rec === "weekdays") return `Weekdays at ${formattedTime}`;
    if (rec === "once") return task.specific_date ? `Once on ${task.specific_date} at ${formattedTime}` : `Once at ${formattedTime}`;
    if (rec === "weekly") {
      const days = task.days_of_week && task.days_of_week.length > 0 ? task.days_of_week.join(", ") : "Monday";
      return `Every ${days} at ${formattedTime}`;
    }
    return `Scheduled at ${formattedTime}`;
  }

  function formatHourMinute(timeStr) {
    try {
      const parts = timeStr.split(":");
      let h = parseInt(parts[0], 10);
      const m = parts[1] || "00";
      const meridiem = h >= 12 ? "PM" : "AM";
      if (h > 12) h -= 12;
      if (h === 0) h = 12;
      return `${h}:${m} ${meridiem}`;
    } catch (e) {
      return timeStr;
    }
  }

  function formatNextRun(isoStr, status) {
    if (status === "paused") return "Paused";
    if (status === "completed") return "Completed";
    if (!isoStr) return "Scheduled";

    try {
      const dt = new Date(isoStr);
      const now = new Date();
      const diffMs = dt - now;

      if (diffMs < 0) return "Due soon";

      const diffHours = Math.round(diffMs / (1000 * 60 * 60));
      if (diffHours < 24) {
        return `Next run: Today at ${dt.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
      }
      return `Next run: ${dt.toLocaleDateString([], { month: "short", day: "numeric" })}, ${dt.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
    } catch (e) {
      return "Next run pending";
    }
  }

  // ---------------------------------------------------------------------------
  // Task Context Menu Operations
  // ---------------------------------------------------------------------------
  function openTaskContextMenu(e, task) {
    contextTargetTaskId = task.id;
    activeHistoryTask = task;

    ctxTaskPauseResume.textContent = task.status === "paused" ? "▶ Resume" : "⏸ Pause";

    const rect = e.target.getBoundingClientRect();
    taskItemContextMenu.style.top = `${rect.bottom + 4}px`;
    taskItemContextMenu.style.left = `${Math.min(rect.left, window.innerWidth - 180)}px`;
    taskItemContextMenu.classList.remove("hidden");
  }

  if (ctxTaskRunNow) {
    ctxTaskRunNow.addEventListener("click", () => {
      taskItemContextMenu.classList.add("hidden");
      executeRunNow(contextTargetTaskId);
    });
  }

  if (ctxTaskHistory) {
    ctxTaskHistory.addEventListener("click", () => {
      taskItemContextMenu.classList.add("hidden");
      const t = loadedTasks.find((item) => item.id === contextTargetTaskId);
      if (t) openTaskHistoryModal(t);
    });
  }

  if (ctxTaskEdit) {
    ctxTaskEdit.addEventListener("click", () => {
      taskItemContextMenu.classList.add("hidden");
      const t = loadedTasks.find((item) => item.id === contextTargetTaskId);
      if (t) openTaskModal(t);
    });
  }

  if (ctxTaskPauseResume) {
    ctxTaskPauseResume.addEventListener("click", async () => {
      taskItemContextMenu.classList.add("hidden");
      const t = loadedTasks.find((item) => item.id === contextTargetTaskId);
      if (!t) return;

      const isPaused = t.status === "paused";
      const action = isPaused ? "resume" : "pause";

      try {
        const res = await fetch(`/api/tasks/${t.id}/${action}`, {
          method: "POST",
          headers: { "X-Session-ID": userSessionId },
        });
        if (!res.ok) throw new Error("Failed to update status");
        showToast(isPaused ? "Task resumed 🟢" : "Task paused ⏸");
        loadScheduledTasks();
      } catch (err) {
        showToast("Error updating task status ✕");
      }
    });
  }

  if (ctxTaskDelete) {
    ctxTaskDelete.addEventListener("click", async () => {
      taskItemContextMenu.classList.add("hidden");
      const t = loadedTasks.find((item) => item.id === contextTargetTaskId);
      if (!t) return;

      if (!confirm(`Are you sure you want to delete "${t.title}"?`)) return;

      try {
        const res = await fetch(`/api/tasks/${t.id}`, {
          method: "DELETE",
          headers: { "X-Session-ID": userSessionId },
        });
        if (!res.ok) throw new Error("Delete failed");
        showToast("Task deleted 🗑️");
        loadScheduledTasks();
      } catch (err) {
        showToast("Error deleting task ✕");
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Run Now Execution Handler
  // ---------------------------------------------------------------------------
  async function executeRunNow(taskId) {
    const task = loadedTasks.find((t) => t.id === taskId);
    if (!task) return;

    showToast("🤖 Running task...");

    try {
      const res = await fetch(`/api/tasks/${taskId}/run`, {
        method: "POST",
        headers: { "X-Session-ID": userSessionId },
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Execution failed");

      showToast("✓ Task completed");
      loadScheduledTasks();

      // Open history modal with updated results
      if (data.task) {
        openTaskHistoryModal(data.task);
      }
    } catch (err) {
      showToast(`✕ Task failed: ${err.message}`);
      loadScheduledTasks();
    }
  }

  // ---------------------------------------------------------------------------
  // Task Execution History Modal Controller
  // ---------------------------------------------------------------------------
  function openTaskHistoryModal(task) {
    activeHistoryTask = task;
    historyModalTitle.textContent = task.title;
    historyModalSchedule.textContent = formatRecurrenceLabel(task);
    historyModalIcon.textContent = TASK_ICONS[task.task_type] || "⏰";

    renderHistoryEntries(task.execution_history || []);

    taskHistoryModal.classList.remove("hidden");
    taskHistoryModal.style.display = "flex";
  }

  function closeHistoryModal() {
    taskHistoryModal.classList.add("hidden");
    taskHistoryModal.style.display = "none";
  }

  if (closeHistoryModalBtn) closeHistoryModalBtn.addEventListener("click", closeHistoryModal);

  if (taskHistoryModal) {
    taskHistoryModal.addEventListener("click", (e) => {
      if (e.target === taskHistoryModal) closeHistoryModal();
    });
  }

  if (historyRunNowBtn) {
    historyRunNowBtn.addEventListener("click", () => {
      if (activeHistoryTask) {
        executeRunNow(activeHistoryTask.id);
      }
    });
  }

  function renderHistoryEntries(history) {
    if (!historyEntriesList) return;
    historyEntriesList.innerHTML = "";

    if (!history || history.length === 0) {
      historyEntriesList.innerHTML = `
        <div style="padding: 30px; text-align: center; color: var(--text-muted); font-size: 13.5px;">
          No previous executions recorded yet.<br/>Click <strong>▶ Run Now</strong> to test execution immediately.
        </div>
      `;
      return;
    }

    history.forEach((entry) => {
      const card = document.createElement("div");
      card.className = "history-entry-card";

      const timeStr = entry.executed_at ? new Date(entry.executed_at).toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      }) : "Recently";

      const isSuccess = entry.status === "completed";
      const statusIcon = isSuccess ? "✓ Completed" : "❌ Failed";
      const statusClass = isSuccess ? "active" : "failed";

      card.innerHTML = `
        <div class="history-entry-meta">
          <span class="history-entry-time">${escapeHtml(timeStr)}</span>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="task-status-pill ${statusClass}">${statusIcon}</span>
            <span class="history-entry-duration">${entry.duration_seconds || 0}s</span>
          </div>
        </div>
        <div class="history-entry-result markdown-body">${renderMarkdown(entry.result || entry.error || "No output")}</div>
      `;

      attachCodeCopyButtons(card);
      historyEntriesList.appendChild(card);
    });
  }

  // ---------------------------------------------------------------------------
  // Translation Feature Controller
  // ---------------------------------------------------------------------------
  const TRANSLATION_STORAGE_KEY = "cloud_ai_translation_history";

  let translationLanguages = [];
  let sourceLangCode = "auto";
  let sourceLangName = "Auto Detect";
  let targetLangCode = "ta";
  let targetLangName = "Tamil";
  let translationMode = "natural";
  let isTranslating = false;
  let translationSpeechRecognition = null;
  let isTranslationListening = false;
  let uploadedTranslationFile = null;

  // Elements
  const sourceLangBtn = document.getElementById("sourceLangBtn");
  const sourceLangLabel = document.getElementById("sourceLangLabel");
  const sourceLangMenu = document.getElementById("sourceLangMenu");
  const sourceLangSearchInput = document.getElementById("sourceLangSearchInput");
  const sourceLangList = document.getElementById("sourceLangList");

  const targetLangBtn = document.getElementById("targetLangBtn");
  const targetLangLabel = document.getElementById("targetLangLabel");
  const targetLangMenu = document.getElementById("targetLangMenu");
  const targetLangSearchInput = document.getElementById("targetLangSearchInput");
  const targetLangList = document.getElementById("targetLangList");

  const sourceText = document.getElementById("sourceText");
  const sourceCharCount = document.getElementById("sourceCharCount");
  const targetText = document.getElementById("targetText");
  const targetStatusBadge = document.getElementById("targetStatusBadge");

  const swapLangBtn = document.getElementById("swapLangBtn");
  const submitTranslateBtn = document.getElementById("submitTranslateBtn");
  const clearTranslationBtn = document.getElementById("clearTranslationBtn");
  const translateMicBtn = document.getElementById("translateMicBtn");
  const translateDocBtn = document.getElementById("translateDocBtn");
  const translateDocInput = document.getElementById("translateDocInput");
  const sourceDocBadge = document.getElementById("sourceDocBadge");
  const sourceDocName = document.getElementById("sourceDocName");
  const removeSourceDocBtn = document.getElementById("removeSourceDocBtn");

  const copyTranslationBtn = document.getElementById("copyTranslationBtn");
  const readTranslationBtn = document.getElementById("readTranslationBtn");
  const useInChatBtn = document.getElementById("useInChatBtn");

  const recentTranslationsList = document.getElementById("recentTranslationsList");
  const clearHistoryBtn = document.getElementById("clearHistoryBtn");

  // Load languages from API
  async function loadLanguages() {
    if (translationLanguages.length > 0) return;
    try {
      const res = await fetch("/api/languages");
      const data = await res.json();
      if (data && data.languages) {
        translationLanguages = data.languages;
        renderLanguageLists();
      }
    } catch (e) {
      console.warn("Could not load translation languages", e);
    }
  }

  function renderLanguageLists() {
    renderLanguageDropdown(sourceLangList, translationLanguages, true, sourceLangCode, (item) => {
      sourceLangCode = item.code;
      sourceLangName = item.name;
      if (sourceLangLabel) sourceLangLabel.textContent = item.name;
      if (sourceLangMenu) sourceLangMenu.classList.add("hidden");
    });

    renderLanguageDropdown(targetLangList, translationLanguages.filter((l) => l.code !== "auto"), false, targetLangCode, (item) => {
      targetLangCode = item.code;
      targetLangName = item.name;
      if (targetLangLabel) targetLangLabel.textContent = item.name;
      if (targetLangMenu) targetLangMenu.classList.add("hidden");
    });
  }

  function renderLanguageDropdown(container, list, isSource, currentSelected, onSelect) {
    if (!container) return;
    container.innerHTML = "";
    list.forEach((item) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `lang-opt-btn ${item.code === currentSelected || item.name === currentSelected ? "selected" : ""}`;
      btn.innerHTML = `
        <span class="lang-opt-name">${escapeHtml(item.name)}</span>
        <span class="lang-opt-native">${escapeHtml(item.native || "")}</span>
      `;
      btn.addEventListener("click", () => {
        onSelect(item);
        renderLanguageLists();
      });
      container.appendChild(btn);
    });
  }

  function filterLanguageList(container, query) {
    if (!container) return;
    const q = (query || "").trim().toLowerCase();
    const buttons = container.querySelectorAll(".lang-opt-btn");
    buttons.forEach((btn) => {
      const text = btn.textContent.toLowerCase();
      btn.style.display = text.includes(q) ? "flex" : "none";
    });
  }

  // Translation Modes Selector
  document.querySelectorAll(".btn-mode-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-mode-pill").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      translationMode = btn.dataset.mode || "natural";
      showToast(`Translation Mode: ${btn.textContent} 🌐`);
    });
  });

  // Toggle Source Language Menu
  if (sourceLangBtn && sourceLangMenu) {
    sourceLangBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isHidden = sourceLangMenu.classList.toggle("hidden");
      if (targetLangMenu) targetLangMenu.classList.add("hidden");
      if (!isHidden && sourceLangSearchInput) {
        sourceLangSearchInput.value = "";
        filterLanguageList(sourceLangList, "");
        setTimeout(() => sourceLangSearchInput.focus(), 50);
      }
    });
  }

  if (sourceLangSearchInput) {
    sourceLangSearchInput.addEventListener("input", (e) => {
      filterLanguageList(sourceLangList, e.target.value);
    });
  }

  // Toggle Target Language Menu
  if (targetLangBtn && targetLangMenu) {
    targetLangBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isHidden = targetLangMenu.classList.toggle("hidden");
      if (sourceLangMenu) sourceLangMenu.classList.add("hidden");
      if (!isHidden && targetLangSearchInput) {
        targetLangSearchInput.value = "";
        filterLanguageList(targetLangList, "");
        setTimeout(() => targetLangSearchInput.focus(), 50);
      }
    });
  }

  if (targetLangSearchInput) {
    targetLangSearchInput.addEventListener("input", (e) => {
      filterLanguageList(targetLangList, e.target.value);
    });
  }

  // Close menus on outside click
  document.addEventListener("click", (e) => {
    if (sourceLangMenu && !sourceLangMenu.contains(e.target) && !sourceLangBtn.contains(e.target)) {
      sourceLangMenu.classList.add("hidden");
    }
    if (targetLangMenu && !targetLangMenu.contains(e.target) && !targetLangBtn.contains(e.target)) {
      targetLangMenu.classList.add("hidden");
    }
  });

  // Source Textarea Character Counter & NL Detection
  if (sourceText) {
    sourceText.addEventListener("input", () => {
      if (sourceCharCount) {
        sourceCharCount.textContent = sourceText.value.length;
      }
    });
  }

  // Swap Languages Action
  if (swapLangBtn) {
    swapLangBtn.addEventListener("click", () => {
      const oldSourceCode = sourceLangCode;
      const oldSourceName = sourceLangName;
      const oldTargetCode = targetLangCode;
      const oldTargetName = targetLangName;

      // Handle Auto Detect gracefully
      if (oldSourceCode === "auto") {
        sourceLangCode = oldTargetCode;
        sourceLangName = oldTargetName;
        targetLangCode = "en";
        targetLangName = "English";
      } else {
        sourceLangCode = oldTargetCode;
        sourceLangName = oldTargetName;
        targetLangCode = oldSourceCode;
        targetLangName = oldSourceName;
      }

      if (sourceLangLabel) sourceLangLabel.textContent = sourceLangName;
      if (targetLangLabel) targetLangLabel.textContent = targetLangName;

      // Swap text
      const currentSrc = sourceText ? sourceText.value : "";
      const currentTgt = targetText ? targetText.textContent : "";
      if (sourceText) {
        sourceText.value = currentTgt;
        if (sourceCharCount) sourceCharCount.textContent = currentTgt.length;
      }
      if (targetText) {
        targetText.textContent = currentSrc;
      }

      renderLanguageLists();
      showToast(`Swapped: ${sourceLangName} ⇄ ${targetLangName} 🔄`);
    });
  }

  // Speech-to-Text for Translation
  if (translateMicBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      translationSpeechRecognition = new SpeechRecognition();
      translationSpeechRecognition.continuous = false;
      translationSpeechRecognition.interimResults = false;
      translationSpeechRecognition.lang = "en-US";

      translationSpeechRecognition.onstart = () => {
        isTranslationListening = true;
        translateMicBtn.classList.add("listening");
        showToast("Listening for translation input... 🎙️");
      };

      translationSpeechRecognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        if (sourceText) {
          sourceText.value = (sourceText.value ? sourceText.value + " " : "") + transcript;
          if (sourceCharCount) sourceCharCount.textContent = sourceText.value.length;
          sourceText.focus();
        }
      };

      translationSpeechRecognition.onerror = (err) => {
        console.error("Translation speech recognition error:", err);
        showToast("Could not recognize speech. Please try again 🎙️");
      };

      translationSpeechRecognition.onend = () => {
        isTranslationListening = false;
        translateMicBtn.classList.remove("listening");
      };

      translateMicBtn.addEventListener("click", () => {
        if (isTranslationListening) {
          translationSpeechRecognition.stop();
        } else {
          translationSpeechRecognition.start();
        }
      });
    } else {
      translateMicBtn.addEventListener("click", () => {
        showToast("Speech recognition is not supported in this browser 🎙️");
      });
    }
  }

  // Document Upload Translation
  if (translateDocBtn && translateDocInput) {
    translateDocBtn.addEventListener("click", () => {
      translateDocInput.click();
    });

    translateDocInput.addEventListener("change", async () => {
      const file = translateDocInput.files[0];
      if (!file) return;

      uploadedTranslationFile = file;
      if (sourceDocBadge && sourceDocName) {
        sourceDocName.textContent = file.name;
        sourceDocBadge.classList.remove("hidden");
      }

      showToast(`Document selected: ${file.name} 📄. Translating...`);
      await executeFileTranslation(file);
      translateDocInput.value = "";
    });
  }

  if (removeSourceDocBtn) {
    removeSourceDocBtn.addEventListener("click", () => {
      uploadedTranslationFile = null;
      if (sourceDocBadge) sourceDocBadge.classList.add("hidden");
      if (translateDocInput) translateDocInput.value = "";
      showToast("Document attachment removed 📄");
    });
  }

  async function executeFileTranslation(file) {
    if (isTranslating) return;
    isTranslating = true;
    if (submitTranslateBtn) {
      submitTranslateBtn.disabled = true;
      submitTranslateBtn.textContent = "Translating...";
    }
    if (targetStatusBadge) targetStatusBadge.classList.remove("hidden");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_language", targetLangName);
    formData.append("source_language", sourceLangName);
    formData.append("mode", translationMode);

    try {
      const res = await fetch("/api/translate/file", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data && data.success) {
        if (targetText) targetText.textContent = data.translation;
        if (sourceText && data.extracted_preview) {
          sourceText.value = `[Document: ${file.name}]\n\n${data.extracted_preview}`;
          if (sourceCharCount) sourceCharCount.textContent = sourceText.value.length;
        }
        if (data.source_language && data.source_language !== "Auto") {
          sourceLangName = data.source_language;
          if (sourceLangLabel) sourceLangLabel.textContent = sourceLangName;
        }

        saveTranslationHistory({
          source_lang: data.source_language || sourceLangName,
          target_lang: targetLangName,
          mode: translationMode,
          source_text: `[Document: ${file.name}]`,
          target_text: data.translation,
        });

        showToast(`Document translated to ${targetLangName} ✓`);
      } else {
        const errMsg = (data && data.error) ? data.error : "File translation failed";
        if (targetText) targetText.textContent = `Error: ${errMsg}`;
        showToast(`Error: ${errMsg}`);
      }
    } catch (e) {
      console.error("File translation failed", e);
      if (targetText) targetText.textContent = `Error: ${e.message}`;
      showToast("Network error during file translation.");
    } finally {
      isTranslating = false;
      if (submitTranslateBtn) {
        submitTranslateBtn.disabled = false;
        submitTranslateBtn.innerHTML = `<span>Translate</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>`;
      }
      if (targetStatusBadge) targetStatusBadge.classList.add("hidden");
    }
  }

  // Clear Action
  if (clearTranslationBtn) {
    clearTranslationBtn.addEventListener("click", () => {
      const hasContent = (sourceText && sourceText.value.trim().length > 0) || (targetText && targetText.textContent.trim().length > 0);
      if (hasContent && sourceText.value.trim().length > 80) {
        if (!confirm("Clear source and translated text?")) return;
      }
      if (sourceText) sourceText.value = "";
      if (targetText) targetText.textContent = "";
      if (sourceCharCount) sourceCharCount.textContent = "0";
      if (sourceDocBadge) sourceDocBadge.classList.add("hidden");
      uploadedTranslationFile = null;
      showToast("Cleared text ✕");
    });
  }

  // Copy Translation Action
  if (copyTranslationBtn) {
    copyTranslationBtn.addEventListener("click", async () => {
      const text = targetText ? targetText.textContent.trim() : "";
      if (!text) {
        showToast("No translated text to copy 📋");
        return;
      }
      try {
        await navigator.clipboard.writeText(text);
        showToast("✓ Translation copied");
      } catch (e) {
        // Fallback
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        showToast("✓ Translation copied");
      }
    });
  }

  // Read Aloud Translated Text
  if (readTranslationBtn) {
    readTranslationBtn.addEventListener("click", () => {
      const text = targetText ? targetText.textContent.trim() : "";
      if (!text) {
        showToast("No translated text to read 🔊");
        return;
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
        showToast("Reading aloud translated text 🔊");
      } else {
        showToast("Speech synthesis is not supported in this browser 🔊");
      }
    });
  }

  // Use in Chat Action
  if (useInChatBtn) {
    useInChatBtn.addEventListener("click", () => {
      const text = targetText ? targetText.textContent.trim() : "";
      if (!text) {
        showToast("No translated text to use in chat ↗");
        return;
      }
      if (messageInput) {
        messageInput.value = text;
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 180) + "px";
        switchToView("chat");
        messageInput.focus();
        showToast("Translation added to chat composer ↗");
      }
    });
  }

  // Execute Text Translation
  async function executeTranslation() {
    if (isTranslating) return;
    const rawText = sourceText ? sourceText.value.trim() : "";
    if (!rawText) {
      showToast("Please enter text to translate.");
      if (sourceText) sourceText.focus();
      return;
    }

    isTranslating = true;
    if (submitTranslateBtn) {
      submitTranslateBtn.disabled = true;
      submitTranslateBtn.textContent = "Translating...";
    }
    if (targetStatusBadge) targetStatusBadge.classList.remove("hidden");

    try {
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: rawText,
          source_language: sourceLangName,
          target_language: targetLangName,
          mode: translationMode,
        }),
      });

      const data = await res.json();
      if (data && data.success) {
        if (targetText) targetText.textContent = data.translation;
        if (data.source_language && data.source_language !== "Auto") {
          sourceLangName = data.source_language;
          if (sourceLangLabel) sourceLangLabel.textContent = sourceLangName;
        }

        saveTranslationHistory({
          source_lang: data.source_language || sourceLangName,
          target_lang: targetLangName,
          mode: translationMode,
          source_text: rawText,
          target_text: data.translation,
        });

        showToast(`Translated to ${targetLangName} ✓`);
      } else {
        const errMsg = (data && data.error) ? data.error : "Translation failed";
        if (targetText) targetText.textContent = `Error: ${errMsg}`;
        showToast(`Error: ${errMsg}`);
      }
    } catch (e) {
      console.error("Translation request failed", e);
      if (targetText) targetText.textContent = `Error: ${e.message}`;
      showToast("Network error during translation.");
    } finally {
      isTranslating = false;
      if (submitTranslateBtn) {
        submitTranslateBtn.disabled = false;
        submitTranslateBtn.innerHTML = `<span>Translate</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>`;
      }
      if (targetStatusBadge) targetStatusBadge.classList.add("hidden");
    }
  }

  if (submitTranslateBtn) {
    submitTranslateBtn.addEventListener("click", executeTranslation);
  }

  // Allow Ctrl+Enter or Cmd+Enter to translate
  if (sourceText) {
    sourceText.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        executeTranslation();
      }
    });
  }

  // Translation History Management
  function loadTranslationHistory() {
    try {
      const stored = localStorage.getItem(TRANSLATION_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch (e) {
      console.warn("Could not load translation history", e);
    }
    return [];
  }

  function saveTranslationHistory(entry) {
    try {
      let history = loadTranslationHistory();
      // Remove any duplicate of exact same source text
      history = history.filter((h) => h.source_text !== entry.source_text);
      entry.id = "trans_" + Date.now();
      entry.timestamp = Date.now();
      history.unshift(entry);
      // Keep max 10
      history = history.slice(0, 10);
      localStorage.setItem(TRANSLATION_STORAGE_KEY, JSON.stringify(history));
      renderTranslationHistory();
    } catch (e) {
      console.warn("Could not save translation history", e);
    }
  }

  function renderTranslationHistory() {
    if (!recentTranslationsList) return;
    const history = loadTranslationHistory();
    recentTranslationsList.innerHTML = "";

    if (history.length === 0) {
      recentTranslationsList.innerHTML = `
        <div class="empty-history-notice">
          No recent translations yet. Enter text above and click Translate!
        </div>
      `;
      return;
    }

    history.forEach((item) => {
      const card = document.createElement("div");
      card.className = "recent-trans-card";
      card.innerHTML = `
        <div class="recent-trans-card-top">
          <span class="recent-trans-lang-pair">${escapeHtml(item.source_lang)} → ${escapeHtml(item.target_lang)}</span>
          <span class="recent-trans-mode-tag">${escapeHtml(item.mode || "natural")}</span>
        </div>
        <div class="recent-trans-source-preview" title="${escapeHtml(item.source_text)}">${escapeHtml(item.source_text)}</div>
        <div class="recent-trans-target-preview" title="${escapeHtml(item.target_text)}">${escapeHtml(item.target_text)}</div>
      `;

      card.addEventListener("click", () => {
        if (sourceText) {
          sourceText.value = item.source_text;
          if (sourceCharCount) sourceCharCount.textContent = item.source_text.length;
        }
        if (targetText) {
          targetText.textContent = item.target_text;
        }
        if (item.target_lang) {
          targetLangName = item.target_lang;
          if (targetLangLabel) targetLangLabel.textContent = item.target_lang;
        }
        if (item.source_lang) {
          sourceLangName = item.source_lang;
          if (sourceLangLabel) sourceLangLabel.textContent = item.source_lang;
        }
        if (item.mode) {
          translationMode = item.mode;
          document.querySelectorAll(".btn-mode-pill").forEach((b) => {
            b.classList.toggle("active", b.dataset.mode === item.mode);
          });
        }
        showToast(`Restored translation (${item.source_lang} → ${item.target_lang}) ↺`);
      });

      recentTranslationsList.appendChild(card);
    });
  }

  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener("click", () => {
      if (confirm("Clear your recent translation history?")) {
        localStorage.removeItem(TRANSLATION_STORAGE_KEY);
        renderTranslationHistory();
        showToast("Translation history cleared ✕");
      }
    });
  }

  function initTranslationView() {
    loadLanguages();
    renderTranslationHistory();
  }

  // ---------------------------------------------------------------------------
  // AI Plugin Marketplace Controller
  // ---------------------------------------------------------------------------
  const pluginsGridContainer = document.getElementById("pluginsGridContainer");
  const pluginsConnectedBadge = document.getElementById("pluginsConnectedBadge");
  const pluginSearchInput = document.getElementById("pluginSearchInput");
  const clearPluginSearchBtn = document.getElementById("clearPluginSearchBtn");
  const filterConnectedOnlyCheckbox = document.getElementById("filterConnectedOnlyCheckbox");
  const openPluginLogsBtn = document.getElementById("openPluginLogsBtn");

  // Connect Modal Elements
  const pluginConnectModal = document.getElementById("pluginConnectModal");
  const closeConnectModalBtn = document.getElementById("closeConnectModalBtn");
  const cancelConnectModalBtn = document.getElementById("cancelConnectModalBtn");
  const confirmConnectPluginBtn = document.getElementById("confirmConnectPluginBtn");
  const connectModalPluginId = document.getElementById("connectModalPluginId");
  const connectModalIconBox = document.getElementById("connectModalIconBox");
  const connectModalTitle = document.getElementById("connectModalTitle");
  const connectModalCategory = document.getElementById("connectModalCategory");
  const connectModalDescription = document.getElementById("connectModalDescription");
  const connectModalPermissionsList = document.getElementById("connectModalPermissionsList");
  const connectModalAuthGroup = document.getElementById("connectModalAuthGroup");
  const connectModalApiKey = document.getElementById("connectModalApiKey");

  // Manage Modal Elements
  const pluginManageModal = document.getElementById("pluginManageModal");
  const closeManageModalBtn = document.getElementById("closeManageModalBtn");
  const manageModalIconBox = document.getElementById("manageModalIconBox");
  const manageModalTitle = document.getElementById("manageModalTitle");
  const manageModalStatusBadge = document.getElementById("manageModalStatusBadge");
  const manageModalVersion = document.getElementById("manageModalVersion");
  const managePermissionsTogglesList = document.getElementById("managePermissionsTogglesList");
  const manageToolsSchemaList = document.getElementById("manageToolsSchemaList");
  const managePluginToggleEnabled = document.getElementById("managePluginToggleEnabled");
  const managePluginToggleLabel = document.getElementById("managePluginToggleLabel");
  const manageDisconnectBtn = document.getElementById("manageDisconnectBtn");
  const manageSaveCloseBtn = document.getElementById("manageSaveCloseBtn");

  // Sandbox Runner Elements
  const sandboxToolSelect = document.getElementById("sandboxToolSelect");
  const sandboxParamsInput = document.getElementById("sandboxParamsInput");
  const runSandboxToolBtn = document.getElementById("runSandboxToolBtn");
  const sandboxOutputArea = document.getElementById("sandboxOutputArea");
  const sandboxOutputPre = document.getElementById("sandboxOutputPre");
  const sandboxDurationBadge = document.getElementById("sandboxDurationBadge");

  // Logs Modal Elements
  const pluginLogsModal = document.getElementById("pluginLogsModal");
  const closePluginLogsModalBtn = document.getElementById("closePluginLogsModalBtn");
  const pluginLogsTableBody = document.getElementById("pluginLogsTableBody");
  const logsEmptyNotice = document.getElementById("logsEmptyNotice");
  const logsPluginFilterSelect = document.getElementById("logsPluginFilterSelect");
  const logsStatusFilterSelect = document.getElementById("logsStatusFilterSelect");
  const refreshPluginLogsBtn = document.getElementById("refreshPluginLogsBtn");
  const clearPluginLogsBtn = document.getElementById("clearPluginLogsBtn");

  let allPluginsCache = [];
  let selectedPluginCategory = "all";
  let pluginSearchQuery = "";
  let filterConnectedOnly = false;
  let activeManagePlugin = null;

  async function loadPluginsMarketplace() {
    try {
      if (pluginsGridContainer) {
        pluginsGridContainer.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">Loading plugin marketplace... ⏳</div>`;
      }
      const res = await fetch("/api/plugins");
      if (!res.ok) throw new Error("Failed to load plugins");
      const data = await res.json();
      allPluginsCache = data.plugins || [];

      // Update header badge
      const connectedCount = allPluginsCache.filter((p) => p.is_connected).length;
      if (pluginsConnectedBadge) {
        pluginsConnectedBadge.textContent = `${connectedCount} Connected`;
      }

      // Populate logs plugin filter select
      if (logsPluginFilterSelect) {
        const currentVal = logsPluginFilterSelect.value;
        logsPluginFilterSelect.innerHTML = `<option value="">All Plugins</option>`;
        allPluginsCache.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent = p.name;
          logsPluginFilterSelect.appendChild(opt);
        });
        logsPluginFilterSelect.value = currentVal;
      }

      renderPluginsList();
    } catch (err) {
      console.error("Error loading plugins:", err);
      if (pluginsGridContainer) {
        pluginsGridContainer.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #ef4444;">Could not load plugins. Please check server connection.</div>`;
      }
    }
  }

  function renderPluginsList() {
    if (!pluginsGridContainer) return;
    pluginsGridContainer.innerHTML = "";

    const q = pluginSearchQuery.trim().toLowerCase();
    const filtered = allPluginsCache.filter((p) => {
      if (filterConnectedOnly && !p.is_connected) return false;

      if (selectedPluginCategory !== "all") {
        const matchCategory = p.category.toLowerCase() === selectedPluginCategory.toLowerCase();
        const matchTag = (p.tags || []).some((t) => t.toLowerCase() === selectedPluginCategory.toLowerCase());
        if (!matchCategory && !matchTag) return false;
      }

      if (q) {
        const inName = p.name.toLowerCase().includes(q);
        const inDesc = p.description.toLowerCase().includes(q);
        const inCat = p.category.toLowerCase().includes(q);
        const inTags = (p.tags || []).some((t) => t.toLowerCase().includes(q));
        if (!inName && !inDesc && !inCat && !inTags) return false;
      }

      return true;
    });

    if (filtered.length === 0) {
      pluginsGridContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 50px 20px; color: var(--text-muted); background: var(--bg-card); border: 1.5px dashed var(--border-medium); border-radius: 16px;">
          <div style="font-size: 36px; margin-bottom: 8px;">🔌</div>
          <h4 style="font-size: 16px; font-weight: 600; color: var(--text-main); margin-bottom: 4px;">No matching apps or plugins found</h4>
          <p style="font-size: 13px;">Try adjusting your search query or selecting a different category filter.</p>
        </div>
      `;
      return;
    }

    filtered.forEach((plugin) => {
      const card = document.createElement("div");
      card.className = `plugin-card ${plugin.is_connected ? "connected" : ""}`;

      const tagsHtml = (plugin.tags || [])
        .slice(0, 4)
        .map((t) => `<span class="plugin-tag-pill">${escapeHtml(t)}</span>`)
        .join("");

      const isConn = plugin.is_connected;
      const isEn = plugin.is_enabled;

      let statusBadgeHtml = "";
      if (isConn) {
        statusBadgeHtml = isEn
          ? `<span class="plugin-status-badge connected">● Connected</span>`
          : `<span class="plugin-status-badge available" style="color: #f59e0b;">⏸ Disabled</span>`;
      } else {
        statusBadgeHtml = `<span class="plugin-status-badge available">○ Available</span>`;
      }

      let actionsHtml = "";
      if (!isConn) {
        actionsHtml = `
          <button type="button" class="btn-plugin-connect" data-plugin-id="${plugin.id}">
            <span>+ Connect</span>
          </button>
        `;
      } else {
        actionsHtml = `
          <div class="plugin-footer-left">
            <span class="btn-plugin-connected-pill">✓ Connected</span>
            <button type="button" class="btn-plugin-manage" data-plugin-id="${plugin.id}" title="Manage permissions and sandbox testing">
              ⚙ Manage
            </button>
          </div>
          <button type="button" class="btn-plugin-disconnect" data-plugin-id="${plugin.id}" title="Disconnect plugin">
            ✕ Disconnect
          </button>
        `;
      }

      card.innerHTML = `
        <div class="plugin-card-top">
          <div class="plugin-icon-badge" style="background: ${plugin.icon_bg || "var(--accent-blue)"};">
            ${plugin.icon || "🔌"}
          </div>
          <div class="plugin-header-info">
            <div class="plugin-title-row">
              <h3 class="plugin-name" title="${escapeHtml(plugin.name)}">${escapeHtml(plugin.name)}</h3>
              ${statusBadgeHtml}
            </div>
            <span class="plugin-category-tag">${escapeHtml(plugin.category)} • v${escapeHtml(plugin.version || "1.0.0")}</span>
          </div>
        </div>
        <p class="plugin-desc" title="${escapeHtml(plugin.description)}">${escapeHtml(plugin.description)}</p>
        <div class="plugin-tags-row">
          ${tagsHtml}
        </div>
        <div class="plugin-card-footer">
          ${actionsHtml}
        </div>
      `;

      // Event listeners on card buttons
      const connectBtn = card.querySelector(".btn-plugin-connect");
      if (connectBtn) {
        connectBtn.addEventListener("click", () => openConnectModal(plugin));
      }

      const manageBtn = card.querySelector(".btn-plugin-manage");
      if (manageBtn) {
        manageBtn.addEventListener("click", () => openManageModal(plugin));
      }

      const disconnectBtn = card.querySelector(".btn-plugin-disconnect");
      if (disconnectBtn) {
        disconnectBtn.addEventListener("click", () => handleDisconnectPlugin(plugin.id, plugin.name));
      }

      pluginsGridContainer.appendChild(card);
    });
  }

  // Category Tab Selection
  document.querySelectorAll(".plugin-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".plugin-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      selectedPluginCategory = tab.dataset.category || "all";
      renderPluginsList();
    });
  });

  // Search Bar Input
  if (pluginSearchInput) {
    pluginSearchInput.addEventListener("input", (e) => {
      pluginSearchQuery = e.target.value;
      if (clearPluginSearchBtn) {
        clearPluginSearchBtn.classList.toggle("hidden", !pluginSearchQuery);
      }
      renderPluginsList();
    });
  }

  if (clearPluginSearchBtn) {
    clearPluginSearchBtn.addEventListener("click", () => {
      if (pluginSearchInput) {
        pluginSearchInput.value = "";
        pluginSearchQuery = "";
        clearPluginSearchBtn.classList.add("hidden");
        renderPluginsList();
        pluginSearchInput.focus();
      }
    });
  }

  // Connected-only filter checkbox
  if (filterConnectedOnlyCheckbox) {
    filterConnectedOnlyCheckbox.addEventListener("change", (e) => {
      filterConnectedOnly = e.target.checked;
      renderPluginsList();
    });
  }

  // ---------------------------------------------------------------------------
  // Connect App Modal
  // ---------------------------------------------------------------------------
  function openConnectModal(plugin) {
    if (!pluginConnectModal) return;
    connectModalPluginId.value = plugin.id;
    if (connectModalIconBox) {
      connectModalIconBox.textContent = plugin.icon || "🔌";
      connectModalIconBox.style.background = plugin.icon_bg || "var(--accent-blue)";
    }
    if (connectModalTitle) connectModalTitle.textContent = `Connect ${plugin.name}`;
    if (connectModalCategory) connectModalCategory.textContent = `${plugin.category} • v${plugin.version || "1.0.0"}`;
    if (connectModalDescription) connectModalDescription.textContent = plugin.description;

    // Requested permissions
    if (connectModalPermissionsList) {
      connectModalPermissionsList.innerHTML = "";
      if (plugin.permissions && plugin.permissions.length > 0) {
        plugin.permissions.forEach((perm) => {
          const item = document.createElement("div");
          item.className = "permission-check-item";
          item.innerHTML = `
            <span class="permission-check-icon">✓</span>
            <div>
              <strong>${escapeHtml(perm.name)}</strong>
              <div style="font-size: 11.5px; color: var(--text-muted);">${escapeHtml(perm.description)}</div>
            </div>
          `;
          connectModalPermissionsList.appendChild(item);
        });
      } else {
        connectModalPermissionsList.innerHTML = `<div style="font-size: 12.5px; color: var(--text-muted);">Standard runtime permissions only.</div>`;
      }
    }

    if (connectModalAuthGroup) {
      connectModalAuthGroup.classList.toggle("hidden", !plugin.requires_auth);
      if (connectModalApiKey) connectModalApiKey.value = "";
    }

    pluginConnectModal.classList.remove("hidden");
    pluginConnectModal.style.display = "flex";
  }

  function closeConnectModal() {
    if (pluginConnectModal) {
      pluginConnectModal.classList.add("hidden");
      pluginConnectModal.style.display = "none";
    }
  }

  if (closeConnectModalBtn) closeConnectModalBtn.addEventListener("click", closeConnectModal);
  if (cancelConnectModalBtn) cancelConnectModalBtn.addEventListener("click", closeConnectModal);
  if (pluginConnectModal) {
    pluginConnectModal.addEventListener("click", (e) => {
      if (e.target === pluginConnectModal) closeConnectModal();
    });
  }

  if (confirmConnectPluginBtn) {
    confirmConnectPluginBtn.addEventListener("click", async () => {
      const pluginId = connectModalPluginId.value;
      if (!pluginId) return;

      const apiKey = connectModalApiKey ? connectModalApiKey.value.trim() : "";
      const config = apiKey ? { api_key: apiKey } : {};

      confirmConnectPluginBtn.disabled = true;
      confirmConnectPluginBtn.textContent = "Connecting...";

      try {
        const res = await fetch(`/api/plugins/${encodeURIComponent(pluginId)}/connect`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ config }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.error || "Could not connect plugin");
        }
        closeConnectModal();
        showToast(`Connected ${data.plugin?.name || pluginId} successfully! ✓`);
        await loadPluginsMarketplace();
      } catch (err) {
        alert(`Connection error: ${err.message}`);
      } finally {
        confirmConnectPluginBtn.disabled = false;
        confirmConnectPluginBtn.textContent = "Connect App";
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Manage Permissions & Sandbox Modal
  // ---------------------------------------------------------------------------
  function openManageModal(plugin) {
    if (!pluginManageModal) return;
    activeManagePlugin = plugin;

    if (manageModalIconBox) {
      manageModalIconBox.textContent = plugin.icon || "🔌";
      manageModalIconBox.style.background = plugin.icon_bg || "var(--accent-blue)";
    }
    if (manageModalTitle) manageModalTitle.textContent = plugin.name;
    if (manageModalVersion) manageModalVersion.textContent = `v${plugin.version || "1.0.0"} • Created by ${plugin.author || "Cloud AI"}`;

    if (manageModalStatusBadge) {
      if (plugin.is_enabled) {
        manageModalStatusBadge.className = "status-pill-mini active";
        manageModalStatusBadge.textContent = "🟢 Connected & Enabled";
      } else {
        manageModalStatusBadge.className = "status-pill-mini paused";
        manageModalStatusBadge.textContent = "⏸ Disabled";
      }
    }

    if (managePluginToggleEnabled) {
      managePluginToggleEnabled.checked = plugin.is_enabled;
    }
    if (managePluginToggleLabel) {
      managePluginToggleLabel.textContent = plugin.is_enabled ? "Plugin Enabled" : "Plugin Disabled";
    }

    // Populate Tab 1: Permissions
    renderManagePermissionsTab(plugin);

    // Populate Tab 2: Tools Schemas
    renderManageToolsTab(plugin);

    // Populate Tab 3: Sandbox
    renderManageSandboxTab(plugin);

    // Reset active modal tab to 'permissions'
    switchModalTab("permissions");

    pluginManageModal.classList.remove("hidden");
    pluginManageModal.style.display = "flex";
  }

  function closeManageModal() {
    if (pluginManageModal) {
      pluginManageModal.classList.add("hidden");
      pluginManageModal.style.display = "none";
    }
    activeManagePlugin = null;
  }

  if (closeManageModalBtn) closeManageModalBtn.addEventListener("click", closeManageModal);
  if (manageSaveCloseBtn) manageSaveCloseBtn.addEventListener("click", closeManageModal);
  if (pluginManageModal) {
    pluginManageModal.addEventListener("click", (e) => {
      if (e.target === pluginManageModal) closeManageModal();
    });
  }

  // Modal Tab Switching
  function switchModalTab(tabName) {
    document.querySelectorAll(".modal-tab-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.modalTab === tabName);
    });
    const tabPerm = document.getElementById("manageTabPermissions");
    const tabTools = document.getElementById("manageTabTools");
    const tabSandbox = document.getElementById("manageTabSandbox");

    if (tabPerm) tabPerm.classList.toggle("hidden", tabName !== "permissions");
    if (tabTools) tabTools.classList.toggle("hidden", tabName !== "tools");
    if (tabSandbox) tabSandbox.classList.toggle("hidden", tabName !== "sandbox");
  }

  document.querySelectorAll(".modal-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchModalTab(btn.dataset.modalTab));
  });

  // Render Permissions Tab
  function renderManagePermissionsTab(plugin) {
    if (!managePermissionsTogglesList) return;
    managePermissionsTogglesList.innerHTML = "";

    if (!plugin.permissions || plugin.permissions.length === 0) {
      managePermissionsTogglesList.innerHTML = `<div style="font-size: 13px; color: var(--text-muted); padding: 12px 0;">No configurable permissions for this app.</div>`;
      return;
    }

    plugin.permissions.forEach((perm) => {
      const row = document.createElement("div");
      row.className = "perm-toggle-row";
      row.innerHTML = `
        <div class="perm-toggle-info">
          <div class="perm-toggle-title">${escapeHtml(perm.name)}</div>
          <div class="perm-toggle-desc">${escapeHtml(perm.description)}</div>
        </div>
        <label class="toggle-switch-wrap">
          <input type="checkbox" class="perm-checkbox" data-perm-id="${perm.id}" ${perm.enabled ? "checked" : ""} />
          <span class="toggle-slider"></span>
        </label>
      `;

      const checkbox = row.querySelector(".perm-checkbox");
      if (checkbox) {
        checkbox.addEventListener("change", async (e) => {
          const permId = e.target.dataset.permId;
          const isChecked = e.target.checked;
          try {
            const res = await fetch(`/api/plugins/${encodeURIComponent(plugin.id)}/permissions`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ permissions: { [permId]: isChecked } }),
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.error || "Update failed");
            showToast(`Permission updated for ${plugin.name} ⚙`);
            await loadPluginsMarketplace();
          } catch (err) {
            e.target.checked = !isChecked; // Revert
            alert(`Error updating permission: ${err.message}`);
          }
        });
      }

      managePermissionsTogglesList.appendChild(row);
    });
  }

  // Render Tools Schema Tab
  function renderManageToolsTab(plugin) {
    if (!manageToolsSchemaList) return;
    manageToolsSchemaList.innerHTML = "";

    if (!plugin.tools || plugin.tools.length === 0) {
      manageToolsSchemaList.innerHTML = `<div style="font-size: 13px; color: var(--text-muted); padding: 12px 0;">No tools exposed.</div>`;
      return;
    }

    plugin.tools.forEach((tool) => {
      const card = document.createElement("div");
      card.className = "tool-schema-card";
      const paramsObj = tool.parameters?.properties || {};
      const requiredList = tool.parameters?.required || [];
      const paramKeys = Object.keys(paramsObj);

      const paramsHtml = paramKeys.length > 0
        ? paramKeys.map((pk) => {
            const p = paramsObj[pk];
            const isReq = requiredList.includes(pk) ? `<span style="color: #ef4444;">*required</span>` : `<span style="color: var(--text-muted);">optional</span>`;
            return `• <strong>${escapeHtml(pk)}</strong> (<em>${p.type || "string"}</em>, ${isReq}): ${escapeHtml(p.description || "")}`;
          }).join("<br/>")
        : `<em>No parameters required.</em>`;

      card.innerHTML = `
        <div class="tool-name-code">⚡ ${escapeHtml(tool.name)}()</div>
        <div class="tool-desc-text">${escapeHtml(tool.description)}</div>
        <div class="tool-params-preview" style="background: var(--bg-sidebar-hover); padding: 8px 10px; border-radius: 6px; margin-top: 4px;">
          ${paramsHtml}
        </div>
      `;
      manageToolsSchemaList.appendChild(card);
    });
  }

  // Render Sandbox Tab
  function renderManageSandboxTab(plugin) {
    if (!sandboxToolSelect) return;
    sandboxToolSelect.innerHTML = "";

    if (!plugin.tools || plugin.tools.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No tools available";
      sandboxToolSelect.appendChild(opt);
      if (sandboxParamsInput) sandboxParamsInput.value = "{}";
      return;
    }

    plugin.tools.forEach((tool, idx) => {
      const opt = document.createElement("option");
      opt.value = tool.name;
      opt.textContent = `${tool.name} - ${tool.description.substring(0, 45)}...`;
      sandboxToolSelect.appendChild(opt);
    });

    // Populate initial sample params
    updateSandboxDefaultParams(plugin, plugin.tools[0]);

    sandboxToolSelect.onchange = () => {
      const selectedName = sandboxToolSelect.value;
      const tool = plugin.tools.find((t) => t.name === selectedName);
      if (tool) updateSandboxDefaultParams(plugin, tool);
    };
  }

  function updateSandboxDefaultParams(plugin, tool) {
    if (!sandboxParamsInput || !tool) return;
    const sample = {};
    const props = tool.parameters?.properties || {};
    for (const [k, p] of Object.entries(props)) {
      if (p.type === "number" || p.type === "integer") {
        sample[k] = p.default !== undefined ? p.default : 100;
      } else if (p.type === "array") {
        sample[k] = [10, 20, 30, 40, 50];
      } else if (p.type === "boolean") {
        sample[k] = true;
      } else {
        if (k === "expression") sample[k] = "45 * 38 + sqrt(144)";
        else if (k === "query") sample[k] = "AI latest breakthroughs 2026";
        else if (k === "from_unit") sample[k] = "km";
        else if (k === "to_unit") sample[k] = "mi";
        else if (k === "file_name") sample[k] = "report.pdf";
        else sample[k] = p.default || "example";
      }
    }
    sandboxParamsInput.value = JSON.stringify(sample, null, 2);
  }

  if (runSandboxToolBtn) {
    runSandboxToolBtn.addEventListener("click", async () => {
      if (!activeManagePlugin) return;
      const toolName = sandboxToolSelect.value;
      if (!toolName) return;

      let params = {};
      try {
        const raw = sandboxParamsInput.value.trim();
        if (raw) params = JSON.parse(raw);
      } catch (e) {
        alert("Invalid JSON format in arguments field. Please verify formatting.");
        return;
      }

      runSandboxToolBtn.disabled = true;
      runSandboxToolBtn.textContent = "Executing...";

      try {
        const res = await fetch(`/api/plugins/${encodeURIComponent(activeManagePlugin.id)}/execute`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tool_name: toolName, params }),
        });
        const data = await res.json();
        if (sandboxOutputArea && sandboxOutputPre) {
          sandboxOutputArea.classList.remove("hidden");
          sandboxOutputPre.textContent = JSON.stringify(data, null, 2);
          if (sandboxDurationBadge) {
            sandboxDurationBadge.textContent = `${data.duration_ms || 0} ms`;
          }
        }
      } catch (err) {
        if (sandboxOutputArea && sandboxOutputPre) {
          sandboxOutputArea.classList.remove("hidden");
          sandboxOutputPre.textContent = `Execution Error: ${err.message}`;
        }
      } finally {
        runSandboxToolBtn.disabled = false;
        runSandboxToolBtn.textContent = "▶ Execute Tool";
      }
    });
  }

  // Manage Enable/Disable Switch
  if (managePluginToggleEnabled) {
    managePluginToggleEnabled.addEventListener("change", async (e) => {
      if (!activeManagePlugin) return;
      const isEnabled = e.target.checked;
      const endpoint = isEnabled ? "enable" : "disable";

      try {
        const res = await fetch(`/api/plugins/${encodeURIComponent(activeManagePlugin.id)}/${endpoint}`, {
          method: "POST",
        });
        const data = await res.json();
        if (!res.ok || !data.success) throw new Error(data.error || "Toggle failed");

        if (managePluginToggleLabel) {
          managePluginToggleLabel.textContent = isEnabled ? "Plugin Enabled" : "Plugin Disabled";
        }
        if (manageModalStatusBadge) {
          if (isEnabled) {
            manageModalStatusBadge.className = "status-pill-mini active";
            manageModalStatusBadge.textContent = "🟢 Connected & Enabled";
          } else {
            manageModalStatusBadge.className = "status-pill-mini paused";
            manageModalStatusBadge.textContent = "⏸ Disabled";
          }
        }
        showToast(`${activeManagePlugin.name} ${isEnabled ? "enabled" : "disabled"} ⚡`);
        await loadPluginsMarketplace();
      } catch (err) {
        e.target.checked = !isEnabled;
        alert(`Failed to toggle plugin: ${err.message}`);
      }
    });
  }

  // Manage Disconnect Button
  if (manageDisconnectBtn) {
    manageDisconnectBtn.addEventListener("click", () => {
      if (!activeManagePlugin) return;
      handleDisconnectPlugin(activeManagePlugin.id, activeManagePlugin.name);
    });
  }

  async function handleDisconnectPlugin(pluginId, pluginName) {
    if (!confirm(`Are you sure you want to disconnect "${pluginName}"? This will disable its capabilities in chat.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/plugins/${encodeURIComponent(pluginId)}/disconnect`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || "Disconnect failed");

      closeManageModal();
      showToast(`Disconnected ${pluginName} ✕`);
      await loadPluginsMarketplace();
    } catch (err) {
      alert(`Disconnect error: ${err.message}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Plugin Activity & Execution Logs Modal
  // ---------------------------------------------------------------------------
  function openPluginLogsModal() {
    if (!pluginLogsModal) return;
    loadPluginLogs();
    pluginLogsModal.classList.remove("hidden");
    pluginLogsModal.style.display = "flex";
  }

  function closePluginLogsModal() {
    if (pluginLogsModal) {
      pluginLogsModal.classList.add("hidden");
      pluginLogsModal.style.display = "none";
    }
  }

  if (openPluginLogsBtn) openPluginLogsBtn.addEventListener("click", openPluginLogsModal);
  if (closePluginLogsModalBtn) closePluginLogsModalBtn.addEventListener("click", closePluginLogsModal);
  if (pluginLogsModal) {
    pluginLogsModal.addEventListener("click", (e) => {
      if (e.target === pluginLogsModal) closePluginLogsModal();
    });
  }

  async function loadPluginLogs() {
    if (!pluginLogsTableBody) return;
    pluginLogsTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--text-muted);">Loading logs... ⏳</td></tr>`;

    const pluginId = logsPluginFilterSelect ? logsPluginFilterSelect.value : "";
    const status = logsStatusFilterSelect ? logsStatusFilterSelect.value : "";

    try {
      const params = new URLSearchParams();
      if (pluginId) params.set("plugin_id", pluginId);
      if (status && status !== "all") params.set("status", status);

      const res = await fetch(`/api/plugins/logs?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to fetch logs");
      const data = await res.json();
      const logs = data.logs || [];

      pluginLogsTableBody.innerHTML = "";
      if (logs.length === 0) {
        if (logsEmptyNotice) logsEmptyNotice.classList.remove("hidden");
        return;
      }

      if (logsEmptyNotice) logsEmptyNotice.classList.add("hidden");

      logs.forEach((log) => {
        const tr = document.createElement("tr");
        const dateStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "--";
        const statusClass = log.status === "success" ? "success" : log.status === "blocked" ? "blocked" : "error";
        const summaryText = log.output_summary || log.error_message || log.status;

        tr.innerHTML = `
          <td style="font-family: var(--font-mono, monospace); font-size: 11.5px;">${escapeHtml(dateStr)}</td>
          <td><strong>${escapeHtml(log.plugin_name || log.plugin_id)}</strong></td>
          <td><code>${escapeHtml(log.action)}</code></td>
          <td><span class="status-badge-table ${statusClass}">${escapeHtml(log.status.toUpperCase())}</span></td>
          <td style="font-family: var(--font-mono, monospace);">${log.duration_ms || 0} ms</td>
          <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(summaryText)}">
            ${escapeHtml(summaryText)}
          </td>
        `;
        pluginLogsTableBody.appendChild(tr);
      });
    } catch (err) {
      pluginLogsTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: #ef4444;">Error loading logs: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  if (refreshPluginLogsBtn) refreshPluginLogsBtn.addEventListener("click", loadPluginLogs);
  if (logsPluginFilterSelect) logsPluginFilterSelect.addEventListener("change", loadPluginLogs);
  if (logsStatusFilterSelect) logsStatusFilterSelect.addEventListener("change", loadPluginLogs);

  if (clearPluginLogsBtn) {
    clearPluginLogsBtn.addEventListener("click", async () => {
      if (!confirm("Clear all recorded plugin telemetry and activity logs?")) return;
      try {
        const res = await fetch("/api/plugins/logs", { method: "DELETE" });
        const data = await res.json();
        showToast(data.message || "Logs cleared ✕");
        loadPluginLogs();
      } catch (err) {
        alert(`Failed to clear logs: ${err.message}`);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Initialization & Route Parsing
  // ---------------------------------------------------------------------------
  renderSidebar();
  loadActiveChat();

  // If URL hash or path requests translation, scheduled, or plugins view directly
  if (window.location.pathname.includes("/translation") || window.location.hash === "#translation") {
    switchToView("translation");
  } else if (window.location.pathname.includes("/scheduled") || window.location.hash === "#scheduled") {
    switchToView("scheduled");
  } else if (window.location.pathname.includes("/plugins") || window.location.hash === "#plugins") {
    switchToView("plugins");
  }
});


