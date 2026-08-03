"use client";

import { useState } from "react";

export default function PDFUploader() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState(false);

  const [message, setMessage] = useState("");

  async function uploadFile() {
    if (!selectedFile) {
      setMessage("Please select a PDF first.");
      return;
    }

    setUploading(true);
    setMessage("");

    const formData = new FormData();

    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      console.log(data);

      setMessage("PDF uploaded successfully!");
    } catch (error) {
      console.error(error);

      setMessage("Upload failed. Please try again.");
    } finally {
      setUploading(false);
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
          }
        }}
      />

      {selectedFile && (
        <p>
          Selected file: {selectedFile.name}
        </p>
      )}

      {selectedFile && (
        <button
          onClick={uploadFile}
          disabled={uploading}
        >
          {uploading ? "Uploading..." : "Upload PDF"}
        </button>
      )}

      {message && (
        <p>{message}</p>
      )}
    </div>
  );
}