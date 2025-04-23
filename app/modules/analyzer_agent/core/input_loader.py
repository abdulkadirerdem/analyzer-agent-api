import json
from typing import Dict, Any
import os


def load_dummy_input(path: str = "examples/dummy_input.json") -> Dict[str, Any]:
    """
    Load JSON data from the given path
    Returns the parsed JSON data or an empty dict if an error occurs
    """
    print(f"DEBUG load_dummy_input: Loading data from: {path}")
    
    try:
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            return {}
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Analyze the data structure for debugging
            if isinstance(data, dict):
                print(f"DEBUG: JSON loaded successfully with {len(data)} top-level keys")
                for key in data.keys():
                    print(f"DEBUG: Found key: {key}")
            else:
                print(f"DEBUG: JSON loaded but is not a dictionary: {type(data)}")
                
            return data
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode error in {path}: {str(e)}")
        return {}
    except Exception as e:
        print(f"ERROR: Failed to load {path}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {}
