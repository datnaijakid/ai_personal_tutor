import fitz
from pathlib import Path


def extract_text_from_pdf(file_path: str | Path) -> list[dict[str, int | str]]:
    """Return a JSON-serializable text representation of every PDF page."""
    with fitz.open(file_path) as document:
        return [
            {
                "page_number": page_number,
                "text": page.get_text(),
            }
            for page_number, page in enumerate(document, start=1)
        ]
