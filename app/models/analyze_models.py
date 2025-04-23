from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AnalyzeFileRequest(BaseModel):
    """Request model for file path analysis"""
    file_path: str


class AnalyzeDirectoryRequest(BaseModel):
    """Request model for directory analysis"""
    directory_path: str


class FunctionInfo(BaseModel):
    """Information about a function in analyzed code"""
    name: str
    code: str
    docstring: str
    fan_in: int
    fan_out: int
    is_entry_point: bool


class FileAnalysisResult(BaseModel):
    """Result model for a single file analysis"""
    file: str
    functions: List[FunctionInfo]


class AnalysisResponse(BaseModel):
    """Response model for code analysis"""
    results: Dict[str, FileAnalysisResult]


class AnalysisResult(BaseModel):
    """Simple analysis result for storing file analysis"""
    file: str
    functions: List[Dict[str, Any]]
