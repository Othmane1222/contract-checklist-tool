from io import BytesIO

from docx import Document
from pypdf import PdfReader


def extract_pdf(data: bytes) -> list[dict]:
    reader = PdfReader(BytesIO(data))
    blocks = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            blocks.append({"kind": "page", "number": number, "text": text})
    return blocks


def extract_docx(data: bytes) -> list[dict]:
    document = Document(BytesIO(data))
    blocks = []
    number = 0
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            number += 1
            blocks.append({"kind": "paragraph", "number": number, "text": text})
    return blocks