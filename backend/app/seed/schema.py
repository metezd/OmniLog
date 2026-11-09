"""The shape of the seed file. A file that does not fit is refused before the database is touched.

Names follow the database, so a value in the file has the same limits as its column. Unknown keys
are refused too, so a typo such as "decison_points" is an error, not a silent gap.
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SeedOption(_Strict):
    label: str = Field(min_length=1, max_length=10)  # Short label such as A or B
    text: Optional[str] = Field(default=None, min_length=1, max_length=200)


class SeedDecisionPoint(_Strict):
    """A question of a chapter. Its position is its place in the list, starting at 1."""

    prompt: str = Field(min_length=1, max_length=300)
    # One option is not a decision
    options: List[SeedOption] = Field(min_length=2)

    @model_validator(mode="after")
    def labels_are_unique(self):
        labels = [option.label for option in self.options]
        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        if duplicates:
            raise ValueError(f"option labels must be unique, repeated: {', '.join(duplicates)}")
        return self


class SeedChapter(_Strict):
    number: StrictInt = Field(ge=0)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    release_date: Optional[str] = Field(default=None, min_length=1, max_length=50)
    runtime_minutes: Optional[StrictInt] = Field(default=None, ge=0)
    decision_points: List[SeedDecisionPoint] = []


class SeedGame(_Strict):
    # The id of the game at IGDB. It is the key that joins the seed and the catalog.
    external_api_id: StrictInt
    # Only used when the game is not in the catalog yet. A saved game keeps its own metadata.
    title: str = Field(min_length=1, max_length=200)
    poster_url: Optional[str] = Field(default=None, min_length=1, max_length=500)
    release_date: Optional[str] = Field(default=None, min_length=1, max_length=50)
    chapters: List[SeedChapter] = Field(min_length=1)

    @field_validator("external_api_id")
    @classmethod
    def id_is_an_igdb_id(cls, value: int) -> int:
        if value < 1:
            raise ValueError(
                "external_api_id must be the IGDB id of the game (a positive number). Search the "
                "title with GET /catalog/search?type=GAME and read external_api_id"
            )
        return value

    @model_validator(mode="after")
    def chapter_numbers_are_unique(self):
        numbers = [chapter.number for chapter in self.chapters]
        duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
        if duplicates:
            raise ValueError(f"chapter numbers must be unique, repeated: {duplicates}")
        return self


class SeedFile(_Strict):
    games: List[SeedGame]

    @model_validator(mode="after")
    def games_are_unique(self):
        ids = [game.external_api_id for game in self.games]
        duplicates = sorted({game_id for game_id in ids if ids.count(game_id) > 1})
        if duplicates:
            raise ValueError(f"a game can be in the file once, repeated ids: {duplicates}")
        return self
