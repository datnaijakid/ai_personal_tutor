"use client";

import { useEffect, useRef, useState } from "react";

const MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024;
const PDF_CONTENT_TYPES = new Set(["application/pdf", "application/x-pdf"]);
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").trim();

type UploadErrorResponse = { detail?: string };
type PDFUploaderProps = { onUploadComplete?: (fileName: string) => void };

const styles = {
  chooseButton: { display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.72rem 1rem", border: 0, borderRadius: "999px", background: "#2563eb", color: "#fff", fontWeight: 700, cursor: "pointer", boxShadow: "0 6px 14px rgba(37, 99, 235, 0.2)" },
  uploadButton: { marginTop: "0.75rem", padding: "0.58rem 0.9rem", border: 0, borderRadius: "10px", background: "#dbeafe", color: "#1e3a8a", fontWeight: 700, cursor: "pointer" },
  success: { margin: "0.85rem 0 0", padding: "0.65rem 0.75rem", borderRadius: "10px", background: "#ecfdf5", color: "#15803d", fontSize: "0.9rem", fontWeight: 600 },
  error: { margin: "0.85rem 0 0", padding: "0.65rem 0.75rem", borderRadius: "10px", background: "#fef2f2", color: "#b91c1c", fontSize: "0.9rem" },
};

async function validatePdf(file: File): Promise<string | null> {
  if (!file.name.toLowerCase().endsWith(".pdf")) return "Only PDF files are allowed.";
  if (!PDF_CONTENT_TYPES.has(file.type)) return "Only PDF files are allowed.";
  if (file.size > MAX_PDF_SIZE_BYTES) return "PDF files must be 25 MB or smaller.";
  const header = new Uint8Array(await file.slice(0, 5).arrayBuffer());
  return new TextDecoder().decode(header) === "%PDF-" ? null : "The uploaded file is not a valid PDF.";
}

export default function PDFUploader({ onUploadComplete }: PDFUploaderProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (successTimerRef.current) clearTimeout(successTimerRef.current);
  }, []);

  function clearFiles() {
    setSelectedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function showSuccess() {
    if (successTimerRef.current) clearTimeout(successTimerRef.current);
    setSuccessMessage("✓ PDF uploaded successfully!");
    successTimerRef.current = setTimeout(() => setSuccessMessage(""), 3000);
  }

  async function uploadFiles() {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setError("");

    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(new URL("/upload", API_BASE_URL).toString(), { method: "POST", body: formData });
        if (!response.ok) {
          const body = (await response.json().catch(() => null)) as UploadErrorResponse | null;
          throw new Error(`${file.name}: ${body?.detail || "Upload failed. Please try again."}`);
        }
        onUploadComplete?.(file.name);
      }
      showSuccess();
      clearFiles();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  async function selectFiles(files: File[]) {
    for (const file of files) {
      const validationError = await validatePdf(file);
      if (validationError) {
        clearFiles();
        setError(`${file.name}: ${validationError}`);
        return;
      }
    }
    setSelectedFiles(files);
    setError("");
  }

  return (
    <div>
      <input ref={fileInputRef} type="file" accept=".pdf,application/pdf,application/x-pdf" multiple disabled={uploading} style={{ display: "none" }} onChange={(event) => selectFiles(Array.from(event.target.files ?? []))} />
      <button type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading} style={{ ...styles.chooseButton, opacity: uploading ? 0.65 : 1 }}>
        <span aria-hidden="true">📄</span> Choose File
      </button>

      {selectedFiles.length > 0 && <div style={{ marginTop: "0.8rem", color: "#334155", fontSize: "0.9rem" }}>
        {selectedFiles.length} PDF{selectedFiles.length === 1 ? "" : "s"} selected
        <button type="button" onClick={uploadFiles} disabled={uploading} style={{ ...styles.uploadButton, opacity: uploading ? 0.65 : 1 }}>
          {uploading ? "Uploading..." : "Upload selected"}
        </button>
      </div>}
      {successMessage && <p role="status" style={styles.success}>{successMessage}</p>}
      {error && <p role="alert" style={styles.error}>{error}</p>}
    </div>
  );
}
