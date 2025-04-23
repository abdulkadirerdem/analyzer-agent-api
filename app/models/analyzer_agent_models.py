from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnalyzerAgentRequest(BaseModel):
    """Request model for analyzer agent queries"""
    query: str = Field(..., description="Question about the code to analyze")
    file_path: Optional[str] = Field(None, description="Path to Python file to analyze")
    directory_path: Optional[str] = Field(None, description="Path to directory containing Python files")
    code_analysis: Optional[Dict[str, Any]] = Field(None, description="Pre-analyzed code data (if already analyzed)")
    

class FunctionSummary(BaseModel):
    """Summary of a function in analyzed code"""
    name: str
    explanation: str


class AnalyzerAgentResponse(BaseModel):
    """Response model for analyzer agent queries"""
    overall_analysis: Optional[str] = None
    important_functions: Optional[List[FunctionSummary]] = None
    summarized_functions: Optional[List[FunctionSummary]] = None
    function_summary: Optional[List[FunctionSummary]] = None
    markdown: Optional[str] = None
    error: Optional[str] = None


class AnalyzerAgentUploadRequest(BaseModel):
    """Request model for direct file upload and analyze"""
    query: str = Field(..., description="Question about the code to analyze")
