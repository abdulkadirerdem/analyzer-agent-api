from typing import List
import json
from agents.types import FunctionInfo


def format_as_json(file: str, summarized: List[FunctionInfo]) -> str:
    output = {"file": file, "summarized_functions": summarized}
    return json.dumps(output, indent=2)


def format_as_markdown(file: str, summarized: List[FunctionInfo]) -> str:
    md = f"# 📄 Documentation for `{file}`\n\n"

    for fn in summarized:
        md += f"## 🔹 Function: `{fn['name']}`\n\n"
        md += f"```python\n{fn['code']}\n```\n\n"
        md += f"**Explanation:**\n\n{fn['explanation']}\n\n"
        md += "---\n\n"

    return md
