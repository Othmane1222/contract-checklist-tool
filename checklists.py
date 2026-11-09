import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"


def load_checklist(contract_type: str) -> dict:
    path = CONFIG_DIR / f"{contract_type}.json"
    with path.open(encoding="utf-8") as file:
        return json.load(file)