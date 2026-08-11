import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.api.chat import ChatRequest, chat_endpoint
from app.services.vector_store import VectorStore


class VectorStoreTests(unittest.TestCase):
    def test_store_adds_and_queries_chunks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = VectorStore(persist_directory=str(Path(temp_dir) / "chroma_db"))
            try:
                store.add_chunks(
                    [
                        {
                            "id": "chunk_13",
                            "text": "Financial statements show the company had strong operating cash flow.",
                            "page_number": 13,
                            "document_id": "Chapter 1 slides.pdf",
                            "chunk_number": 13,
                        }
                    ]
                )

                results = store.search("cash flow in financial statements", top_k=5)
            finally:
                store.close()

        self.assertTrue(results)
        self.assertEqual(results[0]["id"], "chunk_13")
        self.assertIn("document_id", results[0]["metadata"])
        self.assertEqual(results[0]["metadata"]["page_number"], 13)

    def test_chat_endpoint_returns_relevant_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = VectorStore(persist_directory=str(Path(temp_dir) / "chroma_db"))
            try:
                store.add_chunks(
                    [
                        {
                            "id": "chunk_13",
                            "text": "Financial statements show the company had strong operating cash flow.",
                            "page_number": 13,
                            "document_id": "Chapter 1 slides.pdf",
                            "chunk_number": 13,
                        }
                    ]
                )

                persisted_path = str(Path(temp_dir) / "chroma_db")
                retrieved_store = VectorStore(persist_directory=persisted_path)
                try:
                    with patch("app.rag.VectorStore", return_value=retrieved_store):
                        response = asyncio.run(
                            chat_endpoint(ChatRequest(question="What does the cash flow in the financial statements say?"))
                        )
                finally:
                    retrieved_store.close()
            finally:
                store.close()

        self.assertIn("cash flow", response.answer.lower())
        self.assertTrue(response.sources)
        self.assertIn("Chapter 1 slides.pdf", response.sources[0])
        self.assertIn("Page 13", response.sources[0])

    def test_build_answer_uses_local_llm_when_available(self):
        results = [
            {
                "id": "chunk_13",
                "text": "Financial statements show the company had strong operating cash flow.",
                "metadata": {"document_id": "Chapter 1 slides.pdf", "page_number": 13},
                "score": 0.85,
            }
        ]

        with patch("app.rag.retrieve_relevant_chunks", return_value=results), patch(
            "app.rag.LocalLLMClient.generate",
            return_value="The company had strong operating cash flow according to the financial statements.",
        ), patch("app.rag.LocalLLMClient.is_available", return_value=True):
            response = build_answer("What does the cash flow say?")

        self.assertIn("strong operating cash flow", response["answer"].lower())
        self.assertIn("Chapter 1 slides.pdf", response["sources"][0])

    def test_build_answer_returns_no_sources_for_irrelevant_chunks(self):
        results = [
            {
                "id": "chunk_1",
                "text": "Photosynthesis converts light energy into chemical energy.",
                "metadata": {"document_id": "Biology.pdf", "page_number": 4},
                "score": 0.12,
            }
        ]

        with patch("app.rag.VectorStore") as vector_store:
            vector_store.return_value.search.return_value = results
            response = build_answer("What is the capital of France?")

        self.assertIn("couldn", response["answer"].lower())
        self.assertEqual(response["sources"], [])


from app.rag import build_answer


if __name__ == "__main__":
    unittest.main()
