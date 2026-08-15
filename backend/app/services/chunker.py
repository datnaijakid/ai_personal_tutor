from collections.abc import Iterable, Mapping
import re


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Return sentence spans while retaining their page offsets."""
    sentences: list[tuple[int, int, str]] = []
    start = 0
    for boundary in _SENTENCE_BOUNDARY.finditer(text):
        end = boundary.start()
        sentence = text[start:end].strip()
        if sentence:
            offset = len(text[start:end]) - len(text[start:end].lstrip())
            sentences.append((start + offset, end, sentence))
        start = boundary.end()

    sentence = text[start:].strip()
    if sentence:
        offset = len(text[start:]) - len(text[start:].lstrip())
        sentences.append((start + offset, len(text), sentence))
    return sentences


def _chunk_long_sentence(
    text: str, page_number: int, chunk_size: int, overlap: int, first_chunk_number: int
) -> list[dict[str, int | str]]:
    """Use character windows only when one sentence exceeds the chunk limit."""
    chunks: list[dict[str, int | str]] = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk_text = text[start : start + chunk_size]
        chunks.append(
            {
                "chunk_number": first_chunk_number + len(chunks),
                "page_number": page_number,
                "start_char": start,
                "end_char": start + len(chunk_text),
                "text": chunk_text,
            }
        )
        if start + chunk_size >= len(text):
            break
    return chunks


def chunk_pages(
    pages: Iterable[Mapping[str, int | str]],
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[dict[str, int | str]]:
    """Create sentence-complete chunks with trailing-sentence context overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be zero or greater and smaller than chunk_size.")

    chunks: list[dict[str, int | str]] = []

    for page in pages:
        page_number = page["page_number"]
        text = str(page["text"]).strip()
        if not text:
            continue

        sentences = _split_sentences(text)
        current: list[tuple[int, int, str]] = []

        def emit_current() -> None:
            if current:
                chunks.append(
                    {
                        "chunk_number": len(chunks) + 1,
                        "page_number": page_number,
                        "start_char": current[0][0],
                        "end_char": current[-1][1],
                        "text": " ".join(sentence[2] for sentence in current),
                    }
                )

        for sentence in sentences:
            if len(sentence[2]) > chunk_size:
                emit_current()
                current.clear()
                chunks.extend(
                    _chunk_long_sentence(
                        sentence[2], page_number, chunk_size, overlap, len(chunks) + 1
                    )
                )
                continue

            candidate = " ".join(item[2] for item in [*current, sentence])
            if current and len(candidate) > chunk_size:
                emit_current()

                # Copy whole trailing sentences into the next chunk as context.
                context: list[tuple[int, int, str]] = []
                context_length = 0
                for item in reversed(current):
                    item_length = len(item[2]) + (1 if context else 0)
                    if context and context_length + item_length > overlap:
                        break
                    context.insert(0, item)
                    context_length += item_length

                while context and len(" ".join(item[2] for item in [*context, sentence])) > chunk_size:
                    context.pop(0)
                current = [*context, sentence]
            else:
                current.append(sentence)

        emit_current()

    return chunks
