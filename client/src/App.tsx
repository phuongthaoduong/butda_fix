import { FormEvent, useState, useRef, useEffect } from "react";
import "./App.css";

type MessageRole = "assistant" | "user" | "error" | "loading";

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
    timestamp: "Just now"
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
  new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

const getAssetUrl = (path: string) => {
  return new URL(path, import.meta.url).href;
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [userInput, setUserInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [cotMessages, setCotMessages] = useState<Array<{ stage: string; message?: string; details?: string; article_url?: string; domain?: string }>>([]);
  const [cotActive, setCotActive] = useState<{ url?: string; domain?: string; title?: string } | null>(null);
  const [cotCurrent, setCotCurrent] = useState<{ stage: string; message?: string } | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const isSendingRef = useRef(false);

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

    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, label, url) => {
      const safeUrl = url.startsWith("http") ? url : "#";
      return `<a href="${safeUrl}" rel="noopener">${label}</a>`;
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
      setIsLoggedIn(true);
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
      timestamp: "Processing..."
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setUserInput("");

    if (REQUIRE_API) {
      const message: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "error",
        title: "Configuration Error",
        text: "Thiếu biến VITE_API_URL trong môi trường production.",
        timestamp: "Just now"
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

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    try {
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        // Connected
      };

      const stageCopy: Record<string, string> = {
        starting: "Starting",
        loading: "Loading",
        searching: "Searching",
        reading: "Reading",
        thinking: "Thinking",
        writing: "Organizing",
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
        } catch (_) {
          // ignore parse errors
        }
      };

      const handleComplete = (ev: MessageEvent) => {
        try {
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
            timestamp: "Just now"
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
          const finalErr: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "error",
            title: "Error",
            text: "Failed to process final result",
            timestamp: "Just now"
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
          const errMsg: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "error",
            title: "Error",
            text: msg,
            timestamp: "Just now"
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
        } catch (_) {
          const errMsg: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "error",
            title: "Error",
            text: "Stream error",
            timestamp: "Just now"
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

      es.onerror = () => {
        const errMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "error",
          title: "Error",
          text: "Connection to server lost",
          timestamp: "Just now"
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
      const message =
        error instanceof Error ? error.message : "Failed to start stream";
      finalize({
        id: `error-${Date.now()}`,
        role: "error",
        title: "Error",
        text: message,
        timestamp: "Just now"
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
      {!isLoggedIn ? (
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
        <div className="main-app">
          <header className="app-header">
            <div className="brand-belt">
              <div className="brand-lockup">
                <img src={getAssetUrl('/logo.png')} alt="BUTDA Logo" />
                <div>
                  <span className="brand-name">BUTDA</span>
                  <p>Being-Up-To-Date Assistant</p>
                </div>
              </div>
            </div>
            <button className="settings-button" type="button" aria-label="Settings">
              ⚙️
            </button>
          </header>

          <main className="chat-main">
            {messages.map((message) => {
              if (message.role === "loading") {
                return (
                  <div key={message.id} className="message-row">
                    <img src={getAssetUrl('/logo.png')} alt="BUTDA" className="message-avatar" />
                    <div className="chat-bubble incoming loading">
                      {isStreaming ? (
                        <div>
                          <div className="message-body">
                            <span>{cotCurrent ? `${cotCurrent.stage}${cotCurrent.message ? `: ${cotCurrent.message}` : ""}` : "Working..."}</span>
                          </div>
                          {cotMessages.filter(t => t.stage === "Searching" && !!t.article_url).map((t, i) => (
                            <div key={i} className="message-body">
                              <span>{t.details ? t.details : (t.message || "Source")}</span>
                              {t.domain ? (<span>{` · ${t.domain}`}</span>) : null}
                              {t.article_url ? (
                                <span>
                                  {" "}
                                  <a href={t.article_url} target="_blank" rel="noopener noreferrer">Open</a>
                                </span>
                              ) : null}
                            </div>
                          ))}
                          {cotActive?.url ? (
                            <div className="message-body">
                              <span>Now reading</span>
                              {cotActive.title ? (<span>{` – ${cotActive.title}`}</span>) : null}
                              {cotActive.domain ? (<span>{` · ${cotActive.domain}`}</span>) : null}
                              <span> <a href={cotActive.url} target="_blank" rel="noopener noreferrer">Open</a></span>
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
              const bubbleClass = [
                "chat-bubble",
                isUser ? "outgoing" : "incoming",
                message.role === "error" ? "error" : ""
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
                    <p className="message-timestamp">{message.timestamp}</p>
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
        </div>
      )}
    </div>
  );
}

export default App;
