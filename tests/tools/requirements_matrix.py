"""Requirement to test matrix (#300).

Reads the user story IDs (US-01 to US-15) from docs/requirements/user-stories.md and the NFR IDs
from docs/requirements/requirements-specification.md, then finds the tests that name each ID in
their name or docstring. tests/test_requirements_traceability.py uses the same functions.

    python tests/tools/requirements_matrix.py            # prints a Markdown table
"""
from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORIES_DOC = ROOT / "docs/requirements/user-stories.md"
NFR_DOC = ROOT / "docs/requirements/requirements-specification.md"
THIS_TEST = "test_requirements_traceability.py"


def _table_ids(path: Path, prefix: str) -> dict[str, str]:
    """IDs from the first column of the Markdown table rows that start with `| <prefix>-NN |`."""
    found: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(rf"^\|\s*({prefix}-\d{{2}})\s*\|(.*)$", line)
        if match and match.group(1) not in found:
            cells = [cell.strip() for cell in match.group(2).split("|")]
            found[match.group(1)] = next((c for c in cells if c and not c.isdigit()), "")
    return found


def story_ids() -> dict[str, str]:
    """US-xx from the story table of user-stories.md, with the heading text as the subject."""
    ids = _table_ids(STORIES_DOC, "US")
    headings = dict(re.findall(r"^### (US-\d{2}) (.+)$", STORIES_DOC.read_text(encoding="utf-8"), re.MULTILINE))
    return {key: headings.get(key, "") for key in ids}


def nfr_ids() -> dict[str, str]:
    """NFR-xx from the NFR table of the requirements specification, with the requirement text."""
    found: dict[str, str] = {}
    for line in NFR_DOC.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"NFR-\d{2}", cells[0]) and cells[0] not in found:
            found[cells[0]] = cells[2]
    return found


def _pattern(requirement_id: str) -> re.Pattern[str]:
    """US-01 matches "US-01" in a docstring and "us01" or "us_01" in a test name, but not US-010."""
    prefix, number = requirement_id.lower().split("-")
    return re.compile(rf"(?<![a-z0-9]){prefix}[-_]?{number}(?!\d)", re.IGNORECASE)


def test_texts() -> dict[str, list[tuple[str, str]]]:
    """For each test file: (test name, name plus docstrings) of every test function.

    The docstring of the module and of the class count for each test in them, because a file
    such as test_epic2_journal_edge_cases.py names its stories once at the top.
    """
    result: dict[str, list[tuple[str, str]]] = {}
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        if path.name == THIS_TEST:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module_doc = ast.get_docstring(tree) or ""
        tests: list[tuple[str, str]] = []

        def visit(node, outer_doc):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    visit(child, outer_doc + "\n" + (ast.get_docstring(child) or "") + "\n" + child.name)
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test"):
                    tests.append((child.name, f"{child.name}\n{ast.get_docstring(child) or ''}\n{outer_doc}"))

        visit(tree, module_doc)
        result[str(path.relative_to(ROOT))] = tests
    return result


def matrix() -> dict[str, dict]:
    texts = test_texts()
    requirements = {**story_ids(), **nfr_ids()}
    rows: dict[str, dict] = {}
    for requirement_id, subject in requirements.items():
        pattern = _pattern(requirement_id)
        files: dict[str, int] = defaultdict(int)
        for path, tests in texts.items():
            for _name, text in tests:
                if pattern.search(text):
                    files[path] += 1
        rows[requirement_id] = {"subject": subject, "files": dict(files), "tests": sum(files.values())}
    return rows


def markdown() -> str:
    lines = ["| Requirement | Subject | Test files | Tests |", "|---|---|---|---|"]
    for requirement_id, row in matrix().items():
        files = ", ".join(f"`{Path(p).name}` ({n})" for p, n in sorted(row["files"].items()))
        lines.append(f"| {requirement_id} | {row['subject']} | {files or 'none'} | {row['tests']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(markdown())
