"use client";

import { useRef, useState } from "react";

const MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024;
const PDF_CONTENT_TYPES = new Set(["application/pdf", "application/x-pdf"]);
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").trim();

type UploadErrorResponse = {
  detail?: string;
};

async function validatePdf(file: File): Promise<string | null> {
  if (!file.name.toLowerCase().endsWith(".pdf")) return "Only PDF files are allowed.";
  if (!PDF_CONTENT_TYPES.has(file.type)) return "Only PDF files are allowed.";
  if (file.size > MAX_PDF_SIZE_BYTES) return "PDF files must be 25 MB or smaller.";

  const header = new Uint8Array(await file.slice(0, 5).arrayBuffer());
  if (new TextDecoder().decode(header) !== "%PDF-") return "The uploaded file is not a valid PDF.";

  return null;
}

export default function PDFUploader() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  function clearFile() {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function uploadFile() {
    if (!selectedFile) {
      setError("Please select a PDF first.");
      return;
    }

    // The backend repeats these checks and remains the source of truth.
    const validationError = await validatePdf(selectedFile);
    if (validationError) {
      setError(validationError);
      setSuccessMessage("");
      clearFile();
      return;
    }

    setUploading(true);
    setError("");
    setSuccessMessage("");
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const uploadUrl = new URL("/upload", API_BASE_URL).toString();
      const response = await fetch(uploadUrl, { method: "POST", body: formData });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as UploadErrorResponse | null;
        throw new Error(body?.detail || "Upload failed. Please try again.");
      }

      setSuccessMessage("PDF uploaded successfully!");
      clearFile();
    } catch (error) {
      console.error(error);
      setError(error instanceof Error ? error.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h2>Upload your textbook</h2>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf,application/x-pdf"
        disabled={uploading}
        onChange={async (event) => {
          const file = event.target.files?.[0];
          if (!file) return;

          const validationError = await validatePdf(file);
          if (validationError) {
            clearFile();
            setError(validationError);
            setSuccessMessage("");
            return;
          }

          setSelectedFile(file);
          setError("");
          setSuccessMessage("");
        }}
      />

      {selectedFile && <p>Selected file: {selectedFile.name}</p>}
      {selectedFile && (
        <button onClick={uploadFile} disabled={uploading}>
          {uploading ? "Uploading..." : "Upload PDF"}
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      {successMessage && <p role="status">{successMessage}</p>}
    </div>
  );
}
