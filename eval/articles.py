"""Find article headings (第三条 / 第3条) and map text positions to articles."""
import re

from verify import build_document, normalize

NUMERALS = r"[0-9０-９]+|[零〇一二两三四五六七八九十百]+"
HEADING = re.compile(rf"^[ \t\u3000]*第\s*({NUMERALS})\s*条", re.MULTILINE)
LABEL = re.compile(rf"第?\s*({NUMERALS})\s*条?")
DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def chinese_to_int(text: str) -> int:
    if text.isdigit():
        return int(text)
    total = 0
    current = 0
    for char in text:
        if char == "百":
            total += (current or 1) * 100
            current = 0
        elif char == "十":
            total += (current or 1) * 10
            current = 0
        else:
            current = DIGITS[char]
    return total + current


def article_number(label: str) -> int:
    match = LABEL.fullmatch(label.strip())
    if not match:
        raise ValueError(f"Not an article label: {label}")
    return chinese_to_int(match.group(1))


def article_starts(blocks: list[dict]) -> list[tuple[int, int]]:
    """(position in the normalized document, article number) for every heading at the start of a line."""
    _, starts = build_document(blocks)
    headings = []
    for block, start in zip(blocks, starts):
        for match in HEADING.finditer(block["text"]):
            offset = len(normalize(block["text"][: match.start()]))
            headings.append((start + offset, chinese_to_int(match.group(1))))
    return sorted(headings)


def article_at(position: int, headings: list[tuple[int, int]]) -> int | None:
    current = None
    for start, number in headings:
        if start > position:
            break
        current = number
    return current