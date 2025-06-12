"""Fetch diffs for pull requests.

In local mock mode, reads from a sample repository on disk.  In production, would call GitHub’s API using installation tokens.
"""

import os
from typing import List, Tuple


def fetch_changed_files(repo_name: str, pr_number: str) -> List[Tuple[str, List[str]]]:
    """Return a list of tuples (file_path, lines) representing changed files.

    In mock mode we just read all files under app/demo/sample_repos/python_small.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "..", "demo", "sample_repos", "python_small")
    changed_files: List[Tuple[str, List[str]]] = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    lines = f.readlines()
                rel_path = os.path.relpath(path, base_dir)
                changed_files.append((rel_path, lines))
    return changed_files