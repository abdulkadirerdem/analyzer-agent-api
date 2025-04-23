from fastapi import APIRouter, HTTPException, UploadFile, File
import os
import tempfile
import networkx as nx
from app.models.analyze_models import (
    AnalyzeFileRequest,
    AnalyzeDirectoryRequest,
    AnalysisResponse,
    AnalysisResult,
)
from app.modules.code_analyzer.scanner import find_python_files
from app.modules.code_analyzer.parser import parse_python_file
from app.modules.code_analyzer.graph_builder import build_dependency_graph
from app.modules.code_analyzer.analyzer import summarize_analysis

router = APIRouter(
    prefix="/codebase-analyzer",
    tags=["code-analyzer"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary="API status check",
    description="Verifies that the code analyzer API is running",
)
def analyze():
    return {"message": "Code Insight API is running 🚀"}


@router.post(
    "/file",
    response_model=AnalysisResponse,
    summary="Analyze a local file",
    description="Analyzes a Python file at the specified path and provides insights about functions, dependencies, and structure",
)
def analyze_file(request: AnalyzeFileRequest):
    """
    Analyze a single Python file and provide insights

    - **file_path**: Full path to the Python file to analyze
    """
    target_file = request.file_path

    # Check if file exists and has a .py extension
    if not os.path.exists(target_file):
        raise HTTPException(
            status_code=404, detail=f"File {target_file} does not exist"
        )

    if not target_file.endswith(".py"):
        raise HTTPException(
            status_code=400, detail=f"File {target_file} is not a Python file"
        )

    # Parse the file
    file_data = {target_file: parse_python_file(target_file)}

    # Create a minimal graph
    graph = nx.DiGraph()
    graph.add_node(target_file)

    # Run the analysis
    result = summarize_analysis(graph, file_data)

    # Filter for target file
    base_name = os.path.basename(target_file)
    if base_name in result:
        filtered_result = {base_name: result[base_name]}
    else:
        raise HTTPException(
            status_code=500, detail=f"No analysis available for {base_name}"
        )

    return {"results": filtered_result}


@router.post(
    "/directory",
    response_model=AnalysisResponse,
    summary="Analyze a directory",
    description="Analyzes all Python files in the specified directory and provides insights about functions, dependencies, and structure",
)
def analyze_directory(request: AnalyzeDirectoryRequest):
    """
    Analyze all Python files in a directory and provide insights

    - **directory_path**: Full path to the directory containing Python files to analyze
    """
    path = request.directory_path

    # Check if directory exists
    if not os.path.exists(path) or not os.path.isdir(path):
        raise HTTPException(status_code=404, detail=f"Directory {path} does not exist")

    # Find all Python files
    files = find_python_files(path)
    if not files:
        raise HTTPException(status_code=404, detail=f"No Python files found in {path}")

    # Parse all files
    file_data = {f: parse_python_file(f) for f in files}

    # Build dependency graph
    graph = build_dependency_graph(file_data)

    # Run the analysis
    result = summarize_analysis(graph, file_data)

    return {"results": result}


@router.post(
    "/upload",
    response_model=AnalysisResponse,
    summary="Analyze an uploaded file",
    description="Analyzes an uploaded Python file and provides insights about functions, dependencies, and structure",
)
async def analyze_uploaded_file(file: UploadFile = File(...)):
    """
    Analyze an uploaded Python file and provide insights

    - **file**: Python file to upload and analyze (.py extension required)
    """
    # Check if file has a .py extension
    if not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400, detail=f"File {file.filename} is not a Python file"
        )

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
        # Read the uploaded file and write to the temporary file
        content = await file.read()
        temp.write(content)
        temp_path = temp.name

    try:
        # Parse the file
        file_data = {temp_path: parse_python_file(temp_path)}

        # Create a minimal graph
        graph = nx.DiGraph()
        graph.add_node(temp_path)

        # Run the analysis
        result = summarize_analysis(graph, file_data)

        # Use the original filename for the result
        if os.path.basename(temp_path) in result:
            analysis_result = result[os.path.basename(temp_path)]
            # Replace the temporary filename with the original
            analysis_result["file"] = file.filename
            filtered_result = {file.filename: analysis_result}
        else:
            raise HTTPException(
                status_code=500, detail=f"No analysis available for {file.filename}"
            )

        return {"results": filtered_result}
    finally:
        # Clean up - remove the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
