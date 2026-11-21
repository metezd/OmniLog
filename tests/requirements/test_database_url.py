"""The database URL of a host without a driver (Render gives "postgresql://...") uses psycopg2."""
import pytest
from sqlalchemy.engine import make_url

from app.core.database import normalize_database_url


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:pa%40ss@dpg-abc/omnilog",
        "postgres://user:pa%40ss@dpg-abc/omnilog",
    ],
)
def test_a_url_without_a_driver_gets_psycopg2(url):
    result = make_url(normalize_database_url(url))

    assert result.drivername == "postgresql+psycopg2"
    assert result.get_dialect().driver == "psycopg2"
    assert (result.username, result.password, result.host, result.database) == ("user", "pa@ss", "dpg-abc", "omnilog")


def test_the_query_part_is_kept():
    result = make_url(normalize_database_url("postgresql://u:p@h:5433/db?sslmode=require"))

    assert result.port == 5433 and result.query == {"sslmode": "require"}


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg2://u:p@localhost/x",
        "postgresql+psycopg://u:p@localhost/x",
        "sqlite:///./omnilog_local.db",
    ],
)
def test_a_url_that_names_a_driver_is_not_changed(url):
    assert normalize_database_url(url) == url
