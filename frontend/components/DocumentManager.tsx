"use client";

import { useCallback, useEffect, useState } from "react";

type Document = { document_id: string; filename: string; status: string };
const labels: Record<string, string> = { pending: "Pending", processing: "Processing", completed: "Completed", failed: "Failed", indexing: "Processing", indexed: "Completed" };
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

function apiUrl(path: string) {
  return API_BASE_URL ? new URL(path, API_BASE_URL).toString() : path;
}

export default function DocumentManager({ courseId, refreshKey }: { courseId: string; refreshKey: number }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState("");
  const load = useCallback(async () => { try { const response = await fetch(apiUrl(`/documents?course_id=${encodeURIComponent(courseId)}`)); if (!response.ok) throw new Error("Unable to load documents."); setDocuments((await response.json()).documents ?? []); setError(""); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load documents."); } }, [courseId]);
  useEffect(() => { const timeoutId = setTimeout(() => void load(), 0); return () => clearTimeout(timeoutId); }, [load, refreshKey]);
  const action = async (document: Document, operation: "delete" | "reindex" | "rename") => {
    const filename = operation === "rename" ? window.prompt("Document name", document.filename)?.trim() : undefined;
    if ((operation === "rename" && !filename) || (operation === "delete" && !window.confirm(`Delete ${document.filename}?`))) return;
    const suffix = operation === "reindex" ? "/reindex" : "";
    const response = await fetch(apiUrl(`/documents/${document.document_id}${suffix}?course_id=${encodeURIComponent(courseId)}`), { method: operation === "delete" ? "DELETE" : operation === "rename" ? "PATCH" : "POST", headers: operation === "rename" ? { "Content-Type": "application/json" } : undefined, body: operation === "rename" ? JSON.stringify({ course_id: courseId, filename }) : undefined });
    if (!response.ok) { setError((await response.json().catch(() => null))?.detail ?? "Document action failed."); return; }
    await load();
  };
  return <section style={{ marginTop: "1.25rem" }}><strong>Documents</strong>{error && <p role="alert" style={{ color: "#b91c1c" }}>{error}</p>}{documents.length === 0 ? <p>No PDFs uploaded yet.</p> : <div style={{ display: "grid", gap: "0.55rem", marginTop: "0.75rem" }}>{documents.map((document) => <div key={document.document_id} style={{ padding: "0.7rem", borderRadius: "12px", background: "#eff6ff" }}><div style={{ fontWeight: 700 }}>{document.filename}</div><div>Status: {labels[document.status] ?? document.status}</div><button onClick={() => action(document, "rename")}>Rename</button> <button onClick={() => action(document, "reindex")}>Re-index</button> <button onClick={() => action(document, "delete")}>Delete</button></div>)}</div>}</section>;
}
