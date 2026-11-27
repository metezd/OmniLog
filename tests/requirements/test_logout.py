"""POST /auth/logout ends the token of the request (US-03, NFR-02, #378).

Before, "Log out" only deleted the cookie, and a copied token worked for 90 more minutes.
"""
import threading
from datetime import timedelta

import jwt

from app.core import config
from app.core.clock import utc_now
from app.core.database import SessionLocal
from app.core.security import JWT_ALGORITHM, create_access_token, read_access_token
from app.models.entities import RevokedToken
from app.services import auth_service
from helpers import new_credentials


def register(client):
    credentials = new_credentials()
    assert client.post("/auth/register", json=credentials).status_code == 201
    return credentials


def login(client, credentials):
    response = client.post(
        "/auth/login", json={"username": credentials["username"], "password": credentials["password"]}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def token_of(headers):
    return headers["Authorization"].removeprefix("Bearer ")


# ---------------------------------------------------------------- logout
def test_a_token_is_refused_after_logout(client):
    headers = login(client, register(client))
    assert client.get("/auth/me", headers=headers).status_code == 200

    response = client.post("/auth/logout", headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.get("/library", headers=headers).status_code == 401


def test_the_other_tokens_of_the_same_user_still_work(client):
    credentials = register(client)
    laptop = login(client, credentials)
    phone = login(client, credentials)

    client.post("/auth/logout", headers=laptop)

    assert client.get("/auth/me", headers=phone).status_code == 200
    assert client.get("/auth/me", headers=laptop).status_code == 401


def test_a_new_login_after_logout_works(client):
    credentials = register(client)
    client.post("/auth/logout", headers=login(client, credentials))

    assert client.get("/auth/me", headers=login(client, credentials)).status_code == 200


def test_logout_needs_a_token(client):
    response = client.post("/auth/logout")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_second_logout_of_the_same_token_is_401(client):
    headers = login(client, register(client))
    client.post("/auth/logout", headers=headers)

    assert client.post("/auth/logout", headers=headers).status_code == 401


def test_logout_with_an_invalid_token_is_401(client):
    assert client.post("/auth/logout", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


# ---------------------------------------------------------------- the stored rows
def test_the_row_is_kept_until_the_token_would_expire(client, db):
    headers = login(client, register(client))
    claims = read_access_token(token_of(headers))

    client.post("/auth/logout", headers=headers)

    row = db.get(RevokedToken, claims.jti)
    assert row is not None
    assert row.user_id == claims.user_id
    assert row.expires_at == claims.expires_at
    remaining = row.expires_at - utc_now()
    assert timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES - 1) < remaining <= timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )


def test_a_logout_deletes_the_rows_of_expired_tokens(client, db):
    credentials = register(client)
    user_id = client.get("/auth/me", headers=login(client, credentials)).json()["id"]
    db.add(RevokedToken(jti="old-expired-token", user_id=user_id, expires_at=utc_now() - timedelta(minutes=1)))
    db.commit()

    client.post("/auth/logout", headers=login(client, credentials))

    db.expire_all()
    assert db.get(RevokedToken, "old-expired-token") is None


def test_two_logouts_of_the_same_token_at_the_same_time_do_not_fail(client):
    headers = login(client, register(client))
    claims = read_access_token(token_of(headers))
    barrier = threading.Barrier(2)
    errors = []

    def logout():
        session = SessionLocal()
        try:
            barrier.wait()
            auth_service.revoke_token(session, claims)
        except Exception as exc:  # noqa: BLE001 - the test reports any error
            errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=logout) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert client.get("/auth/me", headers=headers).status_code == 401


# ---------------------------------------------------------------- the jti claim
def test_every_token_has_its_own_jti():
    first = read_access_token(create_access_token(7))
    second = read_access_token(create_access_token(7))

    assert first.jti != second.jti


def test_a_token_without_jti_is_refused(client):
    credentials = register(client)
    user_id = client.get("/auth/me", headers=login(client, credentials)).json()["id"]
    claims = jwt.decode(token_of(login(client, credentials)), options={"verify_signature": False})
    del claims["jti"]
    old_style = jwt.encode(claims | {"sub": str(user_id)}, config.SECRET_KEY, algorithm=JWT_ALGORITHM)

    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old_style}"}).status_code == 401


def test_a_token_with_a_too_long_jti_is_refused():
    claims = jwt.decode(create_access_token(7), options={"verify_signature": False})
    token = jwt.encode(claims | {"jti": "x" * 65}, config.SECRET_KEY, algorithm=JWT_ALGORITHM)

    assert read_access_token(token) is None
