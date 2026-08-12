from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from app.services.embeddings import get_embedding_service


class VectorStore:
    """Persist chunk text and embeddings in a local ChromaDB collection."""

    def __init__(
        self,
        persist_directory: str | Path = "chroma_db",
        collection_name: str = "pdf_chunks",
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_service = get_embedding_service()

    def close(self) -> None:
        """Close the underlying Chroma client and release file handles."""
        if hasattr(self, "client"):
            self.client.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def add_chunks(self, chunks: list[dict[str, Any]]) -> list[str]:
        if not chunks:
            return []

        documents = []
        ids = []
        metadatas = []
        for chunk in chunks:
            text = str(chunk.get("text", "")).strip()
            if not text:
                continue

            chunk_id = str(chunk.get("id") or f"chunk_{chunk.get('chunk_number', len(ids) + 1)}")
            document_id = chunk.get("document_id") or chunk.get("document") or "unknown_document"
            metadata = {
                "document_id": str(document_id),
                "page_number": int(chunk.get("page_number", 0) or 0),
                "chunk_number": int(chunk.get("chunk_number", 0) or 0),
            }
            if "document" in chunk:
                metadata["document"] = str(chunk["document"])
            if "start_char" in chunk:
                metadata["start_char"] = int(chunk["start_char"])
            if "end_char" in chunk:
                metadata["end_char"] = int(chunk["end_char"])

            documents.append(text)
            ids.append(chunk_id)
            metadatas.append(metadata)

        if not documents:
            return []

        embeddings = self.embedding_service.embed(documents)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return ids

    def replace_chunks(self, chunks: list[dict[str, Any]]) -> list[str]:
        """Replace the searchable document when a new PDF is uploaded."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"},
        )
        return self.add_chunks(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            return []

        query_embedding = self.embedding_service.embed([query.strip()])[0]
        where = {"document_id": document_id} if document_id else None

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, min(int(top_k), 25)),
            where=where,
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        results = []
        for index, item_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 0.0
            score = max(0.0, min(1.0, 1.0 - float(distance)))
            results.append(
                {
                    "id": item_id,
                    "text": documents[index] if index < len(documents) else "",
                    "metadata": metadata,
                    "distance": float(distance),
                    "score": score,
                }
            )
        return results
