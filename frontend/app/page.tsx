"use client";

import { FormEvent, useRef, useState } from "react";
import ChatWidget, { type Message } from "@/components/ChatWidget";
import PDFUploader from "@/components/PDFUploader";

type CourseFile = { id: string; name: string };
type Course = { id: string; name: string; files: CourseFile[]; messages: Message[] };

const styles = {
  page: { width: "100%", maxWidth: "1320px", margin: "0 auto", padding: "3rem 1.5rem 4rem", display: "flex", flexDirection: "column" as const, gap: "2rem" },
  hero: { padding: "2rem", borderRadius: "28px", background: "rgba(219, 234, 254, 0.9)", border: "1px solid rgba(59, 130, 246, 0.24)", boxShadow: "0 18px 48px rgba(15, 23, 42, 0.08)", display: "grid", gap: "1.5rem" },
  eyebrow: { color: "#1d4ed8", fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase" as const, margin: 0, fontSize: "1.05rem" },
  title: { margin: "0.75rem 0 0", fontSize: "clamp(2.4rem, 4vw, 4.2rem)", lineHeight: 1.02, color: "#0f172a" },
  subtitle: { margin: "1.2rem 0 0", maxWidth: "720px", fontSize: "1rem", lineHeight: 1.8, color: "#334155" },
  courseSelector: { display: "flex", flexWrap: "wrap" as const, alignItems: "center", justifyContent: "space-between", gap: "0.65rem", padding: "0.85rem 1rem", borderRadius: "18px", background: "linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%)", boxShadow: "0 10px 28px rgba(37, 99, 235, 0.15)", position: "relative" as const },
  panelGrid: { display: "grid", gridTemplateColumns: "repeat(12, minmax(0, 1fr))", gap: "1.5rem" },
  leftPanel: { gridColumn: "span 3" },
  rightPanel: { gridColumn: "span 9" },
  cardShell: { width: "100%", borderRadius: "24px", background: "rgba(255, 255, 255, 0.92)", border: "1px solid rgba(148, 163, 184, 0.18)", boxShadow: "0 10px 36px rgba(15, 23, 42, 0.06)", overflow: "hidden", minHeight: "520px" },
  cardHeader: { background: "linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%)", padding: "1.3rem 1.5rem", color: "#0f172a" },
  cardTitle: { margin: 0, fontSize: "1.15rem", fontWeight: 700 },
  cardBody: { padding: "1.5rem" },
};

export default function Home() {
  const [courses, setCourses] = useState<Course[]>([{ id: "first-course", name: "Untitled course", files: [], messages: [] }]);
  const [activeCourseId, setActiveCourseId] = useState("first-course");
  const [showNewCourseForm, setShowNewCourseForm] = useState(false);
  const [newCourseName, setNewCourseName] = useState("");
  const [editingCourseName, setEditingCourseName] = useState(false);
  const [courseNameDraft, setCourseNameDraft] = useState("");
  const courseTabsRef = useRef<HTMLDivElement>(null);
  const activeCourse = courses.find((course) => course.id === activeCourseId) ?? courses[0];

  function updateActiveCourse(update: (course: Course) => Course) {
    setCourses((current) => current.map((course) => course.id === activeCourseId ? update(course) : course));
  }

  function createCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newCourseName.trim();
    if (!name) return;
    const course: Course = { id: crypto.randomUUID(), name, files: [], messages: [] };
    setCourses((current) => [...current, course]);
    setActiveCourseId(course.id);
    setNewCourseName("");
    setShowNewCourseForm(false);
  }

  function saveCourseName(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = courseNameDraft.trim();
    if (!name) return;
    updateActiveCourse((course) => ({ ...course, name }));
    setEditingCourseName(false);
  }

  function scrollCourses(direction: "left" | "right") {
    courseTabsRef.current?.scrollBy({ left: direction === "left" ? -240 : 240, behavior: "smooth" });
  }

  return (
    <main style={styles.page}>
      <section style={styles.hero}>
        <div>
          <p style={styles.eyebrow}>Professor DOTU</p>
          <h1 style={styles.title}>A smarter study zone for your textbook questions.</h1>
          <p style={styles.subtitle}>Upload your PDF and use the chat tutor to explore concepts, get answers, and review sources instantly.</p>
        </div>
      </section>

      <section style={styles.courseSelector} aria-label="Course selector">
        <button type="button" onClick={() => scrollCourses("left")} aria-label="Show previous courses" style={{ border: 0, borderRadius: "50%", width: "32px", height: "32px", background: "rgba(255,255,255,0.7)", color: "#1e3a8a", cursor: "pointer" }}>‹</button>
        <div ref={courseTabsRef} className="course-tab-strip">
          {courses.map((course) => <button key={course.id} type="button" onClick={() => setActiveCourseId(course.id)} style={{ flex: "0 0 auto", border: 0, borderRadius: "999px", padding: "0.65rem 1rem", background: course.id === activeCourseId ? "#eff6ff" : "rgba(255,255,255,0.42)", color: "#0f172a", fontWeight: 700, cursor: "pointer", whiteSpace: "nowrap" }}>{course.name}</button>)}
        </div>
        <button type="button" onClick={() => scrollCourses("right")} aria-label="Show more courses" style={{ border: 0, borderRadius: "50%", width: "32px", height: "32px", background: "rgba(255,255,255,0.7)", color: "#1e3a8a", cursor: "pointer" }}>›</button>
        <button type="button" onClick={() => { setCourseNameDraft(activeCourse.name); setEditingCourseName(true); }} aria-label="Edit active course name" title="Edit course name" style={{ border: 0, background: "transparent", color: "#1e3a8a", fontSize: "1.1rem", cursor: "pointer", padding: "0.4rem" }}>✎</button>
        <button type="button" onClick={() => setShowNewCourseForm(true)} style={{ border: 0, background: "transparent", color: "#1e3a8a", fontWeight: 700, cursor: "pointer", padding: "0.65rem" }}>+ Add a course</button>
      </section>

      {editingCourseName && <section style={{ padding: "1rem", borderRadius: "18px", background: "rgba(255,255,255,0.92)", boxShadow: "0 10px 28px rgba(15,23,42,0.08)" }}>
        <form onSubmit={saveCourseName} style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>
          <label htmlFor="edit-course-name" style={{ fontWeight: 700, color: "#0f172a" }}>Edit course name</label>
          <input id="edit-course-name" autoFocus value={courseNameDraft} onChange={(event) => setCourseNameDraft(event.target.value)} placeholder="e.g. Financial Accounting" style={{ flex: "1 1 220px", padding: "0.65rem 0.8rem", border: "1px solid #bfdbfe", borderRadius: "10px" }} />
          <button type="submit" style={{ padding: "0.65rem 1rem", border: 0, borderRadius: "10px", background: "#2563eb", color: "white", fontWeight: 700, cursor: "pointer" }}>Save name</button>
          <button type="button" onClick={() => setEditingCourseName(false)} style={{ padding: "0.65rem 0.8rem", border: 0, background: "transparent", color: "#334155", cursor: "pointer" }}>Cancel</button>
        </form>
      </section>}

      {showNewCourseForm && <section style={{ padding: "1rem", borderRadius: "18px", background: "rgba(255,255,255,0.92)", boxShadow: "0 10px 28px rgba(15,23,42,0.08)" }}>
        <form onSubmit={createCourse} style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center" }}>
          <label htmlFor="course-name" style={{ fontWeight: 700, color: "#0f172a" }}>New course name</label>
          <input id="course-name" autoFocus value={newCourseName} onChange={(event) => setNewCourseName(event.target.value)} placeholder="e.g. Calculus" style={{ flex: "1 1 220px", padding: "0.65rem 0.8rem", border: "1px solid #bfdbfe", borderRadius: "10px" }} />
          <button type="submit" style={{ padding: "0.65rem 1rem", border: 0, borderRadius: "10px", background: "#2563eb", color: "white", fontWeight: 700, cursor: "pointer" }}>Create course</button>
          <button type="button" onClick={() => setShowNewCourseForm(false)} style={{ padding: "0.65rem 0.8rem", border: 0, background: "transparent", color: "#334155", cursor: "pointer" }}>Cancel</button>
        </form>
      </section>}

      <section style={styles.panelGrid}>
        <div className="course-upload-panel" style={{ ...styles.leftPanel, minWidth: 0 }}><div style={styles.cardShell}><div style={styles.cardHeader}><h2 style={styles.cardTitle}>Textbook upload</h2></div><div style={styles.cardBody}>
          <PDFUploader key={activeCourse.id} courseId={activeCourse.id} onUploadComplete={(fileName) => updateActiveCourse((course) => ({ ...course, files: [...course.files, { id: crypto.randomUUID(), name: fileName }] }))} />
          <section style={{ marginTop: "1.25rem" }} aria-label="Uploaded PDFs">
            <span style={{ display: "inline-block", padding: "0.35rem 0.7rem", borderRadius: "999px", background: "#dbeafe", color: "#1e3a8a", fontSize: "0.82rem", fontWeight: 700 }}>Uploaded PDFs</span>
            {activeCourse.files.length === 0 ? (
              <p style={{ margin: "0.75rem 0 0", color: "#64748b", fontSize: "0.9rem" }}>No PDFs uploaded yet.</p>
            ) : (
              <div style={{ display: "grid", gap: "0.55rem", marginTop: "0.75rem" }}>
                {activeCourse.files.map((file) => <div key={file.id} title={file.name} style={{ display: "flex", gap: "0.55rem", alignItems: "flex-start", minWidth: 0, padding: "0.7rem 0.75rem", borderRadius: "12px", background: "#eff6ff", color: "#1e3a8a", fontSize: "0.9rem", overflowWrap: "anywhere" }}><span aria-hidden="true">📄</span><span>{file.name}</span></div>)}
              </div>
            )}
          </section>
        </div></div></div>
        <div className="course-chat-panel" style={{ ...styles.rightPanel, minWidth: 0 }}><div style={styles.cardShell}><div style={styles.cardHeader}><h2 style={styles.cardTitle}>Chat with Professor DOTU</h2></div><div style={styles.cardBody}>
          <ChatWidget key={activeCourse.id} courseId={activeCourse.id} messages={activeCourse.messages} onMessagesChange={(messages) => updateActiveCourse((course) => ({ ...course, messages }))} />
        </div></div></div>
      </section>
    </main>
  );
}
