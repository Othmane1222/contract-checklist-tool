"""Evaluation runner. Usage: python -m eval.run --split dev --runs 2"""
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from openai import APIError

import ai
from ai import AIOutputError, check_contract
from checklists import load_checklist
from eval.articles import article_at, article_number, article_starts
from eval.data import GroundTruth, Manifest
from eval.scoring import consistency, score_item, summarize
from extract import extract_docx, extract_pdf
from verify import build_document, find_quote, verify_findings

EVAL_DIR = Path(__file__).parent
HELDOUT_COUNTER = EVAL_DIR / "heldout_runs.json"
RESULTS_LANGUAGE = "English"


def git_commit() -> str:
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
        return commit + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def read_heldout_count() -> int:
    if not HELDOUT_COUNTER.exists():
        return 0
    return json.loads(HELDOUT_COUNTER.read_text(encoding="utf-8"))["count"]


def record_heldout_run(commit: str) -> int:
    data = {"count": 0, "runs": []}
    if HELDOUT_COUNTER.exists():
        data = json.loads(HELDOUT_COUNTER.read_text(encoding="utf-8"))
    data["count"] += 1
    data["runs"].append({"date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": commit})
    HELDOUT_COUNTER.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data["count"]


def read_blocks(path: Path) -> list[dict]:
    data = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        return extract_pdf(data)
    if path.suffix.lower() == ".docx":
        return extract_docx(data)
    raise SystemExit(f"Unsupported file type: {path.name}")


def load_ground_truth(entry, checklist: dict) -> GroundTruth:
    path = EVAL_DIR / "ground_truth" / f"{entry.id}.json"
    if not path.exists():
        raise SystemExit(f"Missing ground truth: {path.name}")
    truth = GroundTruth.model_validate_json(path.read_text(encoding="utf-8"))
    if truth.contract_id != entry.id:
        raise SystemExit(f"{path.name}: contract_id is '{truth.contract_id}', expected '{entry.id}'")
    expected = {item["id"] for item in checklist["items"]}
    if set(truth.items) != expected:
        missing = sorted(expected - set(truth.items))
        unknown = sorted(set(truth.items) - expected)
        raise SystemExit(f"{path.name}: missing items {missing}, unknown items {unknown}")
    for item_id, label in truth.items.items():
        for article in label.articles:
            try:
                article_number(article)
            except ValueError:
                raise SystemExit(f"{path.name}: '{article}' in {item_id} is not an article number")
    return truth


def locate(finding: dict, label, document: str, headings: list) -> str | None:
    if not label.articles or finding["status"] != "quote_verified":
        return None
    wanted = {article_number(article) for article in label.articles}
    placed = []
    for quote in finding["quotes"]:
        start = find_quote(quote["text"], document)
        if start is not None:
            placed.append(article_at(start, headings))
    if not placed or all(number is None for number in placed):
        return "unplaced"
    return "inside" if any(number in wanted for number in placed) else "outside"


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.0%}"


def write_report(folder: Path, meta: dict, overall: dict, per_item: dict, consistency_rate, compared: int, failed: list) -> None:
    lines = [
        "# Evaluation report",
        "",
        "| | |",
        "|---|---|",
        f"| Date | {meta['date']} |",
        f"| Commit | {meta['commit']} |",
        f"| Model | {meta['model']} (temperature {meta['temperature']}, thinking {meta['thinking']}) |",
        f"| Split | {meta['split']}: {meta['contracts']} contracts × {meta['runs']} runs |",
        f"| Held-out runs so far | {meta['heldout_runs']} |",
        f"| Failed runs | {len(failed)} of {meta['contracts'] * meta['runs']} |",
        "",
        "## Overall",
        "",
        "| Metric | Result | Coverage |",
        "|---|---|---|",
        f"| Found accuracy | {pct(overall['found_accuracy'])} | {pct(overall['coverage'])} decided automatically ({overall['decided']} of {overall['total']}) |",
        f"| False \"missing\" | {overall['false_missing']} | |",
        f"| False \"present\" | {overall['false_present']} | |",
        f"| Sent to manual check | {overall['manual_unverified']} unverified, {overall['manual_possibly_present']} possibly present | |",
        f"| Risk: exact match | {pct(overall['risk_exact'])} | {overall['risk_scored']} of {overall['truth_present']} present items scored |",
        f"| Risk: within one level | {pct(overall['risk_within_one'])} | {overall['risk_scored']} of {overall['truth_present']} present items scored |",
        f"| High rated as Low | {overall['high_as_low']} | |",
        f"| Quote inside labelled article | {pct(overall['location_inside'])} | {overall['location_checked']} checked, {overall['location_unplaced']} could not be placed |",
        f"| Consistency across runs | {pct(consistency_rate)} | {compared} item results compared |",
        "",
        "## Per item",
        "",
        "| Item | Found accuracy | Coverage | False missing | False present | Manual check | Risk exact (scored) | Risk within one | High as Low |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for key, item in sorted(per_item.items()):
        manual = item["manual_unverified"] + item["manual_possibly_present"]
        lines.append(
            f"| {key} | {pct(item['found_accuracy'])} | {pct(item['coverage'])} | {item['false_missing']} | "
            f"{item['false_present']} | {manual} | {pct(item['risk_exact'])} ({item['risk_scored']}) | "
            f"{pct(item['risk_within_one'])} | {item['high_as_low']} |"
        )
    if failed:
        lines += ["", "## Failed runs", "", "| Contract | Run | Error |", "|---|---|---|"]
        lines += [f"| {entry['contract']} | {entry['run']} | {entry['error']} |" for entry in failed]
    (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the contract checker against labelled test contracts.")
    parser.add_argument("--split", choices=["dev", "heldout", "all"], default="dev")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--final", action="store_true", help="required to run the held-out set")
    args = parser.parse_args()

    if args.split in ("heldout", "all") and not args.final:
        sys.exit("The held-out set is for final numbers only. Add --final to run it.")
    if args.runs < 1:
        sys.exit("--runs must be at least 1.")

    manifest = Manifest.model_validate_json((EVAL_DIR / "manifest.json").read_text(encoding="utf-8"))
    entries = [entry for entry in manifest.contracts if args.split == "all" or entry.split == args.split]
    if not entries:
        sys.exit(f"No contracts in split '{args.split}'.")

    records = []
    answers_by_key = defaultdict(list)
    failed = []

    for entry in entries:
        checklist = load_checklist(entry.contract_type)
        truth = load_ground_truth(entry, checklist)
        try:
            blocks = read_blocks(EVAL_DIR / entry.file)
        except Exception as error:
            blocks = []
            reason = type(error).__name__
        else:
            reason = "NoTextFound"
        if not blocks:
            failed += [{"contract": entry.id, "run": run, "error": reason} for run in range(1, args.runs + 1)]
            print(f"{entry.id}: FAILED to read ({reason})")
            continue

        document, _ = build_document(blocks)
        headings = article_starts(blocks)

        for run in range(1, args.runs + 1):
            try:
                result = check_contract(checklist, blocks, RESULTS_LANGUAGE)
            except (AIOutputError, APIError) as error:
                failed.append({"contract": entry.id, "run": run, "error": type(error).__name__})
                print(f"{entry.id} run {run}: FAILED ({type(error).__name__})")
                continue

            findings, _ = verify_findings(result, blocks, checklist)
            for finding in findings:
                label = truth.items[finding["item_id"]]
                record = score_item(label, finding, locate(finding, label, document, headings))
                record.update(contract=entry.id, item=f"{entry.contract_type}/{finding['item_id']}", run=run)
                records.append(record)
                risk = finding["risk"] if record["outcome"] == "present" else None
                answers_by_key[(entry.id, finding["item_id"])].append((record["outcome"], risk))
            print(f"{entry.id} run {run}: ok")

    commit = git_commit()
    heldout_runs = record_heldout_run(commit) if args.split in ("heldout", "all") else read_heldout_count()
    meta = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": commit,
        "model": ai.MODEL,
        "temperature": ai.TEMPERATURE,
        "thinking": ai.THINKING,
        "split": args.split,
        "contracts": len(entries),
        "runs": args.runs,
        "heldout_runs": heldout_runs,
    }

    per_item_records = defaultdict(list)
    for record in records:
        per_item_records[record["item"]].append(record)
    per_item = {key: summarize(items) for key, items in per_item_records.items()}
    overall = summarize(records)
    consistency_rate, compared = consistency(answers_by_key)

    folder = EVAL_DIR / "reports" / datetime.now().strftime("%Y-%m-%d_%H%M")
    folder.mkdir(parents=True, exist_ok=True)
    write_report(folder, meta, overall, per_item, consistency_rate, compared, failed)
    (folder / "runs.json").write_text(
        json.dumps({"meta": meta, "failed": failed, "records": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Report written to {folder / 'report.md'}")


if __name__ == "__main__":
    main()