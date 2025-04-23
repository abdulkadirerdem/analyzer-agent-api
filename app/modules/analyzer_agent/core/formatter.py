from typing import List
import json
from app.modules.analyzer_agent.agents.types import FunctionInfo


def format_as_json(file: str, summarized: List[FunctionInfo]) -> str:
    output = {"file": file, "summarized_functions": summarized}
    return json.dumps(output, indent=2)


def format_as_markdown(file: str, summarized: List[FunctionInfo]) -> str:
    """Format the function summaries as markdown"""
    print(f"DEBUG: Formatting markdown for file: '{file}' with {len(summarized)} functions")
    
    # Make sure we have a valid file name
    if not file or not isinstance(file, str):
        file = "unnamed_file"
        print(f"DEBUG: Setting default file name: {file}")
    
    md = f"# 📄 Documentation for `{file}`\n\n"
    
    # Check if we have functions to document
    if not summarized or len(summarized) == 0:
        print("DEBUG: No functions to format in markdown")
        md += "*No functions to document*\n"
        return md
    
    for i, fn in enumerate(summarized):
        try:
            name = fn.get('name', f"unnamed_function_{i}")
            code = fn.get('code', 'No code available')
            explanation = fn.get('explanation', 'No explanation available')
            
            print(f"DEBUG: Formatting function: {name}")
            
            md += f"## 🔹 Function: `{name}`\n\n"
            md += f"```python\n{code}\n```\n\n"
            md += f"**Explanation:**\n\n{explanation}\n\n"
            md += "---\n\n"
        except Exception as e:
            print(f"ERROR formatting function {i}: {str(e)}")
            md += f"## 🔹 Error formatting function\n\n"
            md += "---\n\n"
    
    print(f"DEBUG: Markdown generation complete. Length: {len(md)} chars")
    return md
