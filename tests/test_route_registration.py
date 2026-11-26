import os
import sys
import warnings
from pathlib import Path

import pytest

# No connection is made: the test only reads the OpenAPI schema
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://u:p@localhost:5432/unused")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-openapi-guard")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def test_no_duplicate_operation_ids_in_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app, "openapi_schema", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app.openapi()

    duplicate_warnings = [
        str(item.message)
        for item in caught
        if "Duplicate Operation ID" in str(item.message)
    ]
    assert not duplicate_warnings, f"Unexpected OpenAPI warnings: {duplicate_warnings}"