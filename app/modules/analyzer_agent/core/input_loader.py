import json
from typing import Dict, Any


def load_dummy_input(path: str = "examples/dummy_input.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
