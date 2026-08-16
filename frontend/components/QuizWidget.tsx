"use client";

import { useState } from "react";

type Quiz = { question: string; options: string[]; correct_option: number; explanation: string; source: { document: string; page: number } };
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

export default function QuizWidget({ courseId }: { courseId: string }) {
  const [topics, setTopics] = useState("");
  const [step, setStep] = useState<"topics" | "count" | "questions">("topics");
  const [count, setCount] = useState(5);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);
  const quiz = quizzes[index];

  async function generateQuiz() {
    setLoading(true); setError(""); setSelected(null); setShowConfetti(false);
    try {
      const url = API_BASE_URL ? new URL("/quiz", API_BASE_URL).toString() : "/quiz";
      const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ course_id: courseId, topic: topics.trim() || null, question_count: count }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || "Unable to generate a quiz.");
      setQuizzes(data.questions); setIndex(0); setStep("questions");
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to generate a quiz."); } finally { setLoading(false); }
  }

  function answer(option: number) {
    if (!quiz || selected !== null) return;
    setSelected(option);
    if (option === quiz.correct_option) { setShowConfetti(true); window.setTimeout(() => setShowConfetti(false), 1800); }
  }

  function nextQuestion() {
    setSelected(null); setShowConfetti(false);
    if (index + 1 < quizzes.length) setIndex((value) => value + 1);
    else { setStep("topics"); setQuizzes([]); }
  }

  return <div style={{ display: "grid", gap: "1rem", position: "relative" }}>
    {showConfetti && <div aria-hidden="true" style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none", zIndex: 4 }}>{Array.from({ length: 24 }, (_, particle) => <i key={particle} className="quiz-confetti" style={{ left: `${(particle * 37) % 100}%`, background: ["#2563eb", "#facc15", "#22c55e", "#f472b6"][particle % 4], animationDelay: `${(particle % 7) * 0.06}s` }} />)}</div>}
    <div style={{ padding: "1rem", borderRadius: "18px", background: "linear-gradient(135deg, #dbeafe, #93c5fd)", color: "#0f172a" }}><strong>Quiz me</strong><p style={{ margin: "0.35rem 0 0", lineHeight: 1.5 }}>Questions are generated only from retrieved material in this course.</p></div>
    {step === "topics" && <><label style={labelStyle}>Chapters or topics <span style={{ color: "#475569", fontWeight: 400 }}>(separate with commas)</span><input autoFocus value={topics} onChange={(event) => setTopics(event.target.value)} placeholder="e.g. Chapter 1, Chapter 3: Retained earnings" style={inputStyle} /></label><button type="button" onClick={() => setStep("count")} style={buttonStyle}>Continue</button></>}
    {step === "count" && <section style={{ padding: "1rem", borderRadius: "16px", background: "#eff6ff", border: "1px solid #bfdbfe" }}><strong style={{ color: "#0f172a" }}>Professor DOTU: How many questions would you like?</strong><div style={{ display: "flex", gap: "0.65rem", alignItems: "center", marginTop: "0.85rem" }}><input aria-label="Number of quiz questions" type="number" min="1" max="10" value={count} onChange={(event) => setCount(Math.max(1, Math.min(10, Number(event.target.value) || 1)))} style={{ ...inputStyle, width: "78px" }} /><button type="button" onClick={generateQuiz} disabled={loading} style={buttonStyle}>{loading ? "Creating…" : "Generate quiz"}</button><button type="button" onClick={() => setStep("topics")} style={{ border: 0, background: "transparent", color: "#1d4ed8", cursor: "pointer" }}>Back</button></div></section>}
    {error && <p role="alert" style={{ margin: 0, color: "#b91c1c" }}>{error}</p>}
    {step === "questions" && quiz && <section style={{ padding: "1.1rem", border: "1px solid #bfdbfe", borderRadius: "18px", background: "#fff" }}><p style={{ margin: "0 0 0.8rem", color: "#1d4ed8", fontWeight: 800 }}>Question {index + 1} of {quizzes.length}</p><h3 style={{ margin: "0 0 1rem", color: "#0f172a", lineHeight: 1.4 }}>{quiz.question}</h3><div style={{ display: "grid", gap: "0.6rem" }}>{quiz.options.map((option, optionIndex) => { const answered = selected !== null; const correct = optionIndex === quiz.correct_option; const selectedWrong = selected === optionIndex && !correct; return <button key={option} type="button" disabled={answered} onClick={() => answer(optionIndex)} style={{ textAlign: "left", padding: "0.75rem 0.85rem", borderRadius: "12px", border: `1px solid ${correct && answered ? "#16a34a" : selectedWrong ? "#dc2626" : "#bfdbfe"}`, background: correct && answered ? "#dcfce7" : selectedWrong ? "#fee2e2" : "#eff6ff", color: "#0f172a", cursor: answered ? "default" : "pointer" }}><strong>{String.fromCharCode(65 + optionIndex)}.</strong> {option}</button>; })}</div>{selected !== null && <div style={{ marginTop: "1rem", padding: "0.9rem", borderRadius: "12px", background: selected === quiz.correct_option ? "#dcfce7" : "#fef3c7", color: "#1f2937" }}><strong>{selected === quiz.correct_option ? "✓ Correct" : "Not quite"}</strong><p style={{ margin: "0.45rem 0 0" }}><strong>Explanation:</strong> {quiz.explanation}</p><p style={{ margin: "0.45rem 0 0", fontSize: "0.9rem" }}><strong>Source:</strong> {quiz.source.document}, Page {quiz.source.page}</p></div>} {selected !== null && <button type="button" onClick={nextQuestion} style={{ ...buttonStyle, marginTop: "1rem" }}>{index + 1 < quizzes.length ? "Next question" : "Finish quiz"}</button>}</section>}
  </div>;
}

const labelStyle = { display: "grid", gap: "0.4rem", color: "#0f172a", fontWeight: 700 };
const inputStyle = { padding: "0.7rem 0.85rem", border: "1px solid #93c5fd", borderRadius: "12px", color: "#0f172a" };
const buttonStyle = { border: 0, borderRadius: "999px", padding: "0.7rem 1rem", background: "#2563eb", color: "white", fontWeight: 700, cursor: "pointer" };
