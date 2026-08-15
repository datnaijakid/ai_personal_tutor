import asyncio
import json
from io import BytesIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import UploadFile

from app.api import upload
from app.services.chunker import chunk_pages
from app.services.pdf_processor import extract_text_from_pdf


def make_pdf_bytes(*page_texts: str) -> bytes:
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


class PdfProcessingTests(unittest.TestCase):
    def test_processor_returns_page_numbered_text(self):
        with TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "textbook.pdf"
            pdf_path.write_bytes(make_pdf_bytes("First page", "Second page"))

            pages = extract_text_from_pdf(pdf_path)

        self.assertEqual([page["page_number"] for page in pages], [1, 2])
        self.assertIn("First page", pages[0]["text"])
        self.assertIn("Second page", pages[1]["text"])

    def test_chunker_preserves_page_numbers_and_overlap(self):
        chunks = chunk_pages(
            [{"page_number": 3, "text": "abcdefghij"}],
            chunk_size=5,
            overlap=2,
        )

        self.assertEqual([chunk["text"] for chunk in chunks], ["abcde", "defgh", "ghij"])
        self.assertEqual([chunk["page_number"] for chunk in chunks], [3, 3, 3])
        self.assertEqual([chunk["chunk_number"] for chunk in chunks], [1, 2, 3])
        self.assertEqual([chunk["start_char"] for chunk in chunks], [0, 3, 6])

    def test_chunker_rejects_invalid_overlap(self):
        with self.assertRaises(ValueError):
            chunk_pages([], chunk_size=100, overlap=100)

    def test_chunker_keeps_sentences_whole_and_repeats_context(self):
        text = (
            "The nephron establishes a salt gradient in the kidney medulla. "
            "That gradient provides the driving force for water reabsorption. "
            "Water reabsorption concentrates the urine before it leaves the kidney."
        )

        chunks = chunk_pages([{"page_number": 7, "text": text}], chunk_size=140, overlap=80)

        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0]["text"].endswith("reabsorption."))
        self.assertTrue(chunks[1]["text"].startswith("That gradient"))
        self.assertIn("Water reabsorption concentrates", chunks[1]["text"])

    def test_upload_saves_pdf_and_chunked_json(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original_upload_directory = upload.UPLOAD_DIR
            original_extracted_directory = upload.EXTRACTED_DIR
            upload.UPLOAD_DIR = root / "uploads"
            upload.EXTRACTED_DIR = root / "extracted"
            try:
                with patch("app.api.upload.VectorStore"):
                    result = asyncio.run(
                        upload.upload_pdf(
                            UploadFile(
                                filename="textbook.pdf",
                                file=BytesIO(make_pdf_bytes("Machine-readable text")),
                                headers={"content-type": "application/pdf"},
                            ),
                            course_id="biology",
                        )
                    )
            finally:
                upload.UPLOAD_DIR = original_upload_directory
                upload.EXTRACTED_DIR = original_extracted_directory

            stored_pdf_path = root / "uploads" / result["stored_filename"]
            processed_path = Path(result["processed_file"])
            self.assertTrue(stored_pdf_path.exists())
            self.assertTrue(processed_path.exists())
            processed_document = json.loads(processed_path.read_text(encoding="utf-8"))

        self.assertEqual(result["page_count"], 1)
        self.assertEqual(result["chunk_count"], 1)
        self.assertEqual(processed_document["original_filename"], "textbook.pdf")
        self.assertTrue(processed_document["document_id"])
        self.assertEqual(processed_document["course_id"], "biology")
        self.assertEqual(processed_document["stored_pdf_path"], str(stored_pdf_path))
        self.assertEqual(processed_document["page_count"], 1)
        self.assertEqual(processed_document["chunk_count"], 1)
        self.assertIn("Machine-readable text", processed_document["pages"][0]["text"])
        self.assertIn("Machine-readable text", processed_document["chunks"][0]["text"])
        self.assertEqual(
            set(processed_document["chunks"][0]),
            {"document_id", "document_name", "course_id", "page_number", "chunk_number", "text"},
        )
        self.assertEqual(processed_document["chunks"][0]["document_name"], "textbook.pdf")

    def test_upload_assigns_distinct_document_ids_and_adds_each_document(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            original_upload_directory = upload.UPLOAD_DIR
            original_extracted_directory = upload.EXTRACTED_DIR
            upload.UPLOAD_DIR = root / "uploads"
            upload.EXTRACTED_DIR = root / "extracted"
            try:
                with patch("app.api.upload.VectorStore") as store_class:
                    results = [
                        asyncio.run(upload.upload_pdf(UploadFile(filename="chapter.pdf", file=BytesIO(make_pdf_bytes(text)), headers={"content-type": "application/pdf"}), course_id=course))
                        for text, course in (("Assets and liabilities", "accounting"), ("Cells have membranes", "biology"))
                    ]
            finally:
                upload.UPLOAD_DIR = original_upload_directory
                upload.EXTRACTED_DIR = original_extracted_directory

        self.assertNotEqual(results[0]["document_id"], results[1]["document_id"])
        self.assertEqual(store_class.return_value.add_chunks.call_count, 2)
        first_chunks = store_class.return_value.add_chunks.call_args_list[0].args[0]
        second_chunks = store_class.return_value.add_chunks.call_args_list[1].args[0]
        self.assertEqual(first_chunks[0]["course_id"], "accounting")
        self.assertEqual(second_chunks[0]["course_id"], "biology")
        self.assertNotEqual(first_chunks[0]["id"], second_chunks[0]["id"])


if __name__ == "__main__":
    unittest.main()
