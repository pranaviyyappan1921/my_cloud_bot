/**
 * Cloud AI Chatbot - Full Interactivity Controller
 * 
 * Features:
 * - Stores ONLY user-created conversations from this Cloud AI Chatbot in localStorage.
 * - Zero hard-coded, sample, or external seed conversations.
 * - Clears any legacy mock/seed conversation data from localStorage on load.
 * - Left Sidebar with Pinned & Previous Chats sections.
 * - + New Chat starts a fresh empty conversation.
 * - Clicking a Previous Chat restores its messages inside the existing page.
 * - Pin/Unpin, Rename, and Delete for conversations created in this chatbot.
 * - Share Button with Copy Conversation and Copy Link options.
 * - 3 Interactive Action Buttons below every AI response:
 *     🔊 Read Aloud (Browser speech synthesis with Stop Reading toggle)
 *     📋 Copy (Clean response text without HTML artifacts + Copied state)
 *     🔄 Try Again (Regenerate answer with duplicate request prevention)
 * - File Attachment Preview & Multimodal Support (PDF, TXT, DOCX, Images).
 * - Enter-to-send and Shift+Enter for new lines.
 * - Markdown Rendering with syntax-highlighted code blocks & code copy.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const messagesEl = document.getElementById("messages");
  const emptyStateEl = document.getElementById("emptyState");
  const composerForm = document.getElementById("composerForm");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const attachBtn = document.getElementById("attachBtn");
  const fileInput = document.getElementById("fileInput");
  const filePreview = document.getElementById("filePreview");
  const filePreviewIcon = document.getElementById("filePreviewIcon");
  const filePreviewName = document.getElementById("filePreviewName");
  const filePreviewSize = document.getElementById("filePreviewSize");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const newChatBtn = document.getElementById("newChatBtn");
  const mobileNewChatBtn = document.getElementById("mobileNewChatBtn");
  const mobileSidebarToggle = document.getElementById("mobileSidebarToggle");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const pinnedChatList = document.getElementById("pinnedChatList");
  const recentChatList = document.getElementById("recentChatList");
  const pinnedCountEl = document.getElementById("pinnedCount");
  const recentCountEl = document.getElementById("recentCount");
  const shareBtn = document.getElementById("shareBtn");
  const shareDropdownMenu = document.getElementById("shareDropdownMenu");
  const shareCopyTranscriptBtn = document.getElementById("shareCopyTranscriptBtn");
  const shareCopyLinkBtn = document.getElementById("shareCopyLinkBtn");
  const headerMenuBtn = document.getElementById("headerMenuBtn");
  const headerDropdownMenu = document.getElementById("headerDropdownMenu");
  const headerClearBtn = document.getElementById("headerClearBtn");
  const headerPinBtn = document.getElementById("headerPinBtn");
  const headerViewFilesBtn = document.getElementById("headerViewFilesBtn");
  const headerDeleteBtn = document.getElementById("headerDeleteBtn");
  const toastNotification = document.getElementById("toastNotification");
  const contextMenu = document.getElementById("chatItemContextMenu");
  const ctxPinBtn = document.getElementById("ctxPinBtn");
  const ctxRenameBtn = document.getElementById("ctxRenameBtn");
  const ctxArchiveBtn = document.getElementById("ctxArchiveBtn");
  const ctxDeleteBtn = document.getElementById("ctxDeleteBtn");

  const modelMenuBtn = document.getElementById("modelMenuBtn");
  const modelMenuLabel = document.getElementById("modelMenuLabel");
  const modelPopoverMenu = document.getElementById("modelPopoverMenu");
  const micBtn = document.getElementById("micBtn");
  const themeToggleBtn = document.getElementById("themeToggleBtn");

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

  function updateModelButtonLabel() {
    if (!modelMenuLabel) return;
    const mName = MODEL_NAMES[selectedModel] || "Gemini 3.7 Flash";
    const eName = EFFORT_LABELS[selectedEffort] || "Medium";
    modelMenuLabel.textContent = `${mName} ${eName}`;

    // Update active indicators inside the popover menu
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

  // Initialize UI label and active state
  updateModelButtonLabel();

  // Toggle model popover
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

  // Handle clicking model entries and effort options
  if (modelPopoverMenu) {
    modelPopoverMenu.querySelectorAll(".model-entry").forEach((entry) => {
      const modelId = entry.dataset.model;

      // Clicking the main model entry selects that model with its current effort
      entry.addEventListener("click", (e) => {
        if (e.target.closest(".effort-option")) return;
        selectedModel = modelId;
        localStorage.setItem(MODEL_STORAGE_KEY, selectedModel);
        updateModelButtonLabel();
        modelPopoverMenu.classList.add("hidden");
        if (modelMenuBtn) modelMenuBtn.classList.remove("active");
        showToast(`Model set to ${MODEL_NAMES[selectedModel]} (${EFFORT_LABELS[selectedEffort]}) ✦`);
      });

      // Clicking an effort option inside the flyout
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
  let speechRecognizer = null;
  let isRecordingVoice = false;

  const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      if (!SpeechRecognitionAPI) {
        showToast("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
        return;
      }

      if (isRecordingVoice) {
        stopVoiceRecording();
      } else {
        startVoiceRecording();
      }
    });
  }

  function startVoiceRecording() {
    try {
      speechRecognizer = new SpeechRecognitionAPI();
      speechRecognizer.continuous = true;
      speechRecognizer.interimResults = true;
      speechRecognizer.lang = "en-US";

      let initialText = messageInput.value;
      if (initialText && !initialText.endsWith(" ")) initialText += " ";

      speechRecognizer.onstart = () => {
        isRecordingVoice = true;
        micBtn.classList.add("listening");
        micBtn.title = "Listening... Click to stop";
        showToast("Listening... Speak into your microphone 🎙️");
      };

      speechRecognizer.onresult = (event) => {
        let transcript = "";
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        messageInput.value = initialText + transcript;
        adjustTextareaHeight();
      };

      speechRecognizer.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        if (event.error === "not-allowed") {
          showToast("Microphone access denied. Please allow microphone permissions.");
        } else if (event.error !== "no-speech") {
          showToast(`Speech recognition: ${event.error}`);
        }
        stopVoiceRecording();
      };

      speechRecognizer.onend = () => {
        stopVoiceRecording();
      };

      speechRecognizer.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      stopVoiceRecording();
      showToast("Could not start speech recognition.");
    }
  }

  function stopVoiceRecording() {
    isRecordingVoice = false;
    if (micBtn) {
      micBtn.classList.remove("listening");
      micBtn.title = "Speech to text (Click to talk)";
    }
    if (speechRecognizer) {
      try {
        speechRecognizer.stop();
      } catch (e) {}
      speechRecognizer = null;
    }
  }

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

  // Load saved theme or default to light
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

  let selectedFile = null;
  let isSending = false;
  let activeChatId = null;
  let contextTargetChatId = null;
  let activeSpeechUtterance = null;
  let activeSpeechBtn = null;

  // ---------------------------------------------------------------------------
  // Session Persistence Helpers (LocalStorage)
  // Contains ONLY conversations created inside this Cloud AI Chatbot
  // ---------------------------------------------------------------------------
  const STORAGE_KEY = "cloud_ai_chatbot_user_conversations";

  function loadSessions() {
    // Purge any old/legacy keys containing sample or external mock data
    try {
      localStorage.removeItem("cloud_chatbot_sessions");
      localStorage.removeItem("cloud_chatbot_sessions_v2");
    } catch (e) {
      console.warn("Could not clear legacy keys", e);
    }

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          return parsed;
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

  // Load purely user-created sessions (empty array if brand new)
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
          } catch (e) {
            console.error(e);
          }
        }
        return code;
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Initialize UI & Session State
  // ---------------------------------------------------------------------------
  renderSidebar();
  loadActiveChat();

  // ---------------------------------------------------------------------------
  // Sidebar Rendering (Pinned & Previous Chats)
  // ---------------------------------------------------------------------------
  function renderSidebar() {
    pinnedChatList.innerHTML = "";
    recentChatList.innerHTML = "";

    const pinned = sessions.filter((s) => s.pinned);
    const recent = sessions.filter((s) => !s.pinned);

    if (pinnedCountEl) pinnedCountEl.textContent = pinned.length;
    if (recentCountEl) recentCountEl.textContent = recent.length;

    if (pinned.length === 0) {
      const emptyNotice = document.createElement("div");
      emptyNotice.className = "empty-section-notice";
      emptyNotice.textContent = "No pinned chats yet";
      pinnedChatList.appendChild(emptyNotice);
    } else {
      pinned.forEach((chat) => pinnedChatList.appendChild(createChatItemEl(chat)));
    }

    if (recent.length === 0) {
      const emptyNotice = document.createElement("div");
      emptyNotice.className = "empty-section-notice";
      emptyNotice.textContent = "No previous chats yet";
      recentChatList.appendChild(emptyNotice);
    } else {
      recent.forEach((chat) => recentChatList.appendChild(createChatItemEl(chat)));
    }
  }

  function createChatItemEl(chat) {
    const item = document.createElement("div");
    item.className = `chat-item ${chat.id === activeChatId ? "active" : ""}`;
    item.dataset.id = chat.id;

    const icon = chat.pinned ? "📌" : "💬";

    item.innerHTML = `
      <div class="chat-item-left">
        <span class="chat-icon">${icon}</span>
        <span class="chat-title-text" title="${escapeHtml(chat.title)}">${escapeHtml(chat.title)}</span>
      </div>
      <div class="chat-item-actions">
        <button class="chat-item-pin-btn" title="${chat.pinned ? "Unpin chat" : "Pin to top"}">
          ${chat.pinned ? "✖" : "📌"}
        </button>
        <button class="chat-item-menu-btn" title="Chat options">•••</button>
      </div>
    `;

    // Click chat item to restore conversation right inside this page
    item.addEventListener("click", (e) => {
      if (e.target.closest(".chat-item-actions")) return;
      selectChat(chat.id);
    });

    // Quick Pin/Unpin button
    const pinBtn = item.querySelector(".chat-item-pin-btn");
    pinBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      chat.pinned = !chat.pinned;
      saveSessions();
      renderSidebar();
      showToast(chat.pinned ? `Pinned "${chat.title}" 📌` : `Unpinned "${chat.title}"`);
    });

    // 3-dot context menu click
    const menuBtn = item.querySelector(".chat-item-menu-btn");
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openContextMenu(e, chat.id);
    });

    return item;
  }

  function selectChat(id) {
    if (activeChatId === id) return;
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
    stopSpeech();

    // If current chat is already fresh and empty, just focus input
    const current = getActiveSession();
    if (current && current.messages.length === 0) {
      clearAttachment();
      messageInput.value = "";
      messageInput.focus();
      closeMobileSidebar();
      return;
    }

    const newId = "chat_" + Date.now();
    const newSession = {
      id: newId,
      title: "New chat",
      pinned: false,
      createdAt: Date.now(),
      messages: []
    };

    sessions.unshift(newSession);
    activeChatId = newId;
    saveSessions();
    renderSidebar();
    loadActiveChat();

    // Reset server-side session history
    fetch("/api/clear", { method: "POST" }).catch(() => {});

    clearAttachment();
    messageInput.value = "";
    messageInput.style.height = "auto";
    messageInput.focus();
    closeMobileSidebar();
    showToast("Started a new conversation");
  }

  if (newChatBtn) newChatBtn.addEventListener("click", createNewChat);
  if (mobileNewChatBtn) mobileNewChatBtn.addEventListener("click", createNewChat);

  // ---------------------------------------------------------------------------
  // Load & Render Active Conversation inside existing page
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
          appendUserMessageDOM(msg.text, msg.fileName);
        } else {
          // Preceding user prompt for Try Again
          let promptText = "";
          let attachedFileName = null;
          for (let i = idx - 1; i >= 0; i--) {
            if (session.messages[i].role === "user") {
              promptText = session.messages[i].text;
              attachedFileName = session.messages[i].fileName;
              break;
            }
          }
          appendAiMessageDOM(msg.text, msg.isError, promptText, attachedFileName, idx);
        }
      });
    }
    scrollToBottom();
  }

  // ---------------------------------------------------------------------------
  // Context Menu Handling (Pin, Rename, Delete)
  // ---------------------------------------------------------------------------
  function openContextMenu(e, chatId) {
    contextTargetChatId = chatId;
    const targetSession = sessions.find((s) => s.id === chatId);
    if (!targetSession) return;

    ctxPinBtn.textContent = targetSession.pinned ? "📌 Unpin chat" : "📌 Pin to top";

    const rect = e.target.getBoundingClientRect();
    contextMenu.style.top = `${rect.bottom + 4}px`;
    contextMenu.style.left = `${Math.min(rect.left, window.innerWidth - 170)}px`;
    contextMenu.classList.remove("hidden");
  }

  document.addEventListener("click", (e) => {
    if (contextMenu && !contextMenu.contains(e.target)) {
      contextMenu.classList.add("hidden");
    }
    if (headerDropdownMenu && !headerMenuBtn.contains(e.target) && !headerDropdownMenu.contains(e.target)) {
      headerDropdownMenu.classList.add("hidden");
    }
    if (shareDropdownMenu && !shareBtn.contains(e.target) && !shareDropdownMenu.contains(e.target)) {
      shareDropdownMenu.classList.add("hidden");
    }
    if (modelPopoverMenu && modelMenuBtn && !modelMenuBtn.contains(e.target) && !modelPopoverMenu.contains(e.target)) {
      modelPopoverMenu.classList.add("hidden");
      modelMenuBtn.classList.remove("active");
    }
  });

  ctxPinBtn.addEventListener("click", () => {
    const s = sessions.find((s) => s.id === contextTargetChatId);
    if (s) {
      s.pinned = !s.pinned;
      saveSessions();
      renderSidebar();
      showToast(s.pinned ? "Chat pinned to top 📌" : "Chat unpinned");
    }
    contextMenu.classList.add("hidden");
  });

  ctxRenameBtn.addEventListener("click", () => {
    const s = sessions.find((s) => s.id === contextTargetChatId);
    if (s) {
      const newTitle = prompt("Enter new title for this chat:", s.title);
      if (newTitle && newTitle.trim()) {
        s.title = newTitle.trim();
        saveSessions();
        renderSidebar();
        showToast("Chat renamed ✏️");
      }
    }
    contextMenu.classList.add("hidden");
  });

  ctxArchiveBtn.addEventListener("click", () => {
    showToast("Chat archived 📦");
    contextMenu.classList.add("hidden");
  });

  ctxDeleteBtn.addEventListener("click", () => {
    deleteChat(contextTargetChatId);
    contextMenu.classList.add("hidden");
  });

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

  // ---------------------------------------------------------------------------
  // Header Actions (Share Button & 3-Dot Dropdown)
  // ---------------------------------------------------------------------------
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

      const dateStr = new Date(session.createdAt || Date.now()).toLocaleDateString();
      let transcript = `=== Cloud AI Chatbot: ${session.title} ===\nDate: ${dateStr}\n\n`;

      session.messages.forEach((m) => {
        const sender = m.role === "user" ? "User" : "AI (Gemini Flash)";
        const fileInfo = m.fileName ? ` [Attached: ${m.fileName}]` : "";
        transcript += `[${sender}${fileInfo}]:\n${m.text}\n\n`;
      });

      navigator.clipboard.writeText(transcript.trim()).then(() => {
        showToast("Conversation copied to clipboard! 📋");
      }).catch(() => {
        showToast("Could not copy transcript to clipboard.");
      });

      shareDropdownMenu.classList.add("hidden");
    });
  }

  if (shareCopyLinkBtn) {
    shareCopyLinkBtn.addEventListener("click", () => {
      const shareUrl = `${window.location.origin}${window.location.pathname}#chat=${encodeURIComponent(activeChatId || "")}`;
      navigator.clipboard.writeText(shareUrl).then(() => {
        showToast("Shareable link copied to clipboard! 🔗");
      }).catch(() => {
        showToast("Could not copy link to clipboard.");
      });
      shareDropdownMenu.classList.add("hidden");
    });
  }

  if (headerMenuBtn) {
    headerMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      headerDropdownMenu.classList.toggle("hidden");
    });
  }

  if (headerClearBtn) {
    headerClearBtn.addEventListener("click", () => {
      const session = getActiveSession();
      if (session) {
        session.messages = [];
        saveSessions();
        loadActiveChat();
        fetch("/api/clear", { method: "POST" }).catch(() => {});
        showToast("Conversation cleared 🗑️");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerPinBtn) {
    headerPinBtn.addEventListener("click", () => {
      const session = getActiveSession();
      if (session) {
        session.pinned = !session.pinned;
        saveSessions();
        renderSidebar();
        showToast(session.pinned ? "Chat pinned 📌" : "Chat unpinned");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerViewFilesBtn) {
    headerViewFilesBtn.addEventListener("click", () => {
      const session = getActiveSession();
      const files = session ? session.messages.filter((m) => m.fileName).map((m) => m.fileName) : [];
      if (files.length > 0) {
        alert("Files in this chat:\n• " + files.join("\n• "));
      } else {
        showToast("No files uploaded in this chat yet.");
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  if (headerDeleteBtn) {
    headerDeleteBtn.addEventListener("click", () => {
      if (activeChatId) {
        deleteChat(activeChatId);
      }
      headerDropdownMenu.classList.add("hidden");
    });
  }

  // ---------------------------------------------------------------------------
  // 4 Interactive Example Cards
  // ---------------------------------------------------------------------------
  document.querySelectorAll(".example-card").forEach((card) => {
    card.addEventListener("click", () => {
      const prompt = card.getAttribute("data-prompt");
      if (prompt) {
        messageInput.value = prompt;
        adjustTextareaHeight();
        messageInput.focus();
      }
    });
  });

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

  // ---------------------------------------------------------------------------
  // File Attachment & Pre-send Preview
  // ---------------------------------------------------------------------------
  attachBtn.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    const maxSizeBytes = 10 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      alert(`The selected file is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max limit is 10 MB.`);
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
  });

  removeFileBtn.addEventListener("click", clearAttachment);

  function clearAttachment() {
    selectedFile = null;
    fileInput.value = "";
    filePreview.classList.add("hidden");
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    const kb = bytes / 1024;
    if (kb < 1024) return kb.toFixed(1) + " KB";
    return (kb / 1024).toFixed(1) + " MB";
  }

  // ---------------------------------------------------------------------------
  // Sending Message Turn (Saves directly to chatbot local storage)
  // ---------------------------------------------------------------------------
  composerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isSending) return;

    const text = messageInput.value.trim();
    if (!text && !selectedFile) return;

    emptyStateEl.style.display = "none";

    const attachedFileName = selectedFile ? selectedFile.name : null;
    const attachedFileObject = selectedFile;

    let session = getActiveSession();
    if (!session) {
      const newId = "chat_" + Date.now();
      session = {
        id: newId,
        title: "New chat",
        pinned: false,
        createdAt: Date.now(),
        messages: []
      };
      sessions.unshift(session);
      activeChatId = newId;
    }

    // Auto-title chat from user's first query
    if (session.messages.length === 0 || session.title === "New chat") {
      let rawTitle = text || (attachedFileName ? `File: ${attachedFileName}` : "New Chat");
      session.title = rawTitle.slice(0, 32) + (rawTitle.length > 32 ? "..." : "");
      renderSidebar();
    }

    const userDisplayText = text || "Analyzed attached file.";

    session.messages.push({
      role: "user",
      text: userDisplayText,
      fileName: attachedFileName,
      timestamp: Date.now()
    });
    saveSessions();

    // Render User Bubble
    appendUserMessageDOM(userDisplayText, attachedFileName);

    // Prepare FormData
    const formData = new FormData();
    if (text) formData.append("message", text);
    if (attachedFileObject) formData.append("file", attachedFileObject);
    formData.append("model", selectedModel);
    formData.append("effort", selectedEffort);

    // Pass rolling history so backend keeps thread context
    const rollingHistory = session.messages.slice(0, -1).map((m) => ({
      role: m.role === "user" ? "user" : "model",
      text: m.text
    }));
    formData.append("history", JSON.stringify(rollingHistory.slice(-20)));

    // Reset composer
    messageInput.value = "";
    messageInput.style.height = "auto";
    clearAttachment();

    setSending(true);
    const typingIndicator = appendTypingIndicatorDOM();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      typingIndicator.remove();

      if (!response.ok) {
        const errorMsg = data.error || `Server error (${response.status}).`;
        const aiIndex = session.messages.length;
        session.messages.push({ role: "ai", text: `⚠️ **Error:** ${errorMsg}`, isError: true, timestamp: Date.now() });
        appendAiMessageDOM(`⚠️ **Error:** ${errorMsg}`, true, userDisplayText, attachedFileName, aiIndex);
      } else {
        const reply = data.reply || "No response received.";
        const aiIndex = session.messages.length;
        session.messages.push({ role: "ai", text: reply, isError: false, timestamp: Date.now() });
        appendAiMessageDOM(reply, false, userDisplayText, attachedFileName, aiIndex);
      }
      saveSessions();
      renderSidebar();
    } catch (err) {
      console.error("Network error:", err);
      typingIndicator.remove();
      const netMsg = "⚠️ **Network Error:** Could not connect to the backend server.";
      const aiIndex = session.messages.length;
      session.messages.push({ role: "ai", text: netMsg, isError: true, timestamp: Date.now() });
      appendAiMessageDOM(netMsg, true, userDisplayText, attachedFileName, aiIndex);
      saveSessions();
    } finally {
      setSending(false);
      messageInput.focus();
    }
  });

  // ---------------------------------------------------------------------------
  // DOM Render Helpers: User Message
  // ---------------------------------------------------------------------------
  function appendUserMessageDOM(text, fileName) {
    const row = document.createElement("div");
    row.className = "msg-row user";

    let fileChip = "";
    if (fileName) {
      fileChip = `<div class="msg-file-chip">📎 ${escapeHtml(fileName)}</div><br/>`;
    }

    row.innerHTML = `
      <div class="avatar user">🧑</div>
      <div class="msg-bubble">
        ${fileChip}${escapeHtml(text)}
      </div>
    `;

    messagesEl.appendChild(row);
    scrollToBottom();
  }

  // ---------------------------------------------------------------------------
  // DOM Render Helpers: AI Message with 3 Action Buttons
  // ---------------------------------------------------------------------------
  function appendAiMessageDOM(markdownContent, isError = false, promptText = "", attachedFileName = null, msgIndex = -1) {
    const row = document.createElement("div");
    row.className = `msg-row ai ${isError ? "error" : ""}`;

    const contentWrap = document.createElement("div");
    contentWrap.className = "msg-content-wrap";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";

    if (isError) {
      bubble.innerHTML = `<div class="markdown-body" style="color: #ef4444;">${renderMarkdown(markdownContent)}</div>`;
    } else {
      bubble.innerHTML = `<div class="markdown-body">${renderMarkdown(markdownContent)}</div>`;
      attachCodeCopyButtons(bubble);
    }

    contentWrap.appendChild(bubble);

    // 3 Interactive Action Buttons (🔊 Read Aloud, 📋 Copy, 🔄 Try Again)
    const actionsBar = createAiActionsBar(markdownContent, promptText, attachedFileName, row, bubble, msgIndex);
    contentWrap.appendChild(actionsBar);

    row.innerHTML = `<div class="avatar ai">✦</div>`;
    row.appendChild(contentWrap);

    messagesEl.appendChild(row);
    scrollToBottom();
  }

  // ---------------------------------------------------------------------------
  // Action Buttons Factory (🔊 Read Aloud, 📋 Copy, 🔄 Try Again)
  // ---------------------------------------------------------------------------
  function createAiActionsBar(aiText, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex) {
    const bar = document.createElement("div");
    bar.className = "ai-actions-bar";

    // 1. 🔊 Read Aloud Button
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

    readBtn.addEventListener("click", () => {
      toggleSpeech(readBtn, aiText);
    });

    // 2. 📋 Copy Button
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

    copyBtn.addEventListener("click", () => {
      copyCleanAiText(copyBtn, aiText, bubbleEl);
    });

    // 3. 🔄 Try Again Button
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
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="6" width="12" height="12" rx="2"></rect>
        </svg>
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
  // 📋 Clean AI Text Copy to Clipboard
  // ---------------------------------------------------------------------------
  function copyCleanAiText(btn, rawText, bubbleEl) {
    let textToCopy = rawText;

    if (bubbleEl) {
      const clone = bubbleEl.cloneNode(true);
      clone.querySelectorAll(".code-header").forEach((el) => el.remove());
      textToCopy = clone.innerText.trim();
    }

    if (!textToCopy) {
      textToCopy = rawText || "";
    }

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
    }).catch((err) => {
      console.error("Copy failed:", err);
      showToast("Failed to copy response.");
    });
  }

  // ---------------------------------------------------------------------------
  // 🔄 Try Again: Regenerate AI Response
  // ---------------------------------------------------------------------------
  async function regenerateAiResponse(retryBtn, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex) {
    if (isSending) return;

    let session = getActiveSession();
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
      showToast("Cannot determine original prompt for regeneration.");
      return;
    }

    setSending(true);
    retryBtn.classList.add("loading");
    retryBtn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
      </svg>
      <span>Regenerating...</span>
    `;

    const typingIndicator = appendTypingIndicatorDOM();

    const formData = new FormData();
    formData.append("message", promptText);
    formData.append("model", selectedModel);
    formData.append("effort", selectedEffort);

    const targetIdx = msgIndex >= 0 ? msgIndex : session.messages.length - 1;
    const historyTurns = session.messages.slice(0, targetIdx).map((m) => ({
      role: m.role === "user" ? "user" : "model",
      text: m.text
    }));
    formData.append("history", JSON.stringify(historyTurns.slice(-20)));

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        body: formData
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
        showToast("Regeneration encountered an error.");
      } else {
        const newReply = data.reply || "No response received.";
        bubbleEl.innerHTML = `<div class="markdown-body">${renderMarkdown(newReply)}</div>`;
        attachCodeCopyButtons(bubbleEl);

        if (msgIndex >= 0 && session.messages[msgIndex]) {
          session.messages[msgIndex].text = newReply;
          session.messages[msgIndex].isError = false;
          saveSessions();
        } else {
          for (let i = session.messages.length - 1; i >= 0; i--) {
            if (session.messages[i].role === "ai") {
              session.messages[i].text = newReply;
              session.messages[i].isError = false;
              saveSessions();
              break;
            }
          }
        }

        const parentWrap = bubbleEl.parentElement;
        const oldBar = parentWrap.querySelector(".ai-actions-bar");
        if (oldBar) oldBar.remove();
        const newBar = createAiActionsBar(newReply, promptText, attachedFileName, msgRowEl, bubbleEl, msgIndex);
        parentWrap.appendChild(newBar);

        showToast("Response regenerated! 🔄");
      }
    } catch (err) {
      console.error("Regeneration error:", err);
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
      setSending(false);
      messageInput.focus();
    }
  }

  // ---------------------------------------------------------------------------
  // Typing Indicator DOM
  // ---------------------------------------------------------------------------
  function appendTypingIndicatorDOM() {
    const row = document.createElement("div");
    row.className = "msg-row ai";
    row.innerHTML = `
      <div class="avatar ai">✦</div>
      <div class="msg-bubble">
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;
    messagesEl.appendChild(row);
    scrollToBottom();
    return row;
  }

  // ---------------------------------------------------------------------------
  // Markdown Rendering & Code Block Copy Buttons
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

  function attachCodeCopyButtons(container) {
    const preBlocks = container.querySelectorAll("pre");
    preBlocks.forEach((pre) => {
      const code = pre.querySelector("code");
      if (!code) return;

      const header = document.createElement("div");
      header.className = "code-header";
      header.innerHTML = `
        <span>Code</span>
        <button class="btn-copy-code" title="Copy code">
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
  // Toast Notification
  // ---------------------------------------------------------------------------
  let toastTimer = null;
  function showToast(msg) {
    if (!toastNotification) return;
    clearTimeout(toastTimer);
    toastNotification.textContent = msg;
    toastNotification.classList.remove("hidden");
    toastTimer = setTimeout(() => {
      toastNotification.classList.add("hidden");
    }, 2500);
  }

  function setSending(state) {
    isSending = state;
    sendBtn.disabled = state;
    if (state) {
      document.querySelectorAll(".btn-ai-retry").forEach((b) => (b.disabled = true));
    } else {
      document.querySelectorAll(".btn-ai-retry").forEach((b) => (b.disabled = false));
    }
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
});
