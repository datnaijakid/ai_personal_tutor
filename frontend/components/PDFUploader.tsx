"use client";

import { useState } from "react";

export default function PDFUploader() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [isUploading, setIsUploading] = useState(false);

  const [message, setMessage] = useState("");

  const [error, setError] = useState("");

  const [pageCount, setPageCount] = useState<number | null>(null);

  async function uploadFile() {
    if (!selectedFile) {
      return;
    }

    setIsUploading(true);
    setMessage("");
    setError("");
    setPageCount(null);

    try {
      const formData = new FormData();

      formData.append("file", selectedFile);

      const response = await fetch(
        "http://localhost:8000/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed."
        );
      }

      setMessage(data.message);

      setPageCount(data.page_count);

      console.log("Upload response:", data);
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          "Something went wrong while uploading the PDF."
        );
      }
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div>
      <h2>Upload your textbook</h2>

      <input
        type="file"
        accept=".pdf,application/pdf"
        onChange={(event) => {
          const file = event.target.files?.[0];

          if (file) {
            setSelectedFile(file);
            setMessage("");
            setError("");
            setPageCount(null);
          }
        }}
      />

      {selectedFile && (
        <p>
          Selected file: {selectedFile.name}
        </p>
      )}

      <button
        onClick={uploadFile}
        disabled={!selectedFile || isUploading}
      >
        {isUploading
          ? "Uploading and extracting..."
          : "Upload PDF"}
      </button>

      {message && (
        <p>
          {message}
        </p>
      )}

      {pageCount !== null && (
        <p>
          Pages extracted: {pageCount}
        </p>
      )}

      {error && (
        <p>
          Error: {error}
        </p>
      )}
    </div>
  );
}