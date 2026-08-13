"use client";

import React, { useEffect, useRef, useState } from "react";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

export type Message = {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
};

const bubbleStyles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    display: "flex",
    flexDirection: "column",
    gap: "1rem",
    padding: "1rem",
    borderRadius: "16px",
    background: "#ffffff",
    boxShadow: "0 6px 20px rgba(0,0,0,0.06)",
  },
  header: {
    textAlign: "center",
  },
  title: {
    margin: 0,
    fontSize: "1.25rem",
    fontWeight: 700,
    color: "#0f172a",
  },
  messages: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
    maxHeight: "420px",
    overflowY: "auto",
    padding: "0.25rem",
  },
  bubbleUser: {
    alignSelf: "flex-end",
    background: "#e6f7ff",
    color: "#04233a",
    borderRadius: "16px 16px 4px 16px",
    padding: "0.6rem 0.9rem",
    maxWidth: "78%",
    whiteSpace: "pre-wrap",
  },
  bubbleAssistant: {
    alignSelf: "flex-start",
    background: "linear-gradient(90deg,#93c5fd,#60a5fa)",
    color: "#021124",
    borderRadius: "16px 16px 16px 4px",
    padding: "0.6rem 0.9rem",
    maxWidth: "78%",
    whiteSpace: "pre-wrap",
  },
  sources: {
    marginTop: "0.5rem",
    padding: "0.45rem 0.65rem",
    background: "rgba(2,6,23,0.03)",
    borderRadius: "10px",
    fontSize: "0.88rem",
    color: "#06313a",
  },
  formRow: {
    display: "flex",
    gap: "0.5rem",
    alignItems: "center",
  },
  textarea: {
    flex: 1,
    minHeight: "80px",
    padding: "0.6rem",
    borderRadius: "10px",
    border: "1px solid rgba(2,6,23,0.06)",
    background: "#e6f7ff",
    color: "#04233a",
    resize: "vertical",
  },
  button: {
    padding: "0.6rem 0.9rem",
    borderRadius: "999px",
    border: "none",
    background: "#60a5fa",
    color: "white",
    cursor: "pointer",
  },
  clear: {
    background: "transparent",
    border: "1px solid rgba(2,6,23,0.06)",
    color: "#04233a",
  },
};

type ChatWidgetProps = {
  courseId: string;
  messages: Message[];
  onMessagesChange: (messages: Message[]) => void;
};

export default function ChatWidget({ courseId, messages, onMessagesChange }: ChatWidgetProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const text = input.trim();
    if (!text) return;
    const userMsg: Message = { role: "user", text };
    onMessagesChange([...messages, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const chatUrl = API_BASE_URL ? new URL("/chat", API_BASE_URL).toString() : "/chat";
      const res = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, course_id: courseId }),
      });
      const data = await res.json();
      const assistant: Message = { role: "assistant", text: data?.answer || "(no answer)", sources: data?.sources || [] };
      onMessagesChange([...messages, userMsg, assistant]);
    } catch {
      onMessagesChange([...messages, userMsg, { role: "assistant", text: "Server error. Check backend.", sources: [] }]);
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    onMessagesChange([]);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.ctrlKey || e.shiftKey) === false && !e.altKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div style={bubbleStyles.container}>
      <div style={bubbleStyles.messages}>
        {messages.length === 0 && (
          <div style={bubbleStyles.bubbleAssistant}>Hi — upload a textbook and ask me about the course material.</div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: m.role === "user" ? "flex-end" : "flex-start",
              gap: "0.4rem",
            }}
          >
            <div style={m.role === "user" ? bubbleStyles.bubbleUser : bubbleStyles.bubbleAssistant}>{m.text}</div>
            {m.sources && m.sources.length > 0 && (
              <div style={bubbleStyles.sources}>
                <strong>Sources:</strong>
                <ul style={{ margin: "0.25rem 0 0 0.75rem" }}>
                  {m.sources.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div style={{ marginTop: "0.5rem" }}>
        <div style={bubbleStyles.formRow}>
          <textarea
            style={bubbleStyles.textarea}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Type your question and press Enter to send"
          />
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button style={bubbleStyles.button} onClick={sendMessage} disabled={loading}>
              {loading ? <span className="typing-indicator" aria-label="Professor DOTU is typing"><i /><i /><i /></span> : "Send"}
            </button>
            <button style={{ ...bubbleStyles.button, ...bubbleStyles.clear }} onClick={clearChat}>
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
