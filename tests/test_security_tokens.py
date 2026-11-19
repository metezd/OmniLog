"""Security unit tests for JWT verification edge cases."""
from datetime import datetime, timedelta, timezone
import jwt
import pytest

from app.core.config import SECRET_KEY
from app.core.security import create_access_token, decode_access_token, JWT_ALGORITHM


def test_valid_token():
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42


def test_expired_token():
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired_payload = {"sub": "42", "exp": past_time}
    token = jwt.encode(expired_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_wrong_signature():
    payload = {"sub": "42", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    token = jwt.encode(payload, "completely-wrong-secret-key", algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_alg_none_token():
    payload = {"sub": "42", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    token = jwt.encode(payload, key="", algorithm="none")
    assert decode_access_token(token) is None


def test_different_algorithm():
    payload = {"sub": "42", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS384")
    assert decode_access_token(token) is None


def test_token_without_sub():
    payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_token_without_exp():
    # Signed with the right key but without exp. It must not be valid forever.
    token = jwt.encode({"sub": "42"}, SECRET_KEY, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_new_token_has_iat_and_exp():
    token = create_access_token(user_id=42)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert {"sub", "iat", "exp"} <= payload.keys()
    assert payload["iat"] < payload["exp"]
