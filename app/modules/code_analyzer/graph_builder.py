import os
import networkx as nx


def build_dependency_graph(file_data: dict) -> nx.DiGraph:
    graph = nx.DiGraph()

    # 1. File -> module mapping (example: tests/mock_project/a.py → tests.mock_project.a)
    file_modules = {}
    for filepath in file_data:
        rel_path = os.path.relpath(filepath).replace(os.sep, ".")
        module_path = rel_path.replace(".py", "")
        file_modules[module_path] = filepath
        graph.add_node(filepath)
        
    # 2. Connect edges
    for file_path, data in file_data.items():
        for imp in data["imports"]:
            imp_base = imp.split(".")[0]

            # If exact match exists
            if imp in file_modules:
                graph.add_edge(file_path, file_modules[imp])

            # Or if the base module name matches
            elif imp_base in file_modules:
                graph.add_edge(file_path, file_modules[imp_base])

    return graph
