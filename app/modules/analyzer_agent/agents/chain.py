import json
import logging
from typing import List, Dict, Any, Optional
import os

from openai import OpenAI
from app.modules.analyzer_agent.agents.types import FunctionInfo, ActionType
from app.modules.analyzer_agent.agents.prompt_templates import generate_overall_analysis_prompt

# Import core functions that already exist
from app.modules.analyzer_agent.core.input_loader import load_dummy_input
from app.modules.analyzer_agent.core.function_selector import select_key_functions
from app.modules.analyzer_agent.core.summarizer import summarize_function
from app.modules.analyzer_agent.core.formatter import format_as_markdown

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
        print(f"DEBUG: Loading code data from file: {file_path}")
        
        try:
            data = load_dummy_input(file_path)
            
            # Print debug info about loaded data
            if isinstance(data, dict):
                print(f"DEBUG: Loaded data keys: {list(data.keys())}")
                for key in data.keys():
                    if isinstance(data[key], dict):
                        file_data = data[key]
                        print(f"DEBUG: File '{key}' has keys: {list(file_data.keys())}")
                        if "functions" in file_data and isinstance(file_data["functions"], list):
                            print(f"DEBUG: File has {len(file_data['functions'])} functions")
                            for func in file_data["functions"][:2]:  # Show first 2 only
                                print(f"DEBUG: Function '{func.get('name', 'unnamed')}' with code length: {len(func.get('code', ''))}")
            else:
                print(f"DEBUG: Loaded data is not a dictionary: {type(data)}")
            
            return data
        except Exception as e:
            print(f"ERROR in load_code_data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {}

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
        print(f"DEBUG: Processing query: '{query}' for file: {file_path}")
        
        try:
            # Step 1: Triage the query to determine action
            action = self.triage_query(query, file_path)
            print(f"DEBUG: Triage result - action type: {action}")
            
            # Step 2: Load code data
            data = self.load_code_data(file_path)
            file_name = data.get("file", "")
            
            # If file_name is empty, try to find it in the data structure
            if not file_name and isinstance(data, dict) and len(data) > 0:
                # If data has a structure like {"file.py": {"file": "file.py", "functions": [...]}}
                first_key = next(iter(data))
                if isinstance(data[first_key], dict) and "file" in data[first_key]:
                    file_name = data[first_key]["file"]
                    print(f"DEBUG: Found filename in data structure: {file_name}")
                else:
                    # Use the key itself as filename
                    file_name = first_key
                    print(f"DEBUG: Using key as filename: {file_name}")
            
            print(f"DEBUG: File name: '{file_name}'")
            
            # Get functions list - handle both formats
            if isinstance(data, dict):
                if "functions" in data:
                    # Format: {"functions": [...]}
                    functions = data.get("functions", [])
                    print(f"DEBUG: Got {len(functions)} functions directly from data")
                elif file_name in data and isinstance(data[file_name], dict):
                    # Format: {"file.py": {"functions": [...]}}
                    functions = data[file_name].get("functions", [])
                    print(f"DEBUG: Got {len(functions)} functions from '{file_name}' key")
                elif len(data) > 0:
                    # Try the first key
                    first_key = next(iter(data))
                    if isinstance(data[first_key], dict) and "functions" in data[first_key]:
                        functions = data[first_key].get("functions", [])
                        file_name = first_key if not file_name else file_name
                        print(f"DEBUG: Got {len(functions)} functions from first key '{first_key}'")
                    else:
                        functions = []
                        print(f"DEBUG: No functions found in data")
                else:
                    functions = []
                    print(f"DEBUG: Empty data dictionary")
            else:
                functions = []
                print(f"DEBUG: Data is not a dictionary - can't extract functions")
            
            # Step 3: Perform the appropriate action
            result = {"file": file_name}
            print(f"DEBUG: Starting action with {len(functions)} functions")

            if action.explain_code:
                # Explain all functions
                print(f"DEBUG: Explaining all functions")
                summarized = self.explain_all_functions(functions)
                result["summarized_functions"] = summarized
                result["markdown"] = format_as_markdown(file_name, summarized)
                print(f"DEBUG: Generated markdown with {len(summarized)} functions")

            elif action.find_important_functions:
                # Find and explain important functions
                print(f"DEBUG: Finding important functions, top_n={action.top_n}")
                important_functions = self.find_important_functions(functions, action.top_n)
                print(f"DEBUG: Found {len(important_functions)} important functions")
                summarized = self.explain_all_functions(important_functions)
                result["important_functions"] = summarized
                result["markdown"] = format_as_markdown(file_name, summarized)
                print(f"DEBUG: Generated markdown for important functions")

            elif action.summarize_specific_function and action.function_name:
                # Summarize a specific function
                print(f"DEBUG: Summarizing specific function: {action.function_name}")
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
                    print(f"DEBUG: Generated markdown for specific function")
                else:
                    result["error"] = f"Function '{action.function_name}' not found"
                    print(f"DEBUG: Function '{action.function_name}' not found")

            if action.overall_analysis:
                # If we have summarized functions, generate an overall analysis
                print(f"DEBUG: Generating overall analysis")
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
                    
                    # Make sure we also have markdown
                    if "markdown" not in result:
                        result["markdown"] = format_as_markdown(file_name, summarized)
                        print(f"DEBUG: Generated markdown for important functions")

                result["overall_analysis"] = analysis
                print(f"DEBUG: Added overall analysis")
            
            # Final result check
            print(f"DEBUG: Final result keys: {list(result.keys())}")
            if "markdown" in result:
                markdown_lines = result["markdown"].split('\n')
                print(f"DEBUG: Markdown first line: {markdown_lines[0] if markdown_lines else 'empty'}")
                print(f"DEBUG: Markdown has {len(markdown_lines)} lines")
            
            return result
            
        except Exception as e:
            print(f"ERROR in process_query: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"error": str(e), "file": "", "markdown": "Error processing query"}
