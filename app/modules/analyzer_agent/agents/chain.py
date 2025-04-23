import json
import logging
from typing import List, Dict, Any, Optional
import os

from openai import OpenAI
from agents.types import FunctionInfo, ActionType
from agents.prompt_templates import generate_overall_analysis_prompt

# Import core functions that already exist
from core.input_loader import load_dummy_input
from core.function_selector import select_key_functions
from core.summarizer import summarize_function
from core.formatter import format_as_markdown

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEFAULT_MODEL = "gpt-4o-mini"  # Default model


# Define possible actions for the agent


class CodeExplainerAgent:
    """An agent that analyzes code and explains what it does"""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.client = client
        logger.info(f"Initialized CodeExplainerAgent with model: {model}")

    def triage_query(self, query: str, file_path: str) -> ActionType:
        """Determine what action to take based on the user query"""
        logger.info(f"Triaging query: {query}")

        # Define the function calling for action determination
        triage_tool = {
            "type": "function",
            "function": {
                "name": "determine_action",
                "description": "Determine what action to take based on the user query",
                "parameters": ActionType.model_json_schema(),
            },
        }

        # Create triage prompt
        triage_prompt = f"""
You are a code analysis assistant that helps users understand code.
Based on the user query, determine what action I should take.

Available actions:
1. Explain what the code does in natural language
2. Find the most important functions in the code
3. Summarize a specific function (if user mentions a function name)
4. Provide an overall analysis of the codebase

USER QUERY: {query}
CODE FILE: {file_path}

Determine the action that best matches the user's intention.
"""

        # Call LLM for triage
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": triage_prompt}],
            tools=[triage_tool],
            tool_choice={"type": "function", "function": {"name": "determine_action"}},
        )

        # Parse response
        tool_call = response.choices[0].message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)

        return ActionType(**result)

    def load_code_data(self, file_path: str) -> Dict[str, Any]:
        """Load code data from a file"""
        logger.info(f"Loading code data from: {file_path}")
        return load_dummy_input(file_path)

    def find_important_functions(
        self, functions: List[FunctionInfo], top_n: int = 3
    ) -> List[FunctionInfo]:
        """Find the most important functions using existing selector"""
        logger.info(f"Finding {top_n} important functions from {len(functions)} total")
        return select_key_functions(functions, top_n=top_n)

    def summarize_specific_function(
        self, functions: List[FunctionInfo], function_name: str
    ) -> Optional[str]:
        """Summarize a specific function by name"""
        logger.info(f"Summarizing specific function: {function_name}")

        # Find the function by name
        function = next((fn for fn in functions if fn["name"] == function_name), None)

        if not function:
            logger.warning(f"Function not found: {function_name}")
            return None

        # Use existing summarizer
        return summarize_function(function)

    def explain_all_functions(
        self, functions: List[FunctionInfo]
    ) -> List[Dict[str, str]]:
        """Generate summaries for all functions"""
        logger.info(f"Generating summaries for all {len(functions)} functions")

        results = []
        for function in functions:
            explanation = summarize_function(function)
            results.append(
                {
                    "name": function["name"],
                    "code": function["code"],
                    "explanation": explanation,
                }
            )

        return results

    def generate_overall_analysis(
        self, functions: List[FunctionInfo], summarized_functions: List[Dict]
    ) -> str:
        """Generate an overall analysis of the code"""
        logger.info("Generating overall code analysis")

        # Create a function summary objects for the template
        function_summaries = []
        for func in summarized_functions:
            function_summaries.append(
                {
                    "name": func["name"],
                    "purpose": func["explanation"],
                    "key_features": [],  # We don't have this from the existing summarizer
                }
            )

        # Generate the analysis
        prompt = generate_overall_analysis_prompt(function_summaries)

        response = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "system", "content": prompt}]
        )

        return response.choices[0].message.content

    def process_query(self, query: str, file_path: str) -> Dict[str, Any]:
        """Process a user query and return appropriate results"""
        logger.info(f"Processing query: {query} for file: {file_path}")

        # Step 1: Triage the query to determine action
        action = self.triage_query(query, file_path)

        # Step 2: Load code data
        data = self.load_code_data(file_path)
        file_name = data.get("file", "")
        functions = data.get("functions", [])

        # Step 3: Perform the appropriate action
        result = {"file": file_name}

        if action.explain_code:
            # Explain all functions
            summarized = self.explain_all_functions(functions)
            result["summarized_functions"] = summarized
            result["markdown"] = format_as_markdown(file_name, summarized)

        elif action.find_important_functions:
            # Find and explain important functions
            important_functions = self.find_important_functions(functions, action.top_n)
            summarized = self.explain_all_functions(important_functions)
            result["important_functions"] = summarized
            result["markdown"] = format_as_markdown(file_name, summarized)

        elif action.summarize_specific_function and action.function_name:
            # Summarize a specific function
            explanation = self.summarize_specific_function(
                functions, action.function_name
            )
            function = next(
                (fn for fn in functions if fn["name"] == action.function_name), None
            )

            if function and explanation:
                summarized = [
                    {
                        "name": function["name"],
                        "code": function["code"],
                        "explanation": explanation,
                    }
                ]
                result["function_summary"] = summarized
                result["markdown"] = format_as_markdown(file_name, summarized)
            else:
                result["error"] = f"Function '{action.function_name}' not found"

        if action.overall_analysis:
            # If we have summarized functions, generate an overall analysis
            if "summarized_functions" in result:
                analysis = self.generate_overall_analysis(
                    functions, result["summarized_functions"]
                )
            elif "important_functions" in result:
                analysis = self.generate_overall_analysis(
                    functions, result["important_functions"]
                )
            elif "function_summary" in result:
                analysis = self.generate_overall_analysis(
                    functions, result["function_summary"]
                )
            else:
                # If no functions were summarized yet, summarize important ones first
                important_functions = self.find_important_functions(
                    functions, action.top_n
                )
                summarized = self.explain_all_functions(important_functions)
                analysis = self.generate_overall_analysis(functions, summarized)
                result["important_functions"] = summarized

            result["overall_analysis"] = analysis

        return result
