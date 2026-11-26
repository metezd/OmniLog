"""NFR-05: the backend code is covered by automated tests (#300).

NFR-05 asks for at least 70% line coverage with pytest-cov. The number itself is measured in CI
(docs/tests/coverage.md). These tests check the settings that keep it true: the CI gate is not
under the requirement, the documented command uses the same gate, no file is hidden from the
measurement, and the frontend has thresholds too.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# The autouse fixture in tests/conftest.py imports the app, so the backend must be importable
# when this file runs alone
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
NFR_05_MINIMUM = 70


def gates(path: Path) -> list[int]:
    return [int(value) for value in re.findall(r"--cov-fail-under=(\d+)", path.read_text(encoding="utf-8"))]


def test_nfr05_ci_gate_is_at_least_the_requirement():
    ci_gates = gates(ROOT / ".github/workflows/ci.yml")

    assert ci_gates, "ci.yml runs the backend tests without --cov-fail-under"
    assert min(ci_gates) >= NFR_05_MINIMUM


def test_nfr05_contributing_uses_the_same_gate_as_ci():
    """A contributor who runs the documented command sees the same result as CI."""
    assert gates(ROOT / "CONTRIBUTING.md") == gates(ROOT / ".github/workflows/ci.yml")


@pytest.mark.parametrize("name", [".coveragerc", "setup.cfg", "pyproject.toml", "tox.ini", "pytest.ini"])
def test_nfr05_no_backend_file_is_left_out_of_the_measurement(name):
    """Hiding files with `omit` or an exclusion would raise the number without a test."""
    path = ROOT / name
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")

    assert not re.search(r"^\s*omit\s*=", text, re.MULTILINE), f"{name} leaves files out of the coverage"
    assert "exclude_lines" not in text and "exclude_also" not in text, f"{name} leaves lines out of the coverage"


def test_nfr05_the_frontend_has_coverage_thresholds():
    config = (ROOT / "frontend/vitest.config.mts").read_text(encoding="utf-8")
    thresholds = dict(re.findall(r"(lines|statements|functions|branches):\s*(\d+)", config))

    assert set(thresholds) == {"lines", "statements", "functions", "branches"}
    assert all(int(value) > 0 for value in thresholds.values())
