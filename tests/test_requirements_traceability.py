"""Every requirement has tests (#300).

Reads the user stories (US-01 to US-15) from docs/requirements/user-stories.md and the
non-functional requirements from docs/requirements/requirements-specification.md, and checks that
the names or docstrings of the tests name each ID. The matrix itself is printed by
`python tests/tools/requirements_matrix.py` and kept in docs/tests/traceability.md.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The autouse fixture in tests/conftest.py imports the app, so the backend must be importable
# when this file runs alone. tests/tools holds the matrix code.
for folder in (ROOT / "backend", ROOT / "tests" / "tools"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import requirements_matrix as rm  # noqa: E402

# A requirement named by fewer test files needs a written reason here
SINGLE_FILE_REASONS: dict[str, str] = {
    "NFR-05": "coverage is a property of the whole suite. CI measures it with --cov-fail-under, and "
    "tests/test_coverage_gate.py checks the gate settings. A second file would repeat those checks.",
}


def test_the_requirement_tables_are_read():
    """A changed table format must not make the check below empty and pass by accident."""
    stories, nfrs = rm.story_ids(), rm.nfr_ids()

    assert len(stories) >= 15, f"only {sorted(stories)} found in {rm.STORIES_DOC.name}"
    assert len(nfrs) >= 5, f"only {sorted(nfrs)} found in {rm.NFR_DOC.name}"
    assert [f"US-{n:02d}" for n in range(1, 16)] == sorted(stories)[:15]


def test_every_requirement_is_named_by_a_test():
    missing = [rid for rid, row in rm.matrix().items() if row["tests"] == 0]

    assert not missing, f"no test names these requirements in its name or docstring: {missing}"


def test_every_requirement_is_named_by_two_test_files():
    """At least two files, so that one renamed file cannot remove the only proof."""
    thin = {
        rid: sorted(row["files"])
        for rid, row in rm.matrix().items()
        if len(row["files"]) < 2 and rid not in SINGLE_FILE_REASONS
    }

    assert not thin, f"named by only one test file, add a test or a reason: {thin}"


def test_no_test_is_marked_as_an_expected_failure():
    """The `not_built` helper of the requirements phase was removed. No feature may hide behind xfail."""
    marked = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").rglob("*.py")
        if path.name != Path(__file__).name
        and ("xfail" in (text := path.read_text(encoding="utf-8")) or "not_built" in text)
    ]

    assert not marked, f"expected failures in {marked}"


def test_the_check_finds_an_unnamed_id():
    """The pattern must not match a longer number or a similar word, or the check proves nothing."""
    pattern = rm._pattern("US-01")

    assert pattern.search("def test_us01_health") and pattern.search("US-01: GET /health")
    assert not pattern.search("US-010") and not pattern.search("bus01") and not pattern.search("US-11")
