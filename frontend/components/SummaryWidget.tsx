"use client";

import { useState } from "react";

type Summary = { title: string; points: string[]; sources: { document: string; page: number; chunk_id: string }[] };
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

export default function SummaryWidget({ courseId }: { courseId: string }) {
  const [topic, setTopic] = useState("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  async function summarize() {
    if (!topic.trim()) { setError("Enter a chapter or topic first."); return; }
    setLoading(true); setError("");
    try {
      const url = API_BASE_URL ? new URL("/summary", API_BASE_URL).toString() : "/summary";
      const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ course_id: courseId, topic: topic.trim() }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || "Unable to create a summary.");
      setSummary(data);
    } catch (requestError) { setSummary(null); setError(requestError instanceof Error ? requestError.message : "Unable to create a summary."); } finally { setLoading(false); }
  }
  return <div style={{ display: "grid", gap: "1rem" }}>
    <div style={{ padding: "1rem", borderRadius: "18px", background: "linear-gradient(135deg, #dbeafe, #93c5fd)", color: "#0f172a" }}><strong>Summarize chapter</strong><p style={{ margin: "0.35rem 0 0", lineHeight: 1.5 }}>Turn the uploaded chapter into a clear study guide.</p></div>
    <label style={{ display: "grid", gap: "0.4rem", color: "#0f172a", fontWeight: 700 }}>Chapter or topic<input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="e.g. Chapter 1: Financial statements" style={inputStyle} /></label>
    <button type="button" onClick={summarize} disabled={loading} style={buttonStyle}>{loading ? "Building your summary…" : "Summarize chapter"}</button>
    {error && <p role="alert" style={{ margin: 0, color: "#b91c1c" }}>{error}</p>}
    {summary && <section style={{ padding: "1.25rem", borderRadius: "22px", background: "linear-gradient(160deg, #ffffff, #eff6ff)", border: "1px solid #bfdbfe", boxShadow: "0 12px 28px rgba(37,99,235,0.1)" }}><p style={{ margin: 0, color: "#1d4ed8", fontSize: "0.78rem", fontWeight: 800, letterSpacing: "0.12em" }}>STUDY GUIDE</p><h3 style={{ margin: "0.5rem 0 1rem", color: "#0f172a", fontSize: "1.45rem" }}>{summary.title}</h3><ol style={{ display: "grid", gap: "0.7rem", margin: 0, paddingLeft: "1.5rem", color: "#1e3a8a" }}>{summary.points.map((point, index) => <li key={`${index}-${point}`} style={{ padding: "0.75rem", borderRadius: "12px", background: "rgba(219,234,254,0.7)", color: "#0f172a", lineHeight: 1.5 }}>{point}</li>)}</ol><div style={{ marginTop: "1rem", paddingTop: "0.85rem", borderTop: "1px solid #bfdbfe", fontSize: "0.9rem", color: "#334155" }}><strong>Grounded in:</strong> {summary.sources.map((source) => `${source.document}, Page ${source.page}`).join(" · ")}</div></section>}
  </div>;
}

const inputStyle = { padding: "0.7rem 0.85rem", border: "1px solid #93c5fd", borderRadius: "12px", color: "#0f172a" };
const buttonStyle = { border: 0, borderRadius: "999px", padding: "0.7rem 1rem", background: "#2563eb", color: "white", fontWeight: 700, cursor: "pointer", justifySelf: "start" };
