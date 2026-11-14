import pytest

from eval.articles import article_at, article_number, article_starts, chinese_to_int
from eval.data import ItemLabel
from eval.scoring import consistency, score_item, summarize
from verify import build_document, find_quote


@pytest.mark.parametrize("text, number", [
    ("三", 3), ("十", 10), ("十二", 12), ("二十", 20), ("二十三", 23),
    ("一百零五", 105), ("一百一十", 110), ("3", 3), ("12", 12),
])
def test_chinese_to_int(text, number):
    assert chinese_to_int(text) == number


def test_article_labels_accept_both_numeral_styles():
    assert article_number("第三条") == article_number("第3条") == article_number("3") == 3


BLOCKS = [
    {"kind": "paragraph", "number": 1, "text": "第一条 合同期限\n本合同期限一年。"},
    {"kind": "paragraph", "number": 2, "text": "第2条 工作内容\n乙方应遵守本合同第一条的约定。"},
]


def test_headings_found_at_line_start_only():
    # The mid-sentence reference to 第一条 in paragraph 2 must not count as a heading.
    assert [number for _, number in article_starts(BLOCKS)] == [1, 2]


def test_quote_position_maps_to_its_article():
    document, _ = build_document(BLOCKS)
    headings = article_starts(BLOCKS)
    assert article_at(find_quote("本合同期限一年。", document), headings) == 1
    assert article_at(find_quote("乙方应遵守本合同第一条的约定", document), headings) == 2


def finding(status="quote_verified", risk="High"):
    return {"status": status, "risk": risk, "quotes": []}


def test_false_missing_and_false_present_are_separate():
    assert score_item(ItemLabel(found=True, risk="High"), finding("not_found"), None)["found_result"] == "false_missing"
    assert score_item(ItemLabel(found=False), finding("quote_verified"), None)["found_result"] == "false_present"


def test_manual_check_is_neither_right_nor_wrong():
    records = [
        score_item(ItemLabel(found=True, risk="Low"), finding("unverified"), None),
        score_item(ItemLabel(found=True, risk="Low"), finding("quote_verified", "Low"), None),
    ]
    summary = summarize(records)
    assert summary["coverage"] == 0.5
    assert summary["found_accuracy"] == 1.0
    assert summary["manual_unverified"] == 1


def test_risk_scored_only_when_present_in_truth_and_result():
    assert "risk_exact" not in score_item(ItemLabel(found=False), finding("not_found"), None)
    assert "risk_exact" not in score_item(ItemLabel(found=True, risk="High"), finding("not_found"), None)


def test_high_rated_as_low_is_counted():
    record = score_item(ItemLabel(found=True, risk="High"), finding("quote_verified", "Low"), None)
    assert record["high_as_low"]
    assert not record["risk_within_one"]
    summary = summarize([record])
    assert summary["high_as_low"] == 1
    assert summary["risk_exact"] == 0.0


def test_within_one_level():
    record = score_item(ItemLabel(found=True, risk="High"), finding("quote_verified", "Medium"), None)
    assert record["risk_within_one"]
    assert not record["risk_exact"]


def test_found_label_requires_risk():
    with pytest.raises(ValueError):
        ItemLabel(found=True)


def test_consistency_counts_only_items_with_several_runs():
    rate, compared = consistency({
        ("a", "x"): [("present", "High"), ("present", "High")],
        ("a", "y"): [("present", "High"), ("missing", None)],
        ("b", "x"): [("missing", None)],
    })
    assert compared == 2
    assert rate == 0.5