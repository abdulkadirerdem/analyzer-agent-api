import ast


def parse_python_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    imports = []
    imported_symbols = []
    exports = []
    dynamic_imports = []
    aliases = {}
    functions = []

    for node in ast.walk(tree):
        # Static imports: import x or from x import y
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                aliases[alias.asname or alias.name] = alias.name

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
            for alias in node.names:
                imported_symbols.append(alias.name)
                aliases[alias.asname or alias.name] = alias.name

        # Exports: functions, classes, constants
        elif isinstance(node, ast.FunctionDef):
            exports.append(node.name)

            # Extract function code and docstring
            function_code = ast.get_source_segment(source, node)
            docstring = ast.get_docstring(node) or ""

            # Make sure code is properly formatted
            function_code = function_code.rstrip()

            functions.append(
                {
                    "name": node.name,
                    "code": function_code,
                    "docstring": docstring,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno,
                }
            )

        elif isinstance(node, ast.ClassDef):
            exports.append(node.name)

            # Also extract methods from classes
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_code = ast.get_source_segment(source, item)
                    method_docstring = ast.get_docstring(item) or ""

                    # Make sure code is properly formatted
                    method_code = method_code.rstrip()

                    functions.append(
                        {
                            "name": item.name,
                            "code": method_code,
                            "docstring": method_docstring,
                            "lineno": item.lineno,
                            "end_lineno": item.end_lineno,
                        }
                    )

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.append(target.id)

        # Dynamic imports
        elif isinstance(node, ast.Call):
            func_name = getattr(node.func, "id", "")
            if func_name in ("__import__", "import_module"):
                dynamic_imports.append(ast.unparse(node))

    return {
        "file": filepath,
        "imports": list(set(imports)),
        "imported_symbols": list(set(imported_symbols)),
        "exports": list(set(exports)),
        "dynamic_imports": dynamic_imports,
        "aliases": aliases,
        "functions": functions,
    }
