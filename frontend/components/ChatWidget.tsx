"use client";

import React, { useEffect, useRef, useState } from "react";
import QuizWidget from "@/components/QuizWidget";
import FlashcardWidget from "@/components/FlashcardWidget";
import SummaryWidget from "@/components/SummaryWidget";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

export type Message = {
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
};

export type Source = { document: string; document_id: string; page: number; chunk_id: string };

const bubbleStyles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    flex: 1,
    minHeight: 0,
    position: "relative",
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
    flex: 1,
    minHeight: 0,
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
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
    padding: "0.6rem 0.6rem 0.6rem 3.35rem",
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
  conversationId: string | null;
  onConversationChange: (conversationId: string | null) => void;
  onConversationSaved: () => void;
};

function documentUrl(source: Source, courseId: string) {
  return `/documents/${encodeURIComponent(source.document_id)}/file?course_id=${encodeURIComponent(courseId)}#page=${source.page}`;
}

export default function ChatWidget({ courseId, messages, onMessagesChange, conversationId, onConversationChange, onConversationSaved }: ChatWidgetProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [previewSource, setPreviewSource] = useState<Source | null>(null);
  const [showModes, setShowModes] = useState(false);
  const [mode, setMode] = useState<"chat" | "quiz" | "flashcards" | "summary">("chat");
  const conversationCourseId = useRef(courseId);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const text = input.trim();
    if (!text) return;
    setMode("chat");
    const userMsg: Message = { role: "user", text };
    onMessagesChange([...messages, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const chatUrl = API_BASE_URL ? new URL("/chat", API_BASE_URL).toString() : "/chat";
      const res = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          course_id: courseId,
          conversation_id: conversationCourseId.current === courseId ? conversationId : null,
        }),
      });
      const data = await res.json();
      if (data?.conversation_id) {
        conversationCourseId.current = courseId;
        onConversationChange(data.conversation_id);
        onConversationSaved();
      }
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
    conversationCourseId.current = courseId;
    onConversationChange(null);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.ctrlKey || e.shiftKey) === false && !e.altKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const chatComposer = <div style={{ marginTop: "0.5rem" }}>
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
  </div>;

  return (
    <div style={bubbleStyles.container}>
      <div style={{ position: "absolute", left: "1.6rem", bottom: "1.7rem", zIndex: 3 }}>
        {showModes && <div style={{ position: "absolute", left: 0, bottom: "3.25rem", display: "flex", flexDirection: "column", gap: "0.55rem", alignItems: "flex-start", zIndex: 2 }}>
          <button type="button" onClick={() => { setMode("quiz"); setShowModes(false); }} style={{ minWidth: "142px", border: 0, borderRadius: "999px", padding: "0.65rem 1.2rem", background: "#3b82f6", color: "white", boxShadow: "0 8px 20px rgba(37,99,235,0.28)", fontWeight: 700, cursor: "pointer" }}>Quiz me</button>
          <button type="button" onClick={() => { setMode("flashcards"); setShowModes(false); }} style={{ minWidth: "142px", border: 0, borderRadius: "999px", padding: "0.65rem 1.2rem", background: "#3b82f6", color: "white", boxShadow: "0 8px 20px rgba(37,99,235,0.28)", fontWeight: 700, cursor: "pointer" }}>Flashcards</button>
          <button type="button" onClick={() => { setMode("summary"); setShowModes(false); }} style={{ minWidth: "142px", border: 0, borderRadius: "999px", padding: "0.65rem 1.2rem", background: "#3b82f6", color: "white", boxShadow: "0 8px 20px rgba(37,99,235,0.28)", fontWeight: 700, cursor: "pointer" }}>Summarize</button>
          <button type="button" onClick={() => { setMode("chat"); setShowModes(false); }} style={{ minWidth: "142px", border: 0, borderRadius: "999px", padding: "0.65rem 1.2rem", background: "#3b82f6", color: "white", boxShadow: "0 8px 20px rgba(37,99,235,0.28)", fontWeight: 700, cursor: "pointer" }}>Chat mode</button>
        </div>}
        <button type="button" onClick={() => setShowModes((visible) => !visible)} aria-label="Choose a study mode" aria-expanded={showModes} style={{ width: "42px", height: "42px", border: 0, borderRadius: "50%", background: "#1d4ed8", color: "white", fontSize: "1.6rem", lineHeight: 1, boxShadow: "0 8px 20px rgba(37,99,235,0.35)", cursor: "pointer" }}>{showModes ? "×" : "+"}</button>
      </div>
      {mode === "quiz" ? <><div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}><QuizWidget key={courseId} courseId={courseId} /></div>{chatComposer}</> : mode === "flashcards" ? <><div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}><FlashcardWidget key={courseId} courseId={courseId} /></div>{chatComposer}</> : mode === "summary" ? <><div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}><SummaryWidget key={courseId} courseId={courseId} /></div>{chatComposer}</> : <>
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
            <div style={m.role === "user" ? bubbleStyles.bubbleUser : bubbleStyles.bubbleAssistant}>
              {m.role === "assistant" ? m.text.split(/(\[p\.\d+\])/g).map((part, partIndex) => {
                const page = Number(part.match(/^\[p\.(\d+)\]$/)?.[1]);
                const source = m.sources?.find((item) => item.page === page);
                return source ? <button key={partIndex} type="button" onClick={() => setPreviewSource(source)} style={{ color: "#0c4a6e", fontWeight: 800, textDecoration: "underline", border: 0, background: "transparent", cursor: "pointer", padding: 0 }}>{part}</button> : part;
              }) : m.text}
            </div>
            {m.sources && m.sources.length > 0 && (
              <div style={bubbleStyles.sources}>
                <strong>Sources:</strong>
                <ul style={{ margin: "0.25rem 0 0 0.75rem" }}>
                  {m.sources.map((source) => (
                    <li key={source.chunk_id}><button type="button" onClick={() => setPreviewSource(source)} style={{ color: "#075985", textDecoration: "underline", border: 0, background: "transparent", cursor: "pointer", padding: 0 }}>{source.document}, Page {source.page}</button></li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      {previewSource && <div role="dialog" aria-modal="true" aria-label={`Preview ${previewSource.document}`} style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(15,23,42,0.72)", padding: "4vh 5vw", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", color: "white", fontWeight: 700 }}><span>{previewSource.document} — Page {previewSource.page}</span><button type="button" onClick={() => setPreviewSource(null)}>Close</button></div>
        <iframe title={`${previewSource.document} page ${previewSource.page}`} src={documentUrl(previewSource, courseId)} style={{ width: "100%", flex: 1, minHeight: 0, border: 0, background: "white" }} />
      </div>}

      {chatComposer}
      </>}
    </div>
  );
}
