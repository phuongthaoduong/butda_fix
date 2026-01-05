import { FormEvent, useState, useRef, useEffect } from "react";
import "./App.css";

type MessageRole = "assistant" | "user" | "error" | "loading";
type PageType = "login" | "chat";

interface ChatMessage {
  id: string;
  role: MessageRole;
  title?: string;
  text: string;
  timestamp: string;
  meta?: string;
}

const featureCards = [
  { icon: "📰", title: "Personalized News Digests" },
  { icon: "🤖", title: "AI-Powered Summaries" },
  { icon: "⚡", title: "Real-time Updates" },
  { icon: "🛡️", title: "Trusted Sources" }
];

const initialMessages: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    title: "Welcome to BUTDA!",
    text: "I'm your personal news assistant. Tell me what topics you're interested in, I'll curate a 3-minute feed. All the news you need.",
    timestamp: new Date().toISOString()
  }
];

const resolveApiBase = () => {
  if (import.meta.env.DEV) {
    return "";
  }
  return import.meta.env.VITE_API_URL || "";
};

const API_BASE = resolveApiBase();
const REQUIRE_API = !import.meta.env.DEV && !import.meta.env.VITE_API_URL;

const formatTimestamp = () =>
  new Date().toISOString();

const formatTimestampDisplay = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

const getAssetUrl = (path: string) => {
  return new URL(path, import.meta.url).href;
};

// Debug logger for development
const debugLog = (category: string, message: string, data?: unknown) => {
  const timestamp = new Date().toISOString();
  if (import.meta.env.DEV) {
    console.log(`[${timestamp}] [${category}]`, message, data || "");
  }
  // Store error details for display
  if (category === "ERROR") {
    const errorEvent = new CustomEvent("app-error", { detail: { message, data, timestamp } });
    window.dispatchEvent(errorEvent);
  }
};

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>("chat");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [userInput, setUserInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [cotMessages, setCotMessages] = useState<Array<{ stage: string; message?: string; details?: string; article_url?: string; domain?: string }>>([]);
  const [cotActive, setCotActive] = useState<{ url?: string; domain?: string; title?: string } | null>(null);
  const [cotCurrent, setCotCurrent] = useState<{ stage: string; message?: string } | null>(null);
  const [debugErrors, setDebugErrors] = useState<Array<{ message: string; data?: unknown; timestamp: string }>>([]);
  const [showDebug, setShowDebug] = useState(false);
  const [savedItems, setSavedItems] = useState<Array<ChatMessage>>([]);
  const [currentView, setCurrentView] = useState<"chat" | "savelist" | "settings">("chat");
  const [darkMode, setDarkMode] = useState(false);
  const [autoSave, setAutoSave] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [emailTime, setEmailTime] = useState("09:00");
  const [notificationEmail, setNotificationEmail] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);
  const [verifyingEmail, setVerifyingEmail] = useState(false);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState("");
  const [showSaveConfirm, setShowSaveConfirm] = useState(false);
  const [pendingEditItem, setPendingEditItem] = useState<ChatMessage | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileName, setProfileName] = useState("User");
  const [profileTopics, setProfileTopics] = useState("");
  const [editingProfileName, setEditingProfileName] = useState("User");
  const [editingProfileTopics, setEditingProfileTopics] = useState("");
  const eventSourceRef = useRef<EventSource | null>(null);
  const isSendingRef = useRef(false);

  // Apply dark mode to document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark-mode");
    } else {
      document.documentElement.classList.remove("dark-mode");
    }
  }, [darkMode]);

  // Auto-save assistant responses when enabled
  useEffect(() => {
    if (autoSave && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (
        lastMessage.role === "assistant" &&
        lastMessage.title === "Research Summary" &&
        !savedItems.some(item => item.id === lastMessage.id)
      ) {
        setSavedItems(prev => [...prev, lastMessage]);
      }
    }
  }, [messages, autoSave, savedItems]);

  // Listen for debug error events
  useEffect(() => {
    const handleErrors = (e: CustomEvent) => {
      setDebugErrors(prev => [...prev.slice(-9), e.detail]);
    };
    window.addEventListener("app-error", handleErrors as EventListener);
    return () => window.removeEventListener("app-error", handleErrors as EventListener);
  }, []);

  const escapeHtml = (s: string) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const renderMarkdownHtml = (input: string) => {
    let text = input.replace(/\r\n/g, "\n");

    text = text.replace(/```([\s\S]*?)```/g, (_, code) => {
      return `<pre><code>${escapeHtml(code)}</code></pre>`;
    });

    text = escapeHtml(text);

    text = text.replace(/^###\s?(.*)$/gm, "<h3>$1</h3>");
    text = text.replace(/^##\s?(.*)$/gm, "<h2>$1</h2>");
    text = text.replace(/^#\s?(.*)$/gm, "<h1>$1</h1>");

    text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/(^|[^*])\*(.*?)\*/g, "$1<em>$2</em>");
    text = text.replace(/(^|[^_])_(.*?)_/g, "$1<em>$2</em>");

    text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Handle markdown links - be more flexible with URL patterns
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, (m, label, url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    });

    const listBlockRegex = /(^|\n)(?:-\s+.*(?:\n-\s+.*)*)/g;
    text = text.replace(listBlockRegex, (block) => {
      const items = block
        .trim()
        .split(/\n/)
        .map((l) => l.replace(/^-\s+/, ""))
        .map((c) => `<li>${c}</li>`) // content already escaped above
        .join("");
      return `<ul>${items}</ul>`;
    });

    text = text.replace(/\n{2,}/g, "</p><p>");
    text = `<p>${text}</p>`;

    return text;
  };

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (email && password) {
      setCurrentPage("chat");
    }
  };

  const handleVerifyEmail = () => {
    if (notificationEmail && notificationEmail.includes("@")) {
      setVerifyingEmail(true);
      // Simulate email verification (in real app, this would call an API)
      setTimeout(() => {
        setEmailVerified(true);
        setVerifyingEmail(false);
      }, 2000);
    }
  };

  const stripHtml = (html: string): string => {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
  };

  const exportToWord = () => {
    // Create HTML content that Word can open
    let content = `
      <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word'>
      <head><meta charset='utf-8'><title>BUTDA SaveList</title></head>
      <body>
      <h1>BUTDA SaveList</h1>
      <p>Generated: ${new Date().toLocaleString()}</p>
      <hr/>
    `;

    savedItems.forEach((item, index) => {
      const date = new Date(item.timestamp).toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric"
      });
      const time = formatTimestampDisplay(item.timestamp);
      const plainText = stripHtml(renderMarkdownHtml(item.text));

      content += `
        <h2>${index + 1}. ${date}</h2>
        <p><i>${time}</i></p>
        <p>${plainText.replace(/\n/g, '<br>')}</p>
        <hr/>
      `;
    });

    content += `</body></html>`;

    // Create blob and download
    const blob = new Blob(['\ufeff', content], {
      type: 'application/msword'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `BUTDA_SaveList_${new Date().toISOString().split('T')[0]}.doc`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setShowExportModal(false);
  };

  const exportToPDF = () => {
    // Create printable content
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    let content = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>BUTDA SaveList</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
          h1 { color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 10px; }
          h2 { color: #4f46e5; margin-top: 30px; }
          .meta { color: #6b7280; font-size: 14px; }
          .content { line-height: 1.6; margin: 15px 0; white-space: pre-wrap; }
          hr { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }
          @media print { body { margin: 0; } }
        </style>
      </head>
      <body>
        <h1>BUTDA SaveList</h1>
        <p class="meta">Generated: ${new Date().toLocaleString()}</p>
        <hr/>
    `;

    savedItems.forEach((item, index) => {
      const date = new Date(item.timestamp).toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric"
      });
      const time = formatTimestampDisplay(item.timestamp);
      const plainText = stripHtml(renderMarkdownHtml(item.text));

      content += `
        <h2>${index + 1}. ${date}</h2>
        <p class="meta">${time}</p>
        <div class="content">${plainText}</div>
        <hr/>
      `;
    });

    content += `</body></html>`;

    printWindow.document.write(content);
    printWindow.document.close();

    // Wait for content to load, then print
    setTimeout(() => {
      printWindow.focus();
      printWindow.print();
      printWindow.close();
    }, 250);

    setShowExportModal(false);
  };

  const startEditProfile = () => {
    setEditingProfileName(profileName);
    setEditingProfileTopics(profileTopics);
    setIsEditingProfile(true);
  };

  const saveProfile = () => {
    setProfileName(editingProfileName);
    setProfileTopics(editingProfileTopics);
    setIsEditingProfile(false);
  };

  const cancelEditProfile = () => {
    setIsEditingProfile(false);
  };

  const toggleSave = (message: ChatMessage) => {
    const isSaved = savedItems.some(item => item.id === message.id);
    if (isSaved) {
      setSavedItems(prev => prev.filter(item => item.id !== message.id));
    } else {
      setSavedItems(prev => [...prev, message]);
    }
  };

  const isMessageSaved = (messageId: string) => {
    return savedItems.some(item => item.id === messageId);
  };

  const startEdit = (item: ChatMessage) => {
    setEditingItemId(item.id);
    setEditedContent(item.text);
  };

  const cancelEdit = () => {
    setEditingItemId(null);
    setEditedContent("");
  };

  const initiateSaveEdit = () => {
    setShowSaveConfirm(true);
  };

  const confirmSaveEdit = () => {
    if (pendingEditItem) {
      setSavedItems(prev =>
        prev.map(item =>
          item.id === pendingEditItem.id
            ? { ...item, text: editedContent }
            : item
        )
      );
    }
    setEditingItemId(null);
    setEditedContent("");
    setShowSaveConfirm(false);
    setPendingEditItem(null);
  };

  const cancelSaveEdit = () => {
    setShowSaveConfirm(false);
    setPendingEditItem(null);
  };

  const saveEdit = () => {
    const currentItem = savedItems.find(item => item.id === editingItemId);
    if (currentItem) {
      setPendingEditItem(currentItem);
      setShowSaveConfirm(true);
    }
  };

  const handleSend = async () => {
    const text = userInput.trim();
    if (!text) return;
    if (isSendingRef.current) return;
    isSendingRef.current = true;
    setIsSending(true);

    const timestamp = formatTimestamp();
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text,
      timestamp
    };

    const loadingId = `loading-${Date.now()}`;
    const loadingMessage: ChatMessage = {
      id: loadingId,
      role: "loading",
      text: "",
      timestamp: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setUserInput("");

    if (REQUIRE_API) {
      debugLog("ERROR", "Configuration Error: Missing VITE_API_URL", {
        isDev: import.meta.env.DEV,
        apiUrl: import.meta.env.VITE_API_URL,
        apiBase: API_BASE
      });
      const message: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "error",
        title: "Configuration Error",
        text: "Thiếu biến VITE_API_URL trong môi trường production.",
        timestamp: new Date().toISOString(),
        meta: `API_BASE: ${API_BASE || "(empty)"}`
      };
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.role !== "loading");
        return [...filtered, message];
      });
      setIsSending(false);
      isSendingRef.current = false;
      return;
    }

    const finalize = (message: ChatMessage) => {
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.role !== "loading");
        return [...filtered, message];
      });
    };

    // Start streaming (CoT Phase 1)
    setCotMessages([]);
    setCotCurrent(null);
    setIsStreaming(true);

    // Build stream URL
    const encoded = encodeURIComponent(text);
    const base = resolveApiBase();
    const streamPath = base ? `${base}/api/research/stream?query=${encoded}` : `/api/research/stream?query=${encoded}`;
    const streamUrl = new URL(streamPath, window.location.origin).toString();

    debugLog("STREAM", "Connecting to stream", { streamUrl: streamUrl.replace(encoded, "QUERY_ENCODED") });

    // Close any existing connection
    if (eventSourceRef.current) {
      debugLog("STREAM", "Closing existing connection");
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    try {
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        debugLog("STREAM", "Connection opened", { readyState: es.readyState });
      };

      const stageCopy: Record<string, string> = {
        starting: "🔍 Preparing",
        loading: "⏳ Loading",
        searching: "🔎 Searching",
        reading: "📖 Reading",
        thinking: "🧠 Analyzing",
        writing: "✍️ Summarizing",
      };

      const getDomain = (u?: string) => {
        if (!u) return undefined;
        try {
          const host = new URL(u).hostname;
          return host.replace(/^www\./, "");
        } catch {
          return undefined;
        }
      };

      const handleProgress = (ev: MessageEvent) => {
        try {
          const raw = JSON.parse(ev.data);
          const stage = typeof raw.stage === "string" ? raw.stage : "";
          const msg = raw.message && typeof raw.message === "string" ? raw.message : undefined;
          const details = raw.details && typeof raw.details === "string" ? raw.details : undefined;
          const articleUrl = raw.article_url && typeof raw.article_url === "string" ? raw.article_url : undefined;
          const domain = getDomain(articleUrl);

          debugLog("PROGRESS", `Stage: ${stage}`, { stage, msg, details, articleUrl, domain });

          // Friendly copy; show only current stage
          const label = stageCopy[stage] || "Working";
          setCotCurrent({ stage: label, message: msg });

          setCotMessages(prev => {
            const nextItem = { stage: label, message: msg, details, article_url: articleUrl, domain };
            const last = prev[prev.length - 1];
            if (last && last.stage === nextItem.stage && last.article_url === nextItem.article_url && last.details === nextItem.details) {
              return prev;
            }
            return [...prev, nextItem];
          });
          if (articleUrl && label === "Reading") {
            setCotActive({ url: articleUrl, domain, title: details });
          }
        } catch (err) {
          debugLog("ERROR", "Failed to parse progress event", { data: ev.data, error: err });
        }
      };

      const handleComplete = (ev: MessageEvent) => {
        try {
          debugLog("COMPLETE", "Received complete event", { data: ev.data });
          const data = JSON.parse(ev.data);
          const result = data?.data;
          const summary =
            result?.result?.content ||
            result?.content ||
            "No summary available.";

          const finalMsg: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            title: "Research Summary",
            text: summary,
            timestamp: new Date().toISOString()
          };

          setIsStreaming(false);
          setIsSending(false);
          isSendingRef.current = false;
          setCotCurrent(null);
          setCotActive(null);
          finalize(finalMsg);
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
        } catch (err) {
          debugLog("ERROR", "Failed to process final result", { data: ev.data, error: err });
          const finalErr: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "error",
            title: "Error",
            text: "Failed to process final result",
            timestamp: new Date().toISOString(),
            meta: err instanceof Error ? err.message : String(err)
          };
          setIsStreaming(false);
          setIsSending(false);
          isSendingRef.current = false;
          setCotCurrent(null);
          setCotActive(null);
          finalize(finalErr);
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
        }
      };

      const handleErrorEvent = (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          const msg = data?.error || data?.message || "Stream error";
          const code = data?.code;
          debugLog("ERROR", "Stream error event received", { data, msg, code });

          // Build detailed error message
          let fullMessage = msg;
          if (code && code !== "unknown" && code !== "internal_error") {
            fullMessage = `[${code}] ${msg}`;
          }

          const errMsg: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "error",
            title: "Error",
            text: fullMessage,
            timestamp: new Date().toISOString(),
            meta: code ? `Error code: ${code}` : undefined
          };
          setIsStreaming(false);
          setIsSending(false);
          isSendingRef.current = false;
          setCotCurrent(null);
          setCotActive(null);
          finalize(errMsg);
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
        } catch (err) {
          debugLog("ERROR", "Failed to parse error event", { data: ev.data, error: err });
          const errMsg: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "error",
            title: "Error",
            text: "Stream error",
            timestamp: new Date().toISOString()
          };
          setIsStreaming(false);
          setIsSending(false);
          isSendingRef.current = false;
          setCotCurrent(null);
          setCotActive(null);
          finalize(errMsg);
        }
      };

      es.addEventListener("progress", handleProgress);
      es.addEventListener("complete", handleComplete);
      es.addEventListener("error", handleErrorEvent);

      es.onerror = (err) => {
        debugLog("ERROR", "EventSource error occurred", {
          readyState: es.readyState,
          url: streamUrl.replace(encoded, "QUERY_ENCODED"),
          error: err
        });
        const errMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "error",
          title: "Connection Error",
          text: "Connection to server lost. Please check if the backend is running.",
          timestamp: new Date().toISOString(),
          meta: `URL: ${streamUrl.replace(encoded, "QUERY_ENCODED")}`
        };
        setIsStreaming(false);
        setIsSending(false);
        isSendingRef.current = false;
        setCotCurrent(null);
        setCotActive(null);
        finalize(errMsg);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    } catch (error) {
      debugLog("ERROR", "Failed to create EventSource", { error, streamUrl });
      const message =
        error instanceof Error ? error.message : "Failed to start stream";
      finalize({
        id: `error-${Date.now()}`,
        role: "error",
        title: "Error",
        text: message,
        timestamp: new Date().toISOString(),
        meta: error instanceof Error ? error.stack : undefined
      });
      setIsStreaming(false);
      setIsSending(false);
      isSendingRef.current = false;
      setCotCurrent(null);
      setCotActive(null);
    } finally {
      // keep isSendingRef locked until complete/error handlers unlock
    }
  };

  return (
    <div className="app-shell">
      {/* Debug Panel - Only in development */}
      {import.meta.env.DEV && debugErrors.length > 0 && (
        <div style={{
          position: "fixed",
          bottom: "80px",
          right: "20px",
          maxWidth: "400px",
          background: "#1a1a1a",
          color: "#fff",
          padding: "15px",
          borderRadius: "8px",
          fontSize: "12px",
          zIndex: 9999,
          maxHeight: "300px",
          overflow: "auto",
          boxShadow: "0 4px 12px rgba(0,0,0,0.5)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <strong style={{ color: "#ff6b6b" }}>🔍 Debug Errors ({debugErrors.length})</strong>
            <button
              onClick={() => setDebugErrors([])}
              style={{ background: "#ff6b6b", border: "none", color: "#fff", padding: "4px 8px", borderRadius: "4px", cursor: "pointer" }}
            >
              Clear
            </button>
          </div>
          {debugErrors.map((err, i) => (
            <div key={i} style={{ marginBottom: "10px", padding: "8px", background: "#2a2a2a", borderRadius: "4px", borderLeft: "3px solid #ff6b6b" }}>
              <div style={{ color: "#aaa", fontSize: "10px", marginBottom: "4px" }}>{err.timestamp}</div>
              <div style={{ color: "#ff6b6b", fontWeight: "bold", marginBottom: "4px" }}>{err.message}</div>
              {err.data != null && (
                <pre style={{ color: "#ccc", fontSize: "10px", margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {JSON.stringify(err.data, null, 2) as string}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}

      {currentPage === "login" ? (
        <div className="login-container">
          <section className="login-left">
            <div className="login-left-inner">
              <h1>Stay Informed with BUTDA</h1>
              <p>
                Your personal AI assistant for staying up-to-date with the latest
                news and developments.
              </p>
              <div className="feature-grid">
                {featureCards.map((card) => (
                  <article key={card.title} className="feature-card">
                    <span className="feature-icon">{card.icon}</span>
                    <p>{card.title}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>
          <section className="login-right">
            <div className="login-card">
              <div className="brand-badge">
                <img src={getAssetUrl('/logo.png')} alt="BUTDA Logo" />
                <h2>BUTDA</h2>
                <p>Being-Up-To-Date Assistant</p>
              </div>
              <h3>Sign in to your account</h3>
              <form onSubmit={handleLogin}>
                <label>
                  Email address
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </label>
                <label>
                  Password
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </label>
                <button type="submit">Sign in</button>
              </form>
              <p className="signup-hint">
                Don't have an account? <span>Sign up</span>
              </p>
            </div>
          </section>
        </div>
      ) : (
        <div className="app-layout">
          <aside className="sidebar">
            <div className="sidebar-brand">
              <img src={getAssetUrl('/logo.png')} alt="BUTDA Logo" />
              <span className="sidebar-brand-name">BUTDA</span>
            </div>
            <nav className="sidebar-nav">
              <button
                className={`sidebar-nav-item ${currentView === "chat" ? "active" : ""}`}
                onClick={() => setCurrentView("chat")}
              >
                <span className="nav-icon">💬</span>
                <span>Chat</span>
              </button>
              <button
                className={`sidebar-nav-item ${currentView === "savelist" ? "active" : ""}`}
                onClick={() => setCurrentView("savelist")}
              >
                <span className="nav-icon">📚</span>
                <span>SaveList</span>
                {savedItems.length > 0 && (
                  <span className="nav-badge">{savedItems.length}</span>
                )}
              </button>
              <button
                className={`sidebar-nav-item ${currentView === "settings" ? "active" : ""}`}
                onClick={() => setCurrentView("settings")}
              >
                <span className="nav-icon">⚙️</span>
                <span>Settings</span>
              </button>
            </nav>
          </aside>
          <div className="main-content">
            {currentView === "chat" && (
              <>
                <header className="app-header">
                  <div className="header-left"></div>
                  <div className="header-right">
                    <button className="signin-button" type="button" onClick={() => setCurrentPage("login")}>
                      Sign In
                    </button>
                  </div>
                </header>
                <main className="chat-main">
            {messages.map((message) => {
              if (message.role === "loading") {
                return (
                  <div key={message.id} className="message-row">
                    <img src={getAssetUrl('/logo.png')} alt="BUTDA" className="message-avatar" />
                    <div className="chat-bubble incoming loading">
                      {isStreaming ? (
                        <div className="loading-content">
                          {/* Current status - always visible at top */}
                          <div className="message-body status-indicator">
                            <span className="status-text">
                              {cotCurrent ? `${cotCurrent.stage}${cotCurrent.message ? `: ${cotCurrent.message}` : ""}` : "Working..."}
                            </span>
                            <span className="typing-dots-inline">
                              <span />
                              <span />
                              <span />
                            </span>
                          </div>
                          
                          {/* Search results list */}
                          {cotMessages.filter(t => t.stage === "🔎 Searching" && !!t.article_url).length > 0 && (
                            <div className="sources-list">
                              <div className="sources-header">Found sources:</div>
                              {cotMessages.filter(t => t.stage === "🔎 Searching" && !!t.article_url).map((t, i) => (
                                <div key={i} className="source-item">
                                  <span className="source-title">{t.details ? t.details : (t.message || "Source")}</span>
                                  {t.domain ? (<span className="source-domain">{` · ${t.domain}`}</span>) : null}
                                  {t.article_url ? (
                                    <a href={t.article_url} target="_blank" rel="noopener noreferrer" className="source-link">Open</a>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* Currently reading indicator */}
                          {cotActive?.url ? (
                            <div className="message-body reading-indicator">
                              <span>📖 Now reading</span>
                              {cotActive.title ? (<span>{` – ${cotActive.title}`}</span>) : null}
                              {cotActive.domain ? (<span className="source-domain">{` · ${cotActive.domain}`}</span>) : null}
                              <a href={cotActive.url} target="_blank" rel="noopener noreferrer" className="source-link">Open</a>
                            </div>
                          ) : null}
                        </div>
                      ) : (
                        <div className="typing-dots">
                          <span />
                          <span />
                          <span />
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              const isUser = message.role === "user";
              const isResearchSummary = message.title === "Research Summary";
              const bubbleClass = [
                "chat-bubble",
                isUser ? "outgoing" : "incoming",
                message.role === "error" ? "error" : "",
                isResearchSummary ? "research-summary" : ""
              ]
                .filter(Boolean)
                .join(" ");

              const renderBody = () => {
                if (!message.text) return null;
                if (message.role === "error") {
                  return <p className="message-body">{message.text}</p>;
                }
                const safe = renderMarkdownHtml(message.text);
                return (
                  <div
                    className="message-body"
                    dangerouslySetInnerHTML={{ __html: safe }}
                  />
                );
              };

              return (
                <div
                  key={message.id}
                  className={`message-row ${isUser ? "align-end" : ""}`}
                >
                  {!isUser && (
                    <img
                      src={getAssetUrl('/logo.png')}
                      alt="BUTDA"
                      className="message-avatar"
                    />
                  )}
                  <div className={bubbleClass}>
                    {message.title && (
                      <h4 className="message-title">{message.title}</h4>
                    )}
                    {renderBody()}
                    {message.meta && (
                      <p className="message-meta">{message.meta}</p>
                    )}
                    {message.role === "assistant" && message.id !== "welcome" && (
                      <button
                        className="message-save-btn"
                        onClick={() => toggleSave(message)}
                      >
                        {isMessageSaved(message.id) ? "❤️ Saved" : "🤍 Save"}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </main>

          <footer className="chat-input">
            <input
              type="text"
              placeholder="Ask about any topic..."
              value={userInput}
              onChange={(event) => setUserInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleSend();
                }
              }}
              disabled={isSending}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={isSending || !userInput.trim()}
            >
              {isSending ? "Working..." : "Send 🚀"}
            </button>
          </footer>
              </>
            )}
            {currentView === "savelist" && (
              <div className="savelist-view">
                <header className="savelist-header">
                  <div className="savelist-header-left">
                    <h2>SaveList</h2>
                    <p className="savelist-count">{savedItems.length} {savedItems.length === 1 ? "item" : "items"} saved</p>
                  </div>
                  {savedItems.length > 0 && (
                    <button className="export-button" onClick={() => setShowExportModal(true)}>
                      <span className="export-icon">📥</span>
                      Export
                    </button>
                  )}
                </header>
                <main className="savelist-main">
                  {savedItems.length === 0 ? (
                    <div className="savelist-empty">
                      <span className="empty-icon">📚</span>
                      <h3>No saved items yet</h3>
                      <p>Click the heart button on any response to save it here.</p>
                    </div>
                  ) : (
                    <div className="savelist-items">
                      {savedItems.map((item) => (
                        <div key={item.id} className="savelist-item">
                          <div className="savelist-item-header">
                            <span className="savelist-item-title">
                              {new Date(item.timestamp).toLocaleDateString("en-US", {
                                weekday: "long",
                                year: "numeric",
                                month: "long",
                                day: "numeric"
                              })}
                            </span>
                            <div className="savelist-item-actions">
                              {editingItemId === item.id ? (
                                <>
                                  <button
                                    className="savelist-action-btn edit-save-btn"
                                    onClick={saveEdit}
                                  >
                                    ✓ Save
                                  </button>
                                  <button
                                    className="savelist-action-btn edit-cancel-btn"
                                    onClick={cancelEdit}
                                  >
                                    ✕ Cancel
                                  </button>
                                </>
                              ) : (
                                <>
                                  <button
                                    className="savelist-action-btn"
                                    onClick={() => startEdit(item)}
                                  >
                                    ✏️ Edit
                                  </button>
                                  <button
                                    className="savelist-remove-btn"
                                    onClick={() => toggleSave(item)}
                                    aria-label="Remove from saves"
                                  >
                                    🗑️
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                          <div className="savelist-item-content">
                            {editingItemId === item.id ? (
                              <textarea
                                className="savelist-edit-textarea"
                                value={editedContent}
                                onChange={(e) => setEditedContent(e.target.value)}
                                rows={10}
                              />
                            ) : (
                              <div dangerouslySetInnerHTML={{ __html: renderMarkdownHtml(item.text) }} />
                            )}
                          </div>
                          <p className="savelist-item-time">{formatTimestampDisplay(item.timestamp)}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </main>
              </div>
            )}
            {showSaveConfirm && (
              <div className="confirm-modal" onClick={cancelSaveEdit}>
                <div className="confirm-modal-content" onClick={(e) => e.stopPropagation()}>
                  <h3>Confirm Save Edit</h3>
                  <p>This action cannot be withdrawn. Are you sure you want to save these changes?</p>
                  <div className="confirm-modal-actions">
                    <button className="confirm-modal-btn cancel" onClick={cancelSaveEdit}>
                      Cancel
                    </button>
                    <button className="confirm-modal-btn confirm" onClick={confirmSaveEdit}>
                      Confirm Save
                    </button>
                  </div>
                </div>
              </div>
            )}
            {showExportModal && (
              <div className="confirm-modal" onClick={() => setShowExportModal(false)}>
                <div className="confirm-modal-content export-modal-content" onClick={(e) => e.stopPropagation()}>
                  <h3>Export SaveList</h3>
                  <p>Choose a format to export your saved items:</p>
                  <div className="export-options">
                    <button className="export-option-btn" onClick={exportToWord}>
                      <span className="export-option-icon">📄</span>
                      <div className="export-option-info">
                        <span className="export-option-title">Word Document</span>
                        <span className="export-option-desc">.doc format compatible with Microsoft Word</span>
                      </div>
                    </button>
                    <button className="export-option-btn" onClick={exportToPDF}>
                      <span className="export-option-icon">📕</span>
                      <div className="export-option-info">
                        <span className="export-option-title">PDF Document</span>
                        <span className="export-option-desc">Print or save as PDF from your browser</span>
                      </div>
                    </button>
                  </div>
                  <div className="confirm-modal-actions">
                    <button className="confirm-modal-btn cancel" onClick={() => setShowExportModal(false)}>
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
            {currentView === "settings" && (
              <div className="settings-view">
                <header className="settings-header">
                  <h2>Settings</h2>
                  <p className="settings-subtitle">Manage your profile and preferences</p>
                </header>
                <main className="settings-main">
                  <section className="settings-section">
                    <div className="settings-section-header">
                      <h3>Profile</h3>
                      {!isEditingProfile && (
                        <button className="profile-edit-icon-btn" onClick={startEditProfile} aria-label="Edit profile">
                          ✏️
                        </button>
                      )}
                    </div>
                    <div className="profile-card">
                      <div className="profile-info">
                        <div className="profile-field">
                          <label>Name</label>
                          {isEditingProfile ? (
                            <input
                              type="text"
                              value={editingProfileName}
                              onChange={(e) => setEditingProfileName(e.target.value)}
                              placeholder="Your name"
                            />
                          ) : (
                            <div className="profile-value">{profileName}</div>
                          )}
                        </div>
                        <div className="profile-field">
                          <label>Interesting Topics</label>
                          {isEditingProfile ? (
                            <textarea
                              value={editingProfileTopics}
                              onChange={(e) => setEditingProfileTopics(e.target.value)}
                              placeholder="e.g., Technology, Science, Politics, Entertainment..."
                              rows={3}
                            />
                          ) : (
                            <div className="profile-value">{profileTopics || <span className="profile-empty">No topics specified</span>}</div>
                          )}
                        </div>
                        {isEditingProfile && (
                          <div className="profile-edit-actions">
                            <button className="profile-save-btn" onClick={saveProfile}>
                              ✓ Save
                            </button>
                            <button className="profile-cancel-btn" onClick={cancelEditProfile}>
                              ✕ Cancel
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </section>

                  <section className="settings-section">
                    <div className="settings-section-header">
                      <h3>Preferences</h3>
                    </div>
                    <div className="settings-card">
                      <div className="settings-item">
                        <div className="settings-item-info">
                          <h4>Dark Mode</h4>
                          <p>Enable dark theme for the app</p>
                        </div>
                        <label className="toggle-switch">
                          <input type="checkbox" checked={darkMode} onChange={(e) => setDarkMode(e.target.checked)} />
                          <span className="toggle-slider"></span>
                        </label>
                      </div>
                      <div className="settings-item">
                        <div className="settings-item-info">
                          <h4>Push Notifications</h4>
                          <p>Receive push notifications for updates</p>
                        </div>
                        <label className="toggle-switch">
                          <input type="checkbox" defaultChecked />
                          <span className="toggle-slider"></span>
                        </label>
                      </div>
                      <div className="settings-item expanded">
                        <div className="settings-item expanded-header">
                          <div className="settings-item-info">
                            <h4>Email Notifications</h4>
                            <p>Receive daily email summaries</p>
                          </div>
                          <label className="toggle-switch">
                            <input type="checkbox" checked={emailNotifications} onChange={(e) => setEmailNotifications(e.target.checked)} />
                            <span className="toggle-slider"></span>
                          </label>
                        </div>
                        {emailNotifications && (
                          <div className="email-time-selector">
                            <label>Email address:</label>
                            <div className="email-input-row">
                              <input
                                type="email"
                                value={notificationEmail}
                                onChange={(e) => setNotificationEmail(e.target.value)}
                                placeholder="you@example.com"
                                className="email-input"
                                disabled={emailVerified}
                              />
                              {!emailVerified ? (
                                <button
                                  type="button"
                                  onClick={handleVerifyEmail}
                                  disabled={!notificationEmail || !notificationEmail.includes("@") || verifyingEmail}
                                  className="verify-button"
                                >
                                  {verifyingEmail ? "Sending..." : "Verify"}
                                </button>
                              ) : (
                                <span className="verified-badge">
                                  <span className="verified-icon">✓</span>
                                  Verified
                                </span>
                              )}
                            </div>
                            <label>Receive emails at:</label>
                            <input
                              type="time"
                              value={emailTime}
                              onChange={(e) => setEmailTime(e.target.value)}
                              className="time-input"
                            />
                          </div>
                        )}
                      </div>
                      <div className="settings-item">
                        <div className="settings-item-info">
                          <h4>Auto-save Responses</h4>
                          <p>Automatically save all research responses</p>
                        </div>
                        <label className="toggle-switch">
                          <input type="checkbox" checked={autoSave} onChange={(e) => setAutoSave(e.target.checked)} />
                          <span className="toggle-slider"></span>
                        </label>
                      </div>
                    </div>
                  </section>

                  <section className="settings-section">
                    <div className="settings-section-header">
                      <h3>Account</h3>
                    </div>
                    <div className="settings-card">
                      <div className="settings-item">
                        <div className="settings-item-info">
                          <h4>Change Password</h4>
                          <p>Update your account password</p>
                        </div>
                        <button className="settings-action-btn">Change</button>
                      </div>
                      <div className="settings-item">
                        <div className="settings-item-info">
                          <h4>Export Data</h4>
                          <p>Download all your saved items and chats</p>
                        </div>
                        <button className="settings-action-btn">Export</button>
                      </div>
                      <div className="settings-item danger">
                        <div className="settings-item-info">
                          <h4>Delete Account</h4>
                          <p>Permanently delete your account and data</p>
                        </div>
                        <button className="settings-action-btn danger">Delete</button>
                      </div>
                    </div>
                  </section>
                </main>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
