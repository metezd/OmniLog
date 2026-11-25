"""F3 of the penetration test: poster_url only from the image hosts of TMDB and IGDB (#303, US-08).

POST /media checks it since #218 (tests/requirements/test_media_access.py). The same rule must hold
for the update schema, and for the exact addresses that the issue names.
"""
import pytest
from pydantic import ValidationError

from app.schemas.media import MediaItemCreate, MediaItemUpdate

GOOD = ["https://image.tmdb.org/t/p/w500/a.jpg", "https://images.igdb.com/igdb/image/upload/t_cover_big/a.jpg"]
BAD = [
    "javascript:alert(1)",
    "data:image/png;base64,AAAA",
    "http://image.tmdb.org/t/p/w500/a.jpg",
    "https://attacker.example/pixel.png",
    "https://image.tmdb.org.evil.example/a.jpg",
    "https://image.tmdb.org@evil.example/a.jpg",
    "https://user@image.tmdb.org/a.jpg",
    "https://image.tmdb.org:8443/a.jpg",
    "//image.tmdb.org/a.jpg",
    "HTTPS://evil.example/a.jpg",
]


@pytest.mark.parametrize("schema", [MediaItemCreate, MediaItemUpdate])
@pytest.mark.parametrize("url", GOOD)
def test_f3_us08_tmdb_and_igdb_images_are_accepted(schema, url):
    assert schema(title="A title", media_type="GAME", poster_url=url).poster_url == url


@pytest.mark.parametrize("schema", [MediaItemCreate, MediaItemUpdate])
@pytest.mark.parametrize("url", BAD)
def test_f3_us08_other_addresses_are_refused(schema, url):
    with pytest.raises(ValidationError, match="poster_url"):
        schema(title="A title", media_type="GAME", poster_url=url)


def test_f3_us08_an_update_without_a_poster_is_fine():
    assert MediaItemUpdate(title="Only the title").poster_url is None
