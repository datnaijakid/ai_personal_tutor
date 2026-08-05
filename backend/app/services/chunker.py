from collections.abc import Iterable, Mapping


def chunk_pages(
    pages: Iterable[Mapping[str, int | str]],
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[dict[str, int | str]]:
    """Split extracted page text into overlapping, JSON-serializable chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be zero or greater and smaller than chunk_size.")

    chunks: list[dict[str, int | str]] = []
    step = chunk_size - overlap

    for page in pages:
        page_number = page["page_number"]
        text = str(page["text"]).strip()
        if not text:
            continue

        for start in range(0, len(text), step):
            chunk_text = text[start : start + chunk_size]
            if not chunk_text:
                break
            chunks.append(
                {
                    "chunk_number": len(chunks) + 1,
                    "page_number": page_number,
                    "start_char": start,
                    "end_char": start + len(chunk_text),
                    "text": chunk_text,
                }
            )
            if start + chunk_size >= len(text):
                break

    return chunks
