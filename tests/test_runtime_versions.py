"""CI and Render use the Python and Node.js versions of the production images (#379).

The Dockerfiles are the one place for the versions. CI reads them from the FROM lines, and
render.yaml must give the same versions, so a Dependabot bump of a base image cannot make CI,
Docker and Render drift apart again.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
SERVICES = {s["name"]: s for s in BLUEPRINT["services"]}
CI = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


def _image_version(dockerfile, image):
    text = (ROOT / dockerfile).read_text(encoding="utf-8")
    versions = set(re.findall(rf"^FROM {image}:([0-9][0-9.]*)-", text, flags=re.MULTILINE))
    assert len(versions) == 1, f"{dockerfile} must use one {image} version, found {versions}"
    return versions.pop()


def _render_env(service, key):
    env = {item["key"]: str(item.get("value")) for item in SERVICES[service]["envVars"]}
    return env[key]


def _steps(job):
    return CI["jobs"][job]["steps"]


def test_render_python_is_the_python_of_the_backend_image():
    image = _image_version("backend/Dockerfile", "python")
    render = _render_env("omnilog-api", "PYTHON_VERSION")

    # Render needs a full version such as 3.15.0 in PYTHON_VERSION. Only the minor version must be
    # the one of the image: Render may not offer the newest patch yet (3.15.2 failed the build).
    assert re.fullmatch(r"\d+\.\d+\.\d+", render), render
    assert render.startswith(image + "."), f"render.yaml has {render}, the image has {image}"


def test_render_node_is_the_node_of_the_frontend_image():
    image = _image_version("frontend/Dockerfile", "node")
    render = _render_env("omnilog-web", "NODE_VERSION")

    assert render.split(".")[0] == image.split(".")[0]


def test_frontend_checks_read_node_from_the_dockerfile():
    steps = _steps("frontend")
    setup = next(s for s in steps if s.get("uses", "").startswith("actions/setup-node@"))
    reader = next(s for s in steps if s.get("id") == "node")

    assert setup["with"]["node-version"] == "${{ steps.node.outputs.version }}"
    assert "frontend/Dockerfile" in reader["run"]
    assert steps.index(reader) < steps.index(setup)


def test_backend_tests_read_python_from_the_dockerfile():
    for step in _steps("backend"):
        if step.get("uses", "").startswith("actions/setup-python@"):
            assert step["with"]["python-version"] == "${{ steps.python.outputs.version }}"
