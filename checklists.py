import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"
CONTRACT_TYPES = ("employment", "lease", "business")
LANGUAGES = ("en", "es", "zh")


def load_checklist(contract_type: str) -> dict:
    if contract_type not in CONTRACT_TYPES:
        raise ValueError(f"Unknown contract type: {contract_type}")
    path = CONFIG_DIR / f"{contract_type}.json"
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def label_for(item: dict, language: str) -> str:
    labels = item.get("label") or {}
    return labels.get(language) or labels.get("en") or item["id"]