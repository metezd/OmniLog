"""One version number for the whole repository (see CONTRIBUTING.md, Versioning and releases).

The backend version, the frontend package version and the lock file must be the same
semantic version. The release workflow checks the same files against the Git tag.
The files are read as text, so the test needs no database and does not import the app.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def backend_version() -> str:
    text = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    match = re.search(r'^\s+version="([^"]+)",$', text, re.MULTILINE)
    assert match, "No version=... line found in backend/app/main.py"
    return match.group(1)


def frontend_version() -> str:
    data = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    return data["version"]


def lock_versions() -> list[str]:
    data = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    return [data["version"], data["packages"][""]["version"]]


def test_versions_are_semantic():
    assert SEMVER.match(backend_version())


def test_backend_and_frontend_use_the_same_version():
    assert backend_version() == frontend_version()


def test_lock_file_uses_the_frontend_version():
    assert lock_versions() == [frontend_version()] * 2


def test_changelog_has_an_unreleased_section():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" in text
