import networkx as nx
import ast
import os


def detect_circular_imports(graph: nx.DiGraph) -> list[list[str]]:
    try:
        return list(nx.simple_cycles(graph))
    except Exception:
        return []


def calculate_fan_in_out(graph: nx.DiGraph) -> dict:
    return {
        node: {"fan_in": graph.in_degree(node), "fan_out": graph.out_degree(node)}
        for node in graph.nodes
    }


def find_dead_exports(file_data: dict) -> dict:
    all_code = ""
    for fpath in file_data:
        with open(fpath, "r", encoding="utf-8") as f:
            all_code += f.read()

    dead = {}
    for fpath, data in file_data.items():
        dead_symbols = []
        for symbol in data["exports"]:
            if all_code.count(symbol) <= 1:
                dead_symbols.append(symbol)
        if dead_symbols:
            dead[fpath] = dead_symbols

    return dead


def analyze_functions(file_data: dict) -> dict:
    """
    Analyze functions to determine fan-in, fan-out, and if they are entry points
    """
    # Build a dict mapping function names to their files
    function_map = {}
    for filepath, data in file_data.items():
        for func in data.get("functions", []):
            # Use fully qualified name to avoid name clashes
            func_name = f"{os.path.basename(filepath)}:{func['name']}"
            function_map[func_name] = {
                "file": filepath,
                "name": func["name"],
                "code": func["code"],
                "docstring": func["docstring"],
                "fan_in": 0,
                "fan_out": 0,
                "is_entry_point": True  # Default to True, we'll set to False if called
            }
    
    # Count fan_in, fan_out
    for filepath, data in file_data.items():
        for func in data.get("functions", []):
            # Parse the function body to find calls to other functions
            tree = ast.parse(func["code"])
            
            # Find all function calls in this function body
            calls = []
            for call_node in ast.walk(tree):
                if isinstance(call_node, ast.Call) and isinstance(call_node.func, ast.Name):
                    calls.append(call_node.func.id)
            
            # Update fan_out for this function
            func_key = f"{os.path.basename(filepath)}:{func['name']}"
            if func_key in function_map:
                function_map[func_key]["fan_out"] = len(set(calls))
            
            # Update fan_in for called functions
            for called_func_name in calls:
                for other_file in file_data.keys():
                    other_key = f"{os.path.basename(other_file)}:{called_func_name}"
                    if other_key in function_map:
                        function_map[other_key]["fan_in"] += 1
                        function_map[other_key]["is_entry_point"] = False
    
    # Group results by file
    result = {}
    for func_key, func_data in function_map.items():
        file_path = func_data["file"]
        file_basename = os.path.basename(file_path)
        
        if file_basename not in result:
            result[file_basename] = {
                "file": file_basename,
                "functions": []
            }
        
        # Format code properly
        code = func_data["code"]
        
        result[file_basename]["functions"].append({
            "name": func_data["name"],
            "code": code,
            "docstring": func_data["docstring"],
            "fan_in": func_data["fan_in"],
            "fan_out": func_data["fan_out"],
            "is_entry_point": func_data["is_entry_point"]
        })
    
    return result


def summarize_analysis(graph: nx.DiGraph, file_data: dict) -> dict:
    function_analysis = analyze_functions(file_data)
    
    # Result is already in the desired format
    return function_analysis
