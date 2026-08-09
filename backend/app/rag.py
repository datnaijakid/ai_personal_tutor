from __future__ import annotations

from typing import Any

from app.services.local_llm import LocalLLMClient
from app.services.vector_store import VectorStore


LOCAL_LLM = LocalLLMClient()


def build_source_label(metadata: dict[str, Any]) -> str:
    document_name = metadata.get("document") or metadata.get("document_id") or "Uploaded document"
    page_number = metadata.get("page_number")
    if page_number is not None:
        return f"{document_name} (Page {page_number})"
    return str(document_name)


def retrieve_relevant_chunks(
    question: str,
    top_k: int = 5,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    if not question or not question.strip():
        return []

    vector_store = VectorStore()
    try:
        return vector_store.search(question.strip(), top_k=top_k, document_id=document_id)
    finally:
        vector_store.close()


def build_answer(
    question: str,
    top_k: int = 5,
    document_id: str | None = None,
) -> dict[str, Any]:
    results = retrieve_relevant_chunks(question, top_k=top_k, document_id=document_id)

    if not results:
        return {
            "answer": "I couldn’t find relevant material in the uploaded PDFs for that question.",
            "sources": [],
        }

    answer_parts: list[str] = []
    sources: list[str] = []

    for result in results:
        text = (result.get("text") or "").strip()
        if not text:
            continue

        metadata = result.get("metadata") or {}
        source_label = build_source_label(metadata)
        if source_label not in sources:
            sources.append(source_label)
        answer_parts.append(text)

    context = "\n\n".join(answer_parts)

    if LOCAL_LLM.is_available():
        generated = LOCAL_LLM.generate(question, context)
        if generated:
            return {
                "answer": generated,
                "sources": sources,
            }

    fallback = "Based on the uploaded material:\n\n"
    for index, text in enumerate(answer_parts, start=1):
        fallback += f"{index}. {text[:500].strip()}\n\n"

    return {
        "answer": fallback,
        "sources": sources,
    }
