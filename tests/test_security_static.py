"""Security checks for the backend code that Ruff's S rules do not cover.

These tests replace the project rules of the old Semgrep setup for JWT decoding, the CORS
wildcard, FastAPI debug mode, secrets in log lines and SQL built from formatted strings. Each
check is a small function over the syntax tree of a file. The "bad code" tests run every check
on a few lines of unsafe code, so a broken check cannot pass without anyone noticing.
"""
import ast
import re
import sys
from functools import cache
from pathlib import Path

import pytest

# Make `import app...` work when pytest is started from the repo root.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

SKIPPED_FOLDERS = {"venv", ".venv", "__pycache__", "node_modules"}
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
SENSITIVE_WORDS = re.compile(r"password|passwd|secret|token|api[_-]?key", re.IGNORECASE)
SQL_CALLS = {"text", "execute", "exec_driver_sql"}


# ------------------------------------------------------------------ helpers
def _dotted(node: ast.AST) -> str:
    """Return a name like `jwt.decode` for a Name or Attribute node, or an empty string."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _is_constant(node: ast.AST, value: object) -> bool:
    return isinstance(node, ast.Constant) and node.value is value


def _keyword(call: ast.Call, name: str) -> ast.keyword | None:
    return next((item for item in call.keywords if item.arg == name), None)


# ------------------------------------------------------------------ checks
# Every check takes a syntax tree and returns the line numbers of the problems it finds.
def check_jwt(tree: ast.AST) -> list[int]:
    """jwt.decode needs a fixed algorithms list, and the signature check must stay on."""
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if _dotted(node.func) == "jwt.decode":
                algorithms = _keyword(node, "algorithms")
                allows_none = algorithms is not None and any(
                    isinstance(part, ast.Constant) and str(part.value).lower() == "none"
                    for part in ast.walk(algorithms.value)
                )
                if algorithms is None or allows_none:
                    lines.append(node.lineno)
            for item in node.keywords:
                if item.arg in {"verify_signature", "verify"} and _is_constant(item.value, False):
                    lines.append(node.lineno)
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "verify_signature"
                    and _is_constant(value, False)
                ):
                    lines.append(node.lineno)
    return lines


def check_debug_mode(tree: ast.AST) -> list[int]:
    """FastAPI and Starlette must not be created with debug=True."""
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _dotted(node.func).split(".")[-1] in {"FastAPI", "Starlette"}:
            debug = _keyword(node, "debug")
            if debug is not None and _is_constant(debug.value, True):
                lines.append(node.lineno)
    return lines


def check_cors_wildcard(tree: ast.AST) -> list[int]:
    """allow_origins must be an explicit list, never "*" or a match-everything regex."""
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        origins = _keyword(node, "allow_origins")
        if origins is not None and any(
            isinstance(part, ast.Constant) and part.value == "*" for part in ast.walk(origins.value)
        ):
            lines.append(node.lineno)
        pattern = _keyword(node, "allow_origin_regex")
        if pattern is not None and isinstance(pattern.value, ast.Constant):
            if pattern.value.value in {".*", ".+", "^.*$"}:
                lines.append(node.lineno)
    return lines


def check_sensitive_logging(tree: ast.AST) -> list[int]:
    """A log call must not mention a password, secret, token or API key."""
    lines = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in LOG_METHODS:
            continue
        owner = _dotted(node.func.value).split(".")[-1].lower()
        if not (owner == "logging" or owner.endswith("log") or owner.endswith("logger")):
            continue
        arguments = [*node.args, *(item.value for item in node.keywords if item.arg != "exc_info")]
        for argument in arguments:
            for part in ast.walk(argument):
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    text = part.value
                elif isinstance(part, ast.Name):
                    text = part.id
                elif isinstance(part, ast.Attribute):
                    text = part.attr
                else:
                    continue
                if SENSITIVE_WORDS.search(text):
                    lines.append(node.lineno)
                    break
            else:
                continue
            break
    return lines


def _is_built_string(node: ast.AST) -> bool:
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(part, ast.FormattedValue) for part in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return not (isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant))
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Attribute) and node.func.attr == "format"
    return False


def check_sql_strings(tree: ast.AST) -> list[int]:
    """SQL text must be a plain string with bound parameters, never an f-string or a sum."""
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            if _dotted(node.func).split(".")[-1] in SQL_CALLS and _is_built_string(node.args[0]):
                lines.append(node.lineno)
    return lines


CHECKS = {
    "jwt": check_jwt,
    "debug": check_debug_mode,
    "cors": check_cors_wildcard,
    "logging": check_sensitive_logging,
    "sql": check_sql_strings,
}

HOW_TO_FIX = {
    "jwt": 'Call jwt.decode(..., algorithms=["HS256"]) and never turn off the signature check.',
    "debug": "Do not create the app with debug=True.",
    "cors": "Use the explicit CORS_ORIGINS list from the settings.",
    "logging": "Log an id or a fixed message, never a password, secret, token or API key.",
    "sql": 'Use text("... :name") with bound parameters, not an f-string or string concatenation.',
}


# ------------------------------------------------------------------ the backend code
@cache
def _backend_trees() -> dict[str, ast.AST]:
    trees = {}
    for path in sorted(BACKEND_DIR.rglob("*.py")):
        if SKIPPED_FOLDERS & set(path.relative_to(BACKEND_DIR).parts):
            continue
        # utf-8-sig, because some files start with a byte order mark
        source = path.read_text(encoding="utf-8-sig")
        trees[str(path.relative_to(BACKEND_DIR.parent))] = ast.parse(source, filename=str(path))
    return trees


def test_backend_files_were_found():
    """Guards the checks below: with no files they would pass without checking anything."""
    names = _backend_trees()
    assert "backend/app/main.py" in names or "backend\\app\\main.py" in names
    assert len(names) > 20


@pytest.mark.parametrize("check_name", CHECKS)
def test_backend_code_has_no_insecure_pattern(check_name):
    problems = [
        f"{name}:{line}"
        for name, tree in _backend_trees().items()
        for line in CHECKS[check_name](tree)
    ]
    assert not problems, f"{HOW_TO_FIX[check_name]}\n" + "\n".join(problems)


# ------------------------------------------------------------------ bad code
BAD_CODE = [
    ("jwt", "jwt.decode(token, key)"),
    ("jwt", 'jwt.decode(token, key, algorithms=["HS256", "none"])'),
    ("jwt", 'jwt.decode(token, key, algorithms=["HS256"], options={"verify_signature": False})'),
    ("jwt", 'jwt.decode(token, key, algorithms=["HS256"], verify=False)'),
    ("debug", "app = FastAPI(title='x', debug=True)"),
    ("cors", 'app.add_middleware(CORSMiddleware, allow_origins=["*"])'),
    ("cors", 'app.add_middleware(CORSMiddleware, allow_origin_regex=".*")'),
    ("logging", 'logger.info("login for %s", password)'),
    ("logging", 'logger.warning(f"token is {value}")'),
    ("logging", 'logging.error("api_key missing")'),
    ("logging", 'self.logger.debug("sent", user.access_token)'),
    ("sql", 'db.execute(f"DELETE FROM t WHERE a = {value}")'),
    ("sql", 'text(f"{value}")'),
    ("sql", 'text("SELECT * FROM t WHERE a = " + value)'),
    ("sql", 'text("SELECT * FROM t WHERE a = {}".format(value))'),
]

GOOD_CODE = [
    ("jwt", 'jwt.decode(token, key, algorithms=["HS256"])'),
    ("jwt", "jwt.decode(token, key, algorithms=[ALGORITHM])"),
    ("debug", "app = FastAPI(title='x')"),
    ("debug", "app = FastAPI(debug=False)"),
    ("cors", "app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS)"),
    ("cors", 'app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"])'),
    ("logging", 'logger.warning("TMDB sent no details for series %s", series_id)'),
    ("logging", 'print("token")'),
    ("sql", 'text("SELECT * FROM t WHERE a = :a")'),
    ("sql", 'db.execute(text("SELECT 1"), {"a": 1})'),
    ("sql", 'text("part one " "part two")'),
]


@pytest.mark.parametrize(("check_name", "code"), BAD_CODE)
def test_check_finds_bad_code(check_name, code):
    assert CHECKS[check_name](ast.parse(code)), f"{check_name} did not find: {code}"


@pytest.mark.parametrize(("check_name", "code"), GOOD_CODE)
def test_check_accepts_safe_code(check_name, code):
    assert CHECKS[check_name](ast.parse(code)) == [], f"{check_name} wrongly flagged: {code}"


# ------------------------------------------------------------------ the running app
EVIL_ORIGIN = "https://malicious-attacker-website.com"


@pytest.fixture(scope="module")
def running_app():
    from app.main import app

    return app


def test_app_debug_mode_is_off(running_app):
    assert running_app.debug is False


def test_cors_settings_have_no_wildcard(running_app):
    from fastapi.middleware.cors import CORSMiddleware

    from app.core.config import CORS_ORIGINS

    cors = [item for item in running_app.user_middleware if item.cls is CORSMiddleware]
    assert len(cors) == 1
    assert "*" not in cors[0].kwargs["allow_origins"]
    assert not cors[0].kwargs.get("allow_origin_regex")
    assert "*" not in CORS_ORIGINS


def test_cors_does_not_answer_an_unknown_origin(running_app):
    """With credentials turned on, a wildcard would copy the origin back, so look for any header."""
    from fastapi.testclient import TestClient

    client = TestClient(running_app)
    preflight = client.options(
        "/", headers={"Origin": EVIL_ORIGIN, "Access-Control-Request-Method": "GET"}
    )
    normal = client.get("/", headers={"Origin": EVIL_ORIGIN})

    assert "access-control-allow-origin" not in preflight.headers
    assert "access-control-allow-origin" not in normal.headers
