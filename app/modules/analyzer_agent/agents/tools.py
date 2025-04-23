from typing import List, Dict, Any

from core.function_selector import select_key_functions
from core.summarizer import summarize_function
from core.input_loader import load_dummy_input
from agents.types import FunctionInfo


def select_important_functions_tool(
    functions: List[FunctionInfo], top_n: int = 3
) -> List[FunctionInfo]:
    """Select the most important functions from a list.
    
    Args:
        functions: List of functions to analyze
        top_n: Number of functions to select
        
    Returns:
        List of selected important functions
    """
    return select_key_functions(functions, top_n=top_n)


def summarize_function_tool(function: FunctionInfo) -> str:
    """Generate a summary for the given function.
    
    Args:
        function: Function to summarize
        
    Returns:
        Summary of the function's purpose
    """
    return summarize_function(function)


def load_dummy_input_tool(file_path: str) -> Dict[str, Any]:
    """Load function data from a file.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        Dictionary with loaded function data
    """
    return load_dummy_input(file_path)

tools = [
    select_important_functions_tool,
    summarize_function_tool,
    load_dummy_input_tool
]