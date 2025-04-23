from typing_extensions import TypedDict
from typing import List, Optional
from pydantic import BaseModel, Field


class FunctionInfo(TypedDict):
    name: str
    code: str
    docstring: str
    fan_in: int
    fan_out: int
    is_entry_point: bool


class FunctionSummary(BaseModel):
    """Summary information for a single function"""

    name: str = Field(description="Function name")
    purpose: str = Field(description="Function purpose summary")
    key_features: List[str] = Field(description="Key aspects of the function")


class FinalResponse(BaseModel):
    """Final output of the code explainer chain"""

    summaries: List[FunctionSummary] = Field(
        description="Summaries of analyzed functions"
    )
    overall_analysis: str = Field(description="Overall analysis of the code")


class ActionType(BaseModel):
    """Possible actions for the code explainer agent"""

    explain_code: bool = Field(
        default=False, description="Explain what the code does in natural language"
    )
    find_important_functions: bool = Field(
        default=False, description="Find the most important functions"
    )
    summarize_specific_function: bool = Field(
        default=False, description="Summarize a specific function"
    )
    overall_analysis: bool = Field(
        default=False, description="Provide an overall analysis of the codebase"
    )
    function_name: Optional[str] = Field(
        default=None,
        description="Name of the function to summarize if summarize_specific_function is True",
    )
    top_n: int = Field(default=3, description="Number of important functions to find")
