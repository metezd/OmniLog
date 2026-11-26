""".github/rulesets/ matches the workflows and CONTRIBUTING.md (#369).

The live rulesets on GitHub are applied from these files by an admin. When a file names a check
that no workflow runs, every pull request waits for it forever, and when the merge method of the
file is not the one of the Dependabot workflow, Dependabot pull requests are never merged. These
tests catch both before the file is applied.
"""
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RULESETS = ROOT / ".github" / "rulesets"
WORKFLOWS = ROOT / ".github" / "workflows"
CONTRIBUTING = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

MAIN = json.loads((RULESETS / "main.json").read_text(encoding="utf-8"))


def rule(ruleset, kind):
    found = [item for item in ruleset["rules"] if item["type"] == kind]
    assert found, f"no rule {kind}"
    return found[0].get("parameters", {})


def job_names():
    """The names of all jobs of the workflows that run on every pull request (no path filter)."""
    names = set()
    for path in WORKFLOWS.glob("*.yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        # PyYAML reads the key "on" as True
        triggers = data.get("on", data.get(True)) or {}
        pull_request = triggers.get("pull_request") if isinstance(triggers, dict) else None
        if not isinstance(triggers, dict) or "pull_request" not in triggers:
            continue
        if isinstance(pull_request, dict) and ("paths" in pull_request or "paths-ignore" in pull_request):
            continue
        for job_id, job in data["jobs"].items():
            names.add(job.get("name", job_id))
    return names


REQUIRED = [item["context"] for item in rule(MAIN, "required_status_checks")["required_status_checks"]]


@pytest.mark.parametrize("check", REQUIRED)
def test_every_required_check_runs_on_every_pull_request(check):
    assert check in job_names(), f"no workflow without a path filter has a job named {check!r}"


@pytest.mark.parametrize("check", ["PR title", "Branch name", "AI disclosure"])
def test_the_naming_and_ai_checks_are_required(check):
    assert check in REQUIRED


def test_the_merge_method_is_a_merge_commit():
    # The team merges with a merge commit, as the live ruleset of main allows
    assert rule(MAIN, "pull_request")["allowed_merge_methods"] == ["merge"]


def test_no_linear_history_is_asked_for_with_merge_commits():
    assert all(item["type"] != "required_linear_history" for item in MAIN["rules"])


def test_dependabot_merges_with_the_allowed_method():
    workflow = (WORKFLOWS / "dependabot-auto-merge.yml").read_text(encoding="utf-8")
    methods = set(re.findall(r"gh pr merge [^\n]*--(merge|rebase|squash)\b", workflow))

    assert methods == {"merge"}


def test_contributing_names_the_same_merge_method():
    assert "Rebase and merge" not in CONTRIBUTING
    assert "Create a merge commit" in CONTRIBUTING


def test_contributing_updates_the_existing_ruleset_of_main():
    # POST would add a second ruleset next to the live one, PUT replaces it
    assert "rulesets --method POST --input .github/rulesets/main.json" not in CONTRIBUTING
    assert re.search(r"rulesets/\d+ --method PUT --input \.github/rulesets/main\.json", CONTRIBUTING)


def test_every_listed_check_is_named_in_contributing():
    for check in REQUIRED:
        assert check in CONTRIBUTING, f"{check} is required but CONTRIBUTING.md does not name it"
