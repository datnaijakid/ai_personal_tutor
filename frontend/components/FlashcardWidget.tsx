"use client";

import { useState } from "react";

type Flashcard = { front: string; back: string; source: { document: string; page: number } };
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

export default function FlashcardWidget({ courseId }: { courseId: string }) {
  const [topic, setTopic] = useState("");
  const [card, setCard] = useState<Flashcard | null>(null);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generateCard() {
    setLoading(true); setError(""); setFlipped(false);
    try {
      const url = API_BASE_URL ? new URL("/flashcards", API_BASE_URL).toString() : "/flashcards";
      const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ course_id: courseId, topic: topic.trim() || null }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || "Unable to generate a flashcard.");
      setCard(data);
    } catch (requestError) {
      setCard(null); setError(requestError instanceof Error ? requestError.message : "Unable to generate a flashcard.");
    } finally { setLoading(false); }
  }

  return <div style={{ display: "grid", gap: "1rem" }}>
    <div style={{ padding: "1rem", borderRadius: "18px", background: "linear-gradient(135deg, #dbeafe, #93c5fd)", color: "#0f172a" }}><strong>Flashcards</strong><p style={{ margin: "0.35rem 0 0", lineHeight: 1.5 }}>Create a textbook-grounded card for the chapter you are studying.</p></div>
    <label style={{ display: "grid", gap: "0.4rem", color: "#0f172a", fontWeight: 700 }}>Chapter or topic <span style={{ color: "#475569", fontWeight: 400 }}>(optional)</span><input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="e.g. Chapter 1: Financial statements" style={inputStyle} /></label>
    {!card && <button type="button" onClick={generateCard} disabled={loading} style={buttonStyle}>{loading ? "Creating a flashcard…" : "Generate flashcard"}</button>}
    {error && <p role="alert" style={{ margin: 0, color: "#b91c1c" }}>{error}</p>}
    {card && <><button type="button" onClick={() => setFlipped((value) => !value)} style={{ minHeight: "250px", padding: "1.5rem", border: "1px solid #93c5fd", borderRadius: "22px", background: flipped ? "linear-gradient(135deg, #bfdbfe, #60a5fa)" : "linear-gradient(135deg, #eff6ff, #dbeafe)", color: "#0f172a", cursor: "pointer", boxShadow: "0 12px 28px rgba(37,99,235,0.16)", textAlign: "center" }}>
      <span style={{ display: "block", marginBottom: "1rem", color: "#1d4ed8", fontSize: "0.78rem", fontWeight: 800, letterSpacing: "0.12em" }}>{flipped ? "BACK" : "FRONT"}</span>
      <strong style={{ display: "block", fontSize: "1.2rem", lineHeight: 1.55 }}>{flipped ? card.back : card.front}</strong>
      <span style={{ display: "block", marginTop: "1.25rem", color: "#1e3a8a", fontSize: "0.9rem" }}>{flipped ? `Source: ${card.source.document}, Page ${card.source.page}` : "Click to reveal the answer"}</span>
    </button><button type="button" onClick={generateCard} disabled={loading} style={buttonStyle}>{loading ? "Creating…" : "Next flashcard"}</button></>}
  </div>;
}

const inputStyle = { padding: "0.7rem 0.85rem", border: "1px solid #93c5fd", borderRadius: "12px", color: "#0f172a" };
const buttonStyle = { border: 0, borderRadius: "999px", padding: "0.7rem 1rem", background: "#2563eb", color: "white", fontWeight: 700, cursor: "pointer", justifySelf: "start" };
