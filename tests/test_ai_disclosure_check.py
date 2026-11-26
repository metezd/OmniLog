"""The check "AI disclosure" of .github/workflows/pr-title.yml (#309).

It reads the section "AI assistance" of the pull request description: exactly one of the three
boxes must be ticked, and the label ai-assisted must be on the pull request when AI helped.
The tests run the script of the workflow step with bash, the same way GitHub runs it.
"""
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pr-title.yml"
TEMPLATE = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


def job():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["ai-disclosure"]


def run_check(body, has_label):
    script = job()["steps"][0]["run"]
    env = {"PATH": "/usr/bin:/bin", "BODY": body, "HAS_LABEL": "true" if has_label else "false"}
    # The script comes from the workflow file of this repository, not from user input
    return subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)  # noqa: S603, S607


def tick(box):
    return TEMPLATE.replace(f"- [ ] {box}", f"- [x] {box}")


def test_the_job_is_named_and_reads_only():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert data["permissions"] == {"contents": "read"}
    assert job()["name"] == "AI disclosure"
    # The description is user input: it reaches the script only through env
    step = job()["steps"][0]
    assert "github.event" not in step["run"]
    assert step["env"]["BODY"] == "${{ github.event.pull_request.body }}"


def test_dependabot_is_skipped():
    assert "dependabot[bot]" in job()["if"]


@pytest.mark.parametrize("label", [True, False])
def test_none_passes_with_or_without_the_label(label):
    assert run_check(tick("None"), has_label=label).returncode == 0


@pytest.mark.parametrize("box", ["AI helped", "AI wrote most of it"])
def test_ai_help_with_the_label_passes(box):
    assert run_check(tick(box), has_label=True).returncode == 0


@pytest.mark.parametrize("box", ["AI helped", "AI wrote most of it"])
def test_ai_help_without_the_label_fails(box):
    result = run_check(tick(box), has_label=False)

    assert result.returncode == 1
    assert "ai-assisted" in result.stdout


def test_an_upper_case_x_counts():
    body = TEMPLATE.replace("- [ ] None", "- [X] None")
    assert run_check(body, has_label=False).returncode == 0


def test_no_box_ticked_fails():
    result = run_check(TEMPLATE, has_label=False)

    assert result.returncode == 1
    assert "Tick one box" in result.stdout


def test_two_boxes_ticked_fail():
    body = tick("None").replace("- [ ] AI helped", "- [x] AI helped")
    assert run_check(body, has_label=True).returncode == 1


def test_a_description_without_the_section_fails():
    result = run_check("Fixes the login page.", has_label=False)

    assert result.returncode == 1
    assert "AI assistance" in result.stdout


def test_an_empty_description_fails():
    assert run_check("", has_label=False).returncode == 1


def test_a_box_outside_the_section_does_not_count():
    body = "## Checklist\n\n- [x] None\n\n## AI assistance\n\n- [ ] None\n- [ ] AI helped\n- [ ] AI wrote most of it\n"
    assert run_check(body, has_label=False).returncode == 1


def test_windows_line_endings_are_read():
    body = tick("AI helped").replace("\n", "\r\n")
    assert run_check(body, has_label=True).returncode == 0


def test_a_pasted_command_is_not_run(tmp_path):
    marker = tmp_path / "ran"
    body = tick("None") + f"\n::error title=x::injected\n$(touch {marker})\n`touch {marker}`\n"
    result = run_check(body, has_label=False)

    assert result.returncode == 0
    assert "injected" not in result.stdout
    assert not marker.exists()
