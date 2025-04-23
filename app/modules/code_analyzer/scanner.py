import os


def find_python_files(base_path: str) -> list[str]:
    py_files = []
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                py_files.append(os.path.abspath(full_path))
    return py_files
