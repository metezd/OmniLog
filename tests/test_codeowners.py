""".github/CODEOWNERS gives every member the area of their role in docs/CHARTER.md (#293).

GitHub ignores a line whose path matches no file, without an error, so a renamed folder would
silently stop the review request. These tests catch that, and check that each member owns
the area of their role.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"

MEMBERS = {"@metezd", "@KeremKenet", "@KaganKonuk", "@sidarurey", "@musabalperenbasol", "@Mhmd77Edrees"}


def rules():
    result = []
    for line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            path, *owners = line.split()
            result.append((path, owners))
    return result


def owners_of(file_path):
    """The owners of a file: the last matching line wins, as on GitHub."""
    found = []
    for path, owners in rules():
        if path == "*":
            found = owners
        elif path.endswith("/") and ("/" + file_path).startswith(path):
            found = owners
        elif "/" + file_path == path:
            found = owners
    return found


def test_there_is_a_fallback_owner():
    assert rules()[0] == ("*", ["@metezd"])


@pytest.mark.parametrize(("path", "owners"), [r for r in rules() if r[0] != "*"])
def test_every_path_exists(path, owners):
    pattern = path.rstrip("/").lstrip("/")
    assert list(ROOT.glob(pattern)), f"{path} matches no file, so GitHub ignores this line"


def test_only_team_members_are_owners():
    for _path, owners in rules():
        assert set(owners) <= MEMBERS


def test_every_member_owns_an_area():
    owners = {owner for _path, line_owners in rules() for owner in line_owners}
    assert owners == MEMBERS


@pytest.mark.parametrize(
    ("file_path", "owner"),
    [
        ("backend/app/api/library.py", "@KaganKonuk"),
        ("backend/app/integrations/igdb.py", "@musabalperenbasol"),
        ("backend/app/integrations/tmdb.py", "@musabalperenbasol"),
        ("backend/app/services/embedding_service.py", "@sidarurey"),
        ("backend/app/services/recommendations_service.py", "@sidarurey"),
        ("tests/test_health.py", "@Mhmd77Edrees"),
        ("tests/pentest/run_pentest.py", "@Mhmd77Edrees"),
        ("frontend/src/proxy.ts", "@KeremKenet"),
        (".github/workflows/ci.yml", "@metezd"),
    ],
)
def test_each_area_has_the_owner_of_its_role(file_path, owner):
    assert owner in owners_of(file_path)
