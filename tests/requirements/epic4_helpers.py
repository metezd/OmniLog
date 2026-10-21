"""Helpers shared by the Epic 4 tests (chapter rating and playtime).

The chapters of a game have no outside source and no endpoint creates them yet (open point 3 in
docs/analysis/data/domain-model.md), so the tests save chapters in the database directly.
"""
from app.models.entities import Chapter, ChapterKind, Season, DecisionOption, DecisionPoint


def add_chapter(db, media_id, number=1):
    """Save a game chapter and return its id."""
    chapter = Chapter(
        media_item_id=media_id, number=number, kind=ChapterKind.CHAPTER, title=f"Chapter {number}"
    )
    db.add(chapter)
    db.commit()
    return chapter.id


def add_episode(db, media_id, number=1):
    """Save a season with one episode and return the id of the episode."""
    season = Season(media_item_id=media_id, season_number=1, title="Season 1")
    db.add(season)
    db.flush()
    episode = Chapter(
        media_item_id=media_id,
        season_id=season.id,
        number=number,
        kind=ChapterKind.EPISODE,
        title=f"Episode {number}",
    )
    db.add(episode)
    db.commit()
    return episode.id


def diary_actions(client, headers):
    """The action names of the diary of the user, newest first."""
    return [event["action"] for event in client.get("/diary", headers=headers).json()]

def add_decision_point(db, chapter_id, media_id=None, labels=("A", "B"), position=1, prompt="Choice 1"):
    """Save a decision point with given option labels and return its id."""
    point = DecisionPoint(
        chapter_id=chapter_id,
        media_item_id=media_id,
        prompt=prompt,
        position=position,
    )
    db.add(point)
    db.flush()

    for label in labels:
        opt = DecisionOption(
            decision_point_id=point.id,
            label=label,
            text=f"Option {label}",
        )
        db.add(opt)

    db.commit()
    return point.id