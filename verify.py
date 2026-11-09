import re
import unicodedata
from bisect import bisect_right

from schemas import CheckResult

MIN_QUOTE_LENGTH = 8
PUNCTUATION = str.maketrans({"。": ".", "“": '"', "”": '"', "‘": "'", "’": "'"})
ELLIPSIS = re.compile(r"\.{3,}")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(PUNCTUATION)
    return "".join(text.split())


def build_document(blocks: list[dict]) -> tuple[str, list[int]]:
    parts = []
    starts = []
    length = 0
    for block in blocks:
        starts.append(length)
        text = normalize(block["text"])
        parts.append(text)
        length += len(text)
    return "".join(parts), starts


def find_quote(quote: str, document: str) -> int | None:
    parts = [part for part in ELLIPSIS.split(normalize(quote)) if part]
    if sum(len(part) for part in parts) < MIN_QUOTE_LENGTH:
        return None
    start = None
    position = 0
    for part in parts:
        index = document.find(part, position)
        if index == -1:
            return None
        if start is None:
            start = index
        position = index + len(part)
    return start


def has_keyword(words: list[str], document: str) -> bool:
    return any(normalize(word) and normalize(word) in document for word in words)


def verify_findings(result: CheckResult, blocks: list[dict], checklist: dict) -> tuple[list[dict], dict]:
    document, starts = build_document(blocks)
    keywords = {item["id"]: item.get("keywords", []) for item in checklist["items"]}
    labels = {item["id"]: item.get("label", item["id"]) for item in checklist["items"]}
    stats = {"quotes_removed": 0, "locations_corrected": 0}
    findings = []

    for finding in result.results:
        quotes = []
        if finding.found:
            for quote in finding.quotes:
                start = find_quote(quote.text, document)
                if start is None:
                    stats["quotes_removed"] += 1
                    continue
                block = blocks[bisect_right(starts, start) - 1]
                location = {"kind": block["kind"], "number": block["number"]}
                if location != quote.location.model_dump():
                    stats["locations_corrected"] += 1
                quotes.append({"text": quote.text, "location": location})
            status = "quote_verified" if quotes else "unverified"
        elif has_keyword(keywords.get(finding.item_id, []), document):
            status = "possibly_present"
        else:
            status = "not_found"

        findings.append({
            "item_id": finding.item_id,
                        "label": labels.get(finding.item_id, finding.item_id),
            "found": finding.found,
            "risk": finding.risk,
            "explanation": finding.explanation,
            "plain_language": finding.plain_language if quotes else None,
            "status": status,
            "quotes": quotes,
        })

    return findings, stats