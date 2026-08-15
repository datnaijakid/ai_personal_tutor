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

            document_id = str(chunk.get("document_id") or "").strip()
            course_id = str(chunk.get("course_id") or "").strip()
            if not document_id or not course_id:
                raise ValueError("Every chunk must include non-empty document_id and course_id metadata.")

            chunk_id = str(
                chunk.get("id") or f"{document_id}:chunk:{chunk.get('chunk_number', len(ids) + 1)}"
            )
            metadata = {
                "document_id": str(document_id),
                "document_name": str(
                    chunk.get("document_name") or chunk.get("document") or document_id
                ),
                "course_id": course_id,
                "page_number": int(chunk.get("page_number", 0) or 0),
                "chunk_number": int(chunk.get("chunk_number", 0) or 0),
                "text": text,
            }

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

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
        course_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            return []

        query_embedding = self.embedding_service.embed([query.strip()])[0]
        filters = []
        if document_id:
            filters.append({"document_id": document_id})
        if course_id:
            filters.append({"course_id": course_id})

        where = None
        if len(filters) == 1:
            where = filters[0]
        elif filters:
            where = {"$and": filters}

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

    def delete_document(self, document_id: str, course_id: str) -> None:
        """Delete only one course-scoped document's vectors."""
        self.collection.delete(where={"$and": [{"document_id": document_id}, {"course_id": course_id}]})

    def expand_with_neighbors(
        self,
        matches: list[dict[str, Any]],
        neighbor_count: int = 1,
    ) -> list[dict[str, Any]]:
        """Add adjacent chunks from each matched document for answer context.

        Vector similarity finds the best passage, while its neighbouring chunks
        often contain a definition, qualification, or conclusion required to
        answer the question accurately.
        """
        if not matches or neighbor_count < 1:
            return matches

        anchors_by_document: dict[str, list[dict[str, Any]]] = {}
        document_order: list[str] = []
        for match in matches:
            metadata = match.get("metadata") or {}
            document_id = str(metadata.get("document_id") or "")
            chunk_number = metadata.get("chunk_number")
            if not document_id or not isinstance(chunk_number, int):
                continue
            if document_id not in anchors_by_document:
                anchors_by_document[document_id] = []
                document_order.append(document_id)
            anchors_by_document[document_id].append(match)

        expanded: list[dict[str, Any]] = []
        for document_id in document_order:
            anchors = anchors_by_document[document_id]
            course_id = str((anchors[0].get("metadata") or {}).get("course_id") or "")
            where = {"document_id": document_id}
            if course_id:
                where = {"$and": [{"document_id": document_id}, {"course_id": course_id}]}
            collection_result = self.collection.get(
                where=where,
                include=["documents", "metadatas"],
            )
            ids = collection_result.get("ids", [])
            documents = collection_result.get("documents", [])
            metadatas = collection_result.get("metadatas", [])

            retrieved_by_id = {str(match["id"]): match for match in anchors}
            selected_numbers = {
                number
                for anchor in anchors
                for number in range(
                    int(anchor["metadata"]["chunk_number"]) - neighbor_count,
                    int(anchor["metadata"]["chunk_number"]) + neighbor_count + 1,
                )
            }
            document_chunks: list[dict[str, Any]] = []
            for index, item_id in enumerate(ids):
                metadata = metadatas[index] if index < len(metadatas) else {}
                chunk_number = metadata.get("chunk_number")
                if chunk_number not in selected_numbers:
                    continue

                item_id = str(item_id)
                if item_id in retrieved_by_id:
                    document_chunks.append(retrieved_by_id[item_id])
                    continue

                nearest_anchor = min(
                    anchors,
                    key=lambda anchor: abs(
                        int(anchor["metadata"]["chunk_number"]) - int(chunk_number)
                    ),
                )
                document_chunks.append(
                    {
                        "id": item_id,
                        "text": documents[index] if index < len(documents) else "",
                        "metadata": metadata,
                        "score": nearest_anchor.get("score", 0.0),
                        "distance": nearest_anchor.get("distance", 0.0),
                        "neighbor_of": nearest_anchor["id"],
                    }
                )

            expanded.extend(
                sorted(
                    document_chunks,
                    key=lambda item: int((item.get("metadata") or {}).get("chunk_number", 0)),
                )
            )

        return expanded
