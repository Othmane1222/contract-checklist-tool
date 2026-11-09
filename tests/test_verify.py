from schemas import CheckResult, Finding, Location, Quote
from verify import normalize, verify_findings

BLOCKS = [
    {"kind": "page", "number": 1, "text": "第一条 合同期限\n本合同为固定期限劳动合同，期限一年。其中试用期为六个月。试用期工"},
    {"kind": "page", "number": 2, "text": "资为正式工资的 70%。\n第四条 保密义务"},
]
CHECKLIST = {
    "items": [
        {"id": "probation", "keywords": ["试用期"]},
        {"id": "termination", "keywords": ["解除合同"]},
    ]
}


def make_finding(item_id="probation", found=True, quotes=()):
    return Finding(
        item_id=item_id,
        found=found,
        risk="High",
        explanation="Test.",
        quotes=[Quote(text=text, location=Location(kind="page", number=page)) for text, page in quotes],
    )


def check(finding):
    findings, stats = verify_findings(CheckResult(results=[finding]), BLOCKS, CHECKLIST)
    return findings[0], stats


def test_normalize_removes_spaces_and_unifies_punctuation():
    assert normalize("试用期 为\n六个月。“好”") == '试用期为六个月."好"'


def test_quote_across_page_break_is_verified():
    finding, stats = check(make_finding(quotes=[("试用期工资为正式工资的70%", 1)]))
    assert finding["status"] == "quote_verified"
    assert stats == {"quotes_removed": 0, "locations_corrected": 0}


def test_wrong_location_is_corrected():
    finding, stats = check(make_finding(quotes=[("其中试用期为六个月", 2)]))
    assert finding["quotes"][0]["location"] == {"kind": "page", "number": 1}
    assert stats["locations_corrected"] == 1


def test_invented_quote_is_removed():
    finding, stats = check(make_finding(quotes=[("其中试用期为三个月", 1)]))
    assert finding["status"] == "unverified"
    assert finding["quotes"] == []
    assert stats["quotes_removed"] == 1


def test_short_quote_does_not_count():
    finding, _ = check(make_finding(quotes=[("试用期为六个月", 1)]))
    assert finding["status"] == "unverified"


def test_ellipsis_parts_must_appear_in_order():
    in_order, _ = check(make_finding(quotes=[("本合同为固定期限……试用期为六个月", 1)]))
    reversed_order, _ = check(make_finding(quotes=[("试用期为六个月……本合同为固定期限", 1)]))
    assert in_order["status"] == "quote_verified"
    assert reversed_order["status"] == "unverified"


def test_not_found_with_keyword_is_possibly_present():
    finding, _ = check(make_finding(found=False))
    assert finding["status"] == "possibly_present"


def test_not_found_drops_quotes():
    finding, _ = check(make_finding(item_id="termination", found=False, quotes=[("其中试用期为六个月", 1)]))
    assert finding["status"] == "not_found"
    assert finding["quotes"] == []