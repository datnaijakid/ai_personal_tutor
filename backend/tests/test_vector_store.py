import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
