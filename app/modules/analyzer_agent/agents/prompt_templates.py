from typing import List
from agents.types import FunctionInfo


def function_summary_prompt_template(fn: FunctionInfo) -> str:
    return f"""
You are an expert Python developer and technical writer.

Your task is to analyze the following function and explain its purpose in simple terms.
Only write the explanation. Do not repeat the code.

---

Function Name: {fn['name']}
Docstring: {fn.get('docstring', 'N/A')}
Fan-in: {fn.get('fan_in')}
Fan-out: {fn.get('fan_out')}
Entry Point: {fn.get('is_entry_point')}

Code:
{fn['code']}
"""


def generate_overall_analysis_prompt(function_summaries: List[dict]) -> str:
    """Generate a prompt to create an overall analysis of the code."""
    summaries = "\n\n".join(
        [
            f"Function: {summary['name']}\n"
            f"Purpose: {summary['purpose']}\n"
            f"Key Features: {', '.join(summary['key_features'])}"
            for summary in function_summaries
        ]
    )

    return f"""
You are an expert software architect and code reviewer.

Based on the summaries of key functions below, provide an overall analysis of this codebase.
Consider:
- The main purpose of the code
- Architecture patterns used
- Quality of the implementation
- Potential areas for improvement

Your analysis should be concise but insightful.

---

Function Summaries:
{summaries}
"""
