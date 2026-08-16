from __future__ import annotations

import json
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


def build_quiz_question(course_id: str, topic: str | None = None) -> dict[str, Any] | str | None:
    """Generate a quiz only after course-scoped textbook retrieval succeeds."""
    retrieval_query = topic.strip() if topic and topic.strip() else "important concepts, definitions, and key ideas"
    results = retrieve_relevant_chunks(retrieval_query, top_k=3, course_id=course_id)
    if not results:
        return None

    # Use retrieved text as the model's entire knowledge boundary and retain the
    # strongest matched chunk as the visible source citation.
    passages: list[str] = []
    seen: set[str] = set()
    source: dict[str, Any] | None = None
    for result in results:
        text = (result.get("text") or "").strip()
        if not text or " ".join(text.split()).casefold() in seen:
            continue
        seen.add(" ".join(text.split()).casefold())
        passages.append(text)
        if source is None and not result.get("neighbor_of"):
            metadata = result.get("metadata") or {}
            source = {
                "document": metadata.get("document_name") or metadata.get("document_id") or "Uploaded document",
                "document_id": metadata.get("document_id"),
                "page": int(metadata.get("page_number") or 0),
                "chunk_id": result.get("id"),
            }
    if not passages or source is None:
        return None
    if not LOCAL_LLM.is_available():
        return "LLM_UNAVAILABLE"

    raw_quiz = LOCAL_LLM.generate_quiz("\n\n".join(passages), topic)
    try:
        quiz = json.loads(raw_quiz)
        question = str(quiz["question"]).strip()
        options = [str(option).strip() for option in quiz["options"]]
        correct_option = int(quiz["correct_option"])
        explanation = str(quiz["explanation"]).strip()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not question or not explanation or len(options) != 4 or any(not option for option in options) or correct_option not in range(4):
        return None
    return {
        "question": question,
        "options": options,
        "correct_option": correct_option,
        "explanation": explanation,
        "source": source,
    }


def build_quiz_questions(course_id: str, topics: str | None, question_count: int) -> list[dict[str, Any]] | str | None:
    """Retrieve each comma-separated topic independently before creating a quiz set."""
    selected_topics = [topic.strip() for topic in (topics or "").split(",") if topic.strip()] or [None]
    questions: list[dict[str, Any]] = []
    for index in range(question_count):
        question = build_quiz_question(course_id, selected_topics[index % len(selected_topics)])
        if question in (None, "LLM_UNAVAILABLE"):
            return question
        questions.append(question)
    return questions


def build_flashcard(course_id: str, topic: str | None = None) -> dict[str, Any] | str | None:
    """Generate a flashcard after retrieving course-scoped textbook passages."""
    retrieval_query = topic.strip() if topic and topic.strip() else "important concepts, definitions, and key ideas"
    results = retrieve_relevant_chunks(retrieval_query, top_k=3, course_id=course_id)
    if not results:
        return None

    passages: list[str] = []
    seen: set[str] = set()
    source: dict[str, Any] | None = None
    for result in results:
        text = (result.get("text") or "").strip()
        normalized = " ".join(text.split()).casefold()
        if not text or normalized in seen:
            continue
        seen.add(normalized)
        passages.append(text)
        if source is None and not result.get("neighbor_of"):
            metadata = result.get("metadata") or {}
            source = {
                "document": metadata.get("document_name") or metadata.get("document_id") or "Uploaded document",
                "document_id": metadata.get("document_id"),
                "page": int(metadata.get("page_number") or 0),
                "chunk_id": result.get("id"),
            }
    if not passages or source is None:
        return None
    if not LOCAL_LLM.is_available():
        return "LLM_UNAVAILABLE"
    try:
        card = json.loads(LOCAL_LLM.generate_flashcard("\n\n".join(passages), topic))
        front = str(card["front"]).strip()
        back = str(card["back"]).strip()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not front or not back:
        return None
    return {"front": front, "back": back, "source": source}


def build_chapter_summary(course_id: str, topic: str) -> dict[str, Any] | str | None:
    """Retrieve chapter-scoped passages and generate a grounded study summary."""
    results = retrieve_relevant_chunks(topic, top_k=5, course_id=course_id)
    if not results:
        return None
    passages: list[str] = []
    seen: set[str] = set()
    sources: list[dict[str, Any]] = []
    for result in results:
        text = (result.get("text") or "").strip()
        normalized = " ".join(text.split()).casefold()
        if not text or normalized in seen:
            continue
        seen.add(normalized)
        passages.append(text)
        if not result.get("neighbor_of") and len(sources) < 3:
            metadata = result.get("metadata") or {}
            sources.append({"document": metadata.get("document_name") or metadata.get("document_id") or "Uploaded document", "document_id": metadata.get("document_id"), "page": int(metadata.get("page_number") or 0), "chunk_id": result.get("id")})
    if not passages or not sources:
        return None
    if not LOCAL_LLM.is_available():
        return "LLM_UNAVAILABLE"
    try:
        summary = json.loads(LOCAL_LLM.generate_summary("\n\n".join(passages), topic))
        title = str(summary["title"]).strip()
        points = [str(point).strip() for point in summary["points"] if str(point).strip()]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not title or not 1 <= len(points) <= 8:
        return None
    return {"title": title, "points": points, "sources": sources}
