from pathlib import Path

from pypdf import PdfReader


def load_resume(file_path: str) -> str:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return _load_txt(path)
    elif suffix == ".pdf":
        return _load_pdf(path)
    else:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. Please use a .txt or .pdf file."
        )


def _load_txt(path: Path) -> str:
    """Load plain text resume."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"Loaded TXT resume: {path.name} ({len(text)} characters)")
    return text


def _load_pdf(path: Path) -> str:
    """Load PDF resume by extracting all page text."""
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)

    text = "\n\n".join(pages)
    print(
        f"Loaded PDF resume: {path.name} "
        f"({len(reader.pages)} pages, {len(text)} characters)"
    )
    return text
