from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
import os
import tempfile
import json
from typing import Dict, Any, Optional

from app.models.analyzer_agent_models import (
    AnalyzerAgentRequest,
    AnalyzerAgentResponse,
    AnalyzerAgentUploadRequest,
)
from app.modules.analyzer_agent.agents.chain import CodeExplainerAgent
from app.api.codebase_analyzer import analyze_file, analyze_directory
from app.models.analyze_models import AnalyzeFileRequest, AnalyzeDirectoryRequest

router = APIRouter(
    prefix="/code-explainer",
    tags=["code-explainer"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/explain",
    response_model=AnalyzerAgentResponse,
    summary="Explain code",
    description="Analyzes code and answers questions about it",
)
async def explain_code(request: AnalyzerAgentRequest):
    """
    Analyze code and answer questions about it

    - **query**: Question about the code
    - **file_path**: Path to Python file to analyze (optional)
    - **directory_path**: Path to directory containing Python files (optional)
    - **code_analysis**: Pre-analyzed code data (optional, if already analyzed)
    """
    try:
        # Initialize agent
        agent = CodeExplainerAgent()

        # If code analysis is already provided, use it
        if request.code_analysis:
            code_data = request.code_analysis
        else:
            # Otherwise, analyze the file or directory first
            if request.file_path:
                # Analyze single file
                analyze_request = AnalyzeFileRequest(file_path=request.file_path)
                analysis_response = analyze_file(analyze_request)
                code_data = analysis_response.get("results", {})
            elif request.directory_path:
                # Analyze directory
                analyze_request = AnalyzeDirectoryRequest(
                    directory_path=request.directory_path
                )
                analysis_response = analyze_directory(analyze_request)
                code_data = analysis_response.get("results", {})
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either file_path, directory_path, or code_analysis must be provided",
                )

        # Format and process the data
        if code_data and isinstance(code_data, dict):
            # Process the query with the agent
            # Save the code_data to a temporary file since the agent expects a file path
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".json", mode="w"
            ) as temp:
                json.dump(code_data, temp)
                temp.flush()
                temp_path = temp.name

            try:
                # Process the query
                result = agent.process_query(request.query, temp_path)
                return result
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        else:
            return {"error": "No valid code analysis data was provided."}

    except Exception as e:
        # Return any errors
        import traceback

        traceback_str = traceback.format_exc()
        print(f"Error in explain endpoint: {str(e)}\n{traceback_str}")
        return {"error": str(e)}


@router.post(
    "/upload",
    response_model=AnalyzerAgentResponse,
    summary="Upload and explain code",
    description="Upload a Python file, analyze it, and answer questions about it",
)
async def upload_and_explain(
    query: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a Python file, analyze it, and answer questions about it

    - **query**: Question about the code
    - **file**: Python file to analyze
    """
    # Check if file has a .py extension
    if not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400, detail=f"File {file.filename} is not a Python file"
        )

    # Create a temporary file for the uploaded code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
        content = await file.read()
        temp.write(content)
        temp_path = temp.name

    try:
        # Analyze the file
        analyze_request = AnalyzeFileRequest(file_path=temp_path)
        analysis_response = analyze_file(analyze_request)

        # Initialize agent
        agent = CodeExplainerAgent()

        # Format the analysis data correctly for the agent
        code_data = analysis_response.get("results", {})

        # Format properly for the agent
        if code_data and isinstance(code_data, dict) and len(code_data) > 0:
            # Save the analysis to a temporary file with proper formatting
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".json", mode="w"
            ) as analysis_temp:
                # Properly format the json with the original filename
                file_name = file.filename  # Use the original filename

                # Extract the first item's data if it's a dictionary with a single file
                if len(code_data) == 1:
                    first_key = next(iter(code_data))
                    file_data = code_data[first_key]

                    # Create a new dictionary with the original filename as key
                    formatted_data = {file_name: file_data}
                else:
                    # Multiple files or unexpected format, use as is
                    formatted_data = code_data

                # Write to the temp file
                json.dump(formatted_data, analysis_temp)
                analysis_temp.flush()
                analysis_path = analysis_temp.name

            try:
                # Process the query
                result = agent.process_query(query, analysis_path)
                return result
            finally:
                # Clean up the temporary analysis file
                if os.path.exists(analysis_path):
                    os.unlink(analysis_path)
        else:
            return {
                "error": "No code analysis data was generated. The file may be empty or invalid."
            }
    except Exception as e:
        import traceback

        traceback_str = traceback.format_exc()
        print(f"Error in upload endpoint: {str(e)}\n{traceback_str}")
        return {"error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post(
    "/all-in-one",
    response_model=Dict[str, Any],
    summary="Analyze and explain in one step",
    description="A combined endpoint that analyzes code and explains it with a single API call"
)
async def analyze_and_explain(
    query: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Analyze and explain code in a single API call
    
    - **query**: Question about the code
    - **file**: Python file to analyze
    """
    print(f"\n\n----- All-in-one endpoint called -----")
    print(f"Query: {query}")
    print(f"File: {file.filename}")
    
    # Check if file has a .py extension
    if not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400, 
            detail=f"File {file.filename} is not a Python file"
        )
    
    # Create a temporary file for the uploaded code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
        content = await file.read()
        temp.write(content)
        temp_path = temp.name
        print(f"Temporary file created at: {temp_path}")
    
    try:
        # Step 1: Analyze the file
        print("Step 1: Analyzing the file...")
        analyze_request = AnalyzeFileRequest(file_path=temp_path)
        analysis_response = analyze_file(analyze_request)
        print(f"Analysis response keys: {analysis_response.keys() if isinstance(analysis_response, dict) else 'Not a dictionary'}")
        
        # Step 2: Ask the code explainer agent
        print("Step 2: Preparing agent request...")
        agent = CodeExplainerAgent()
        
        # Format the analysis data correctly for the agent
        code_data = analysis_response.get("results", {})
        print(f"Code data keys: {code_data.keys() if isinstance(code_data, dict) else 'Not a dictionary'}")
        
        # The analysis_response.results has the filename as key
        # We need to make sure the file name is correctly passed to the agent
        if code_data and isinstance(code_data, dict) and len(code_data) > 0:
            # Debug - print what we received
            print(f"Code data contains {len(code_data)} file(s)")
            for key in code_data.keys():
                print(f"- File key: {key}")
                if isinstance(code_data[key], dict) and "functions" in code_data[key]:
                    print(f"  - Contains {len(code_data[key]['functions'])} functions")
            
            # Save the analysis to a temporary file with proper formatting
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as analysis_temp:
                # Properly format the json with the original filename
                file_name = file.filename  # Use the original filename
                print(f"Using filename for agent: {file_name}")
                
                # Extract the first item's data if it's a dictionary with a single file
                if len(code_data) == 1:
                    first_key = next(iter(code_data))
                    file_data = code_data[first_key]
                    
                    # Create a new dictionary with the original filename as key
                    formatted_data = {file_name: file_data}
                    print(f"Reformatted data with filename as key: {file_name}")
                else:
                    # Multiple files or unexpected format, use as is
                    formatted_data = code_data
                    print(f"Using original code data structure (multiple files)")
                
                # Write to the temp file
                json.dump(formatted_data, analysis_temp)
                analysis_temp.flush()  # Ensure all data is written
                analysis_path = analysis_temp.name
                print(f"Analysis data written to: {analysis_path}")
                
                # Let's verify the content of the temporary file
                try:
                    with open(analysis_path, 'r') as verify:
                        verify_data = json.load(verify)
                        print(f"Verification: Temp file contains {len(verify_data)} entries")
                        for key in verify_data.keys():
                            print(f"- Verify key: {key}")
                            if isinstance(verify_data[key], dict) and "functions" in verify_data[key]:
                                print(f"  - Contains {len(verify_data[key]['functions'])} functions")
                except Exception as e:
                    print(f"Error verifying temp file: {str(e)}")
            
            try:
                # Process the query
                print(f"Step 3: Calling agent.process_query with query: '{query}'")
                explanation_result = agent.process_query(query, analysis_path)
                print("Agent process_query completed")
                print(f"Explanation result keys: {explanation_result.keys() if isinstance(explanation_result, dict) else 'Not a dictionary'}")
                
                # Log the actual markdown content
                if "markdown" in explanation_result:
                    print(f"Markdown content (first 100 chars): {explanation_result['markdown'][:100]}")
                else:
                    print("No markdown content found in result")
                
                # Log the important functions
                if "important_functions" in explanation_result:
                    print(f"Important functions: {len(explanation_result['important_functions'])}")
                    for func in explanation_result.get("important_functions", []):
                        print(f"- Function: {func.get('name', 'unnamed')}")
                        explanation = func.get('explanation', '')
                        print(f"  Explanation: {explanation[:50]}..." if explanation else "  No explanation")
                
                # Combine results
                result = {
                    "analysis": analysis_response,
                    "explanation": explanation_result
                }
                
                print(f"Final response structure: {list(result.keys())}")
                print(f"Explanation structure: {list(result['explanation'].keys()) if isinstance(result['explanation'], dict) else 'Not a dictionary'}")
                print("----- All-in-one endpoint completed -----\n")
                
                return result
            finally:
                # Clean up the temporary analysis file
                if os.path.exists(analysis_path):
                    os.unlink(analysis_path)
                    print(f"Deleted temporary analysis file: {analysis_path}")
        else:
            print("ERROR: No valid code data found in analysis result")
            return {
                "error": "No code analysis data was generated. The file may be empty or invalid."
            }
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"ERROR in all-in-one endpoint: {str(e)}")
        print(traceback_str)
        return {"error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print(f"Deleted temporary code file: {temp_path}")


@router.post(
    "/debug-format",
    summary="Debug the data format",
    description="Endpoint for debugging the data format used in the API"
)
async def debug_format(
    file: UploadFile = File(...)
):
    """
    Debug the format of data being passed to the agent
    """
    # Check if file has a .py extension
    if not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400, 
            detail=f"File {file.filename} is not a Python file"
        )
    
    # Create a temporary file for the uploaded code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
        content = await file.read()
        temp.write(content)
        temp_path = temp.name
    
    try:
        # Analyze the file
        analyze_request = AnalyzeFileRequest(file_path=temp_path)
        analysis_response = analyze_file(analyze_request)
        
        # Get the raw data
        raw_data = analysis_response.get("results", {})
        
        # Format as we would for the agent
        formatted_data = {}
        
        if raw_data and isinstance(raw_data, dict) and len(raw_data) > 0:
            file_name = file.filename
            
            # Extract the first item's data if it's a dictionary with a single file
            if len(raw_data) == 1:
                first_key = next(iter(raw_data))
                file_data = raw_data[first_key]
                
                # Create a new dictionary with the original filename as key
                formatted_data = {file_name: file_data}
            else:
                # Multiple files or unexpected format, use as is
                formatted_data = raw_data
        
        # Return debug information
        return {
            "original_filename": file.filename,
            "raw_data_keys": list(raw_data.keys()) if isinstance(raw_data, dict) else "Not a dictionary",
            "raw_data": raw_data,
            "formatted_data": formatted_data,
            "formatted_data_keys": list(formatted_data.keys()) if isinstance(formatted_data, dict) else "Not a dictionary"
        }
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error in debug endpoint: {str(e)}\n{traceback_str}")
        return {"error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
