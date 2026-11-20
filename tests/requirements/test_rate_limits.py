"""Rate limits for login, register, search and review (#217, NFR-04).

A fake clock decides the time window, so a test can let a window end without waiting. The tests
run against Redis when it is up, and every test also has a version where Redis is down.
"""
import pytest
from fastapi.testclient import TestClient

from app.core import cache, config, rate_limit
from app.main import app

from helpers import add_to_library, create_media, new_credentials, register_and_login


class FakeClock:
    """Stands in for the `time` module of app/core/rate_limit.py."""

    # The start of an hour, so a test is never cut by the end of a window by chance
    now = 1_800_000_000.0

    @classmethod
    def time(cls) -> float:
        return cls.now


@pytest.fixture(params=["redis", "redis down"])
def limits_on(request, monkeypatch):
    """Turn the limits on with a fake clock, once with Redis and once with Redis down."""
    if request.param == "redis down":
        monkeypatch.setattr(config, "REDIS_URL", "redis://127.0.0.1:1/0")
    cache.reset_connection()
    if request.param == "redis" and not cache.is_available():
        pytest.skip("Redis is not running")

    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(FakeClock, "now", FakeClock.now)
    monkeypatch.setattr(rate_limit, "time", FakeClock)
    # Redis keeps the counts between test runs, the fake clock gives the same windows every run
    cache.clear_prefix("omni:ratelimit:")
    rate_limit.reset()
    yield request.param
    cache.clear_prefix("omni:ratelimit:")
    cache.reset_connection()


def client_at(address: str) -> TestClient:
    """A test client that calls from the given address."""
    return TestClient(app, client=(address, 50000))


def login(client: TestClient, username: str = "nobody"):
    return client.post("/auth/login", json={"username": username, "password": "WrongPass123!"})


def assert_limited(response, retry_after: int) -> None:
    assert response.status_code == 429, response.text
    assert response.headers["Retry-After"] == str(retry_after)
    # The same error shape as the other errors of the API
    assert response.json() == {"detail": f"Too many requests. Try again in {retry_after} seconds."}


# ------------------------------------------------------------------------------------- login
def test_login_is_limited_per_address_and_opens_again_after_the_window(limits_on):
    client = client_at("10.0.0.1")
    for _ in range(10):  # default: 10 per minute
        assert login(client).status_code == 401

    FakeClock.now += 15
    assert_limited(login(client), retry_after=45)

    FakeClock.now += 45
    assert login(client).status_code == 401


def test_login_limit_of_one_address_does_not_block_another(limits_on):
    for _ in range(10):
        login(client_at("10.0.0.2"))
    assert login(client_at("10.0.0.2")).status_code == 429

    assert login(client_at("10.0.0.3")).status_code == 401


def test_a_correct_password_is_also_counted(limits_on, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_LOGIN", (2, 60))
    client = client_at("10.0.0.4")
    credentials = new_credentials()
    register_and_login(client, credentials)  # one login

    assert login(client).status_code == 401
    assert_limited(login(client, credentials["username"]), retry_after=60)


# ---------------------------------------------------------------------------------- register
def test_register_is_limited_per_address(limits_on):
    client = client_at("10.0.1.1")
    for _ in range(5):  # default: 5 per hour
        assert client.post("/auth/register", json=new_credentials()).status_code == 201

    assert_limited(client.post("/auth/register", json=new_credentials()), retry_after=3600)
    assert client_at("10.0.1.2").post("/auth/register", json=new_credentials()).status_code == 201

    FakeClock.now += 3600
    assert client.post("/auth/register", json=new_credentials()).status_code == 201


# ------------------------------------------------------------------------------------ search
def search(client: TestClient, headers: dict, text: str = "zelda"):
    return client.get("/catalog/search", params={"q": text, "type": "GAME"}, headers=headers)


def test_search_is_limited_per_user(limits_on, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_SEARCH", (3, 60))
    # Both users call from the same address, so the limit must follow the user
    client = client_at("10.0.2.1")
    first = register_and_login(client, new_credentials())
    second = register_and_login(client, new_credentials())

    for number in range(3):
        assert search(client, first, f"title {number}").status_code == 200
    assert_limited(search(client, first), retry_after=60)
    assert search(client, second).status_code == 200

    FakeClock.now += 60
    assert search(client, first).status_code == 200


def test_search_without_a_token_is_401_and_not_counted(limits_on, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_SEARCH", (1, 60))
    client = client_at("10.0.2.2")
    headers = register_and_login(client, new_credentials())

    for _ in range(3):
        assert client.get("/catalog/search", params={"q": "zelda", "type": "GAME"}).status_code == 401
    assert search(client, headers).status_code == 200


# ------------------------------------------------------------------------------------ review
def test_review_is_limited_per_user(limits_on, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_REVIEW", (2, 60))
    client = client_at("10.0.3.1")
    headers = register_and_login(client, new_credentials())
    entry = add_to_library(client, headers, create_media(client, headers)["id"])
    other = register_and_login(client, new_credentials())
    other_entry = add_to_library(client, other, create_media(client, other)["id"])

    def review(entry_id: int, auth: dict):
        return client.post(f"/library/{entry_id}/review", json={"text": "A calm and lovely game."}, headers=auth)

    assert review(entry["id"], headers).status_code == 201
    assert review(entry["id"], headers).status_code == 200
    assert_limited(review(entry["id"], headers), retry_after=60)
    assert review(other_entry["id"], other).status_code == 201

    FakeClock.now += 60
    assert review(entry["id"], headers).status_code == 200


# ------------------------------------------------------------------------- Redis and settings
def test_redis_down_gives_no_500(limits_on):
    if limits_on != "redis down":
        pytest.skip("only with Redis down")
    client = client_at("10.0.4.1")

    for _ in range(10):
        assert login(client).status_code == 401
    assert login(client).status_code == 429


def test_limits_can_be_turned_off(limits_on, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
    client = client_at("10.0.4.2")

    for _ in range(12):
        assert login(client).status_code == 401


@pytest.mark.parametrize(
    ("text", "expected"),
    [("10/minute", (10, 60)), ("5/HOUR", (5, 3600)), (" 1/second ", (1, 1)), ("2/day", (2, 86400))],
)
def test_a_limit_setting_is_read(monkeypatch, text, expected):
    monkeypatch.setenv("RATE_LIMIT_TEST", text)

    assert config._rate_limit("RATE_LIMIT_TEST", "1/minute") == expected


@pytest.mark.parametrize("text", ["10", "0/minute", "-1/minute", "ten/minute", "10/week", "10/"])
def test_a_wrong_limit_setting_stops_the_start(monkeypatch, text):
    monkeypatch.setenv("RATE_LIMIT_TEST", text)

    with pytest.raises(RuntimeError, match="RATE_LIMIT_TEST"):
        config._rate_limit("RATE_LIMIT_TEST", "1/minute")
