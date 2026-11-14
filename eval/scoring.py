"""Scoring for the evaluation. Pure functions: no AI calls, no files."""
from collections import Counter

from eval.data import ItemLabel

RISK_LEVEL = {"Low": 0, "Medium": 1, "High": 2}
MANUAL = ("unverified", "possibly_present")


def classify(status: str) -> str:
    if status == "quote_verified":
        return "present"
    if status == "not_found":
        return "missing"
    return status


def score_item(label: ItemLabel, finding: dict, located: str | None) -> dict:
    outcome = classify(finding["status"])
    record = {"outcome": outcome, "risk": finding["risk"], "truth_found": label.found, "located": located}

    if outcome in MANUAL:
        record["found_result"] = "manual"
    elif label.found:
        record["found_result"] = "true_present" if outcome == "present" else "false_missing"
    else:
        record["found_result"] = "false_present" if outcome == "present" else "true_missing"

    # Risk is scored only when the item is really present and the tool found it.
    if label.found and outcome == "present":
        difference = abs(RISK_LEVEL[finding["risk"]] - RISK_LEVEL[label.risk])
        record["risk_exact"] = difference == 0
        record["risk_within_one"] = difference <= 1
        record["high_as_low"] = label.risk == "High" and finding["risk"] == "Low"
    return record


def ratio(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def summarize(records: list[dict]) -> dict:
    results = Counter(record["found_result"] for record in records)
    outcomes = Counter(record["outcome"] for record in records)
    total = len(records)
    decided = total - results["manual"]
    risk = [record for record in records if "risk_exact" in record]
    placed = [record for record in records if record["located"] in ("inside", "outside")]
    return {
        "total": total,
        "decided": decided,
        "coverage": ratio(decided, total),
        "found_accuracy": ratio(results["true_present"] + results["true_missing"], decided),
        "false_missing": results["false_missing"],
        "false_present": results["false_present"],
        "manual_unverified": outcomes["unverified"],
        "manual_possibly_present": outcomes["possibly_present"],
        "truth_present": sum(1 for record in records if record["truth_found"]),
        "risk_scored": len(risk),
        "risk_exact": ratio(sum(record["risk_exact"] for record in risk), len(risk)),
        "risk_within_one": ratio(sum(record["risk_within_one"] for record in risk), len(risk)),
        "high_as_low": sum(record["high_as_low"] for record in risk),
        "location_checked": len(placed),
        "location_inside": ratio(sum(record["located"] == "inside" for record in placed), len(placed)),
        "location_unplaced": sum(1 for record in records if record["located"] == "unplaced"),
    }


def consistency(answers_by_key: dict) -> tuple[float | None, int]:
    """Share of contract-and-item pairs where every run gave the same answer."""
    compared = [answers for answers in answers_by_key.values() if len(answers) >= 2]
    same = sum(1 for answers in compared if len(set(answers)) == 1)
    return ratio(same, len(compared)), len(compared)