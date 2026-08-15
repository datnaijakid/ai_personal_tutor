from __future__ import annotations

from typing import Any

from app.services.local_llm import LocalLLMClient
from app.services.vector_store import VectorStore


LOCAL_LLM = LocalLLMClient()

# Chroma returns the nearest chunks for every query, including queries that have
# no meaningful relationship to an uploaded document. Keep only chunks with a
# sufficiently strong cosine-similarity score before using them for chat.
MIN_CHAT_RELEVANCE_SCORE = 0.40
INSUFFICIENT_CONTEXT_TOKEN = "INSUFFICIENT_CONTEXT"
UNKNOWN_ANSWER = "I can't find this in your uploaded material."


def build_source_label(metadata: dict[str, Any]) -> str:
    document_name = metadata.get("document_name") or metadata.get("document_id") or "Uploaded document"
    page_number = metadata.get("page_number")
    if page_number is not None:
        return f"{document_name} (Page {page_number})"
    return str(document_name)


def is_extractively_grounded(answer: str, context: str) -> bool:
    """Accept model text only when it is a verbatim passage from retrieved text."""
    normalized_answer = " ".join(answer.split()).casefold()
    normalized_context = " ".join(context.split()).casefold()
    return bool(normalized_answer) and normalized_answer in normalized_context


def retrieve_relevant_chunks(
    question: str,
    top_k: int = 5,
    document_id: str | None = None,
    course_id: str | None = None,
    min_score: float = MIN_CHAT_RELEVANCE_SCORE,
) -> list[dict[str, Any]]:
    if not question or not question.strip() or not course_id or not course_id.strip():
        return []

    vector_store = VectorStore()
    try:
        results = vector_store.search(
            question.strip(),
            top_k=top_k,
            document_id=document_id,
            course_id=course_id.strip(),
        )
        relevant_results = [
            result
            for result in results
            if float(result.get("score", 0.0)) >= min_score
        ]
        if not relevant_results:
            return []
        return vector_store.expand_with_neighbors(relevant_results)
    finally:
        vector_store.close()


def build_answer(
    question: str,
    top_k: int = 5,
    document_id: str | None = None,
    course_id: str | None = None,
) -> dict[str, Any]:
    results = retrieve_relevant_chunks(
        question,
        top_k=top_k,
        document_id=document_id,
        course_id=course_id,
    )

    if not results:
        return {
            "answer": UNKNOWN_ANSWER,
            "sources": [],
        }

    # A PDF can be uploaded more than once and neighbouring chunks overlap.
    # Do not give the model (or the fallback) the same passage repeatedly.
    unique_texts: set[str] = set()
    answer_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, int, str]] = set()

    for result in results:
        text = (result.get("text") or "").strip()
        if not text:
            continue

        normalized_text = " ".join(text.split()).casefold()
        if normalized_text in unique_texts:
            continue
        unique_texts.add(normalized_text)

        metadata = result.get("metadata") or {}
        page = int(metadata.get("page_number") or 0)
        source_key = (str(metadata.get("document_id") or ""), page, str(result.get("id") or ""))
        # Neighbour chunks add context but are not independent search evidence.
        # Show only the strongest three source chunks to keep citations useful.
        if not result.get("neighbor_of") and source_key not in seen_sources and len(sources) < 3:
            seen_sources.add(source_key)
            sources.append({
                "document": metadata.get("document_name") or metadata.get("document_id") or "Uploaded document",
                "document_id": metadata.get("document_id"),
                "page": page,
                "chunk_id": result.get("id"),
            })
        answer_parts.append(text)

    if not answer_parts:
        return {"answer": UNKNOWN_ANSWER, "sources": []}

    context = "\n\n".join(answer_parts)
    citation = f" [p.{sources[0]['page']}]" if sources and sources[0]["page"] else ""

    if LOCAL_LLM.is_available():
        generated = LOCAL_LLM.generate(question, context)
        if generated.strip() and generated.strip().casefold() != INSUFFICIENT_CONTEXT_TOKEN.casefold():
            return {
                "answer": generated + citation,
                "sources": sources,
            }
        # Retrieval already passed the confidence threshold. If the optional
        # model declines or rewrites its answer, preserve the supported result
        # by returning the source passage instead of a false refusal.

    # The LLM is optional.  If it is unavailable, returning five unedited
    # search chunks is confusing and often looks like a repeated answer.
    fallback = "I found this relevant passage in the uploaded material:\n\n"
    fallback += answer_parts[0] + citation

    return {
        "answer": fallback,
        "sources": sources,
    }
