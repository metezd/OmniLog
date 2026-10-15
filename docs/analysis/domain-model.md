# Domain Model

> **Note:** this document describes the baseline that is already implemented. The full analysis model for all six epics is in [data/domain-model.md](data/domain-model.md).

This document summarizes the current domain model for OmniLog as represented in the backend data model and aligned with the project requirements. The scope is intentionally limited to the entities that already exist in the codebase and the relationships needed to support media tracking and personal library management.

## Core entities

### 1. User

Represents an authenticated application user.

Important fields:
- `id`: unique primary key
- `username`: unique username used for login and display
- `email`: unique email address
- `hashed_password`: password hash, never stored in plain text
- `created_at`: account creation timestamp

Responsibilities:
- Owns a personal media library
- Can manage watch status and rating for media items
- Serves as the root identity for library records

Relationships:
- One user can have many `UserLibrary` entries

Rules / assumptions:
- `username` and `email` must be unique
- Every user must have a hashed password

---

### 2. MediaItem

Represents a media title in the catalog, such as a game, movie, or TV series.

Important fields:
- `id`: unique primary key
- `title`: display title of the media item
- `media_type`: enum value (`GAME`, `SERIES`, `MOVIE`)
- `poster_url`: optional URL to the cover art
- `release_date`: optional release or first-air information
- `external_api_id`: optional external reference from a third-party service such as IGDB or TMDB

Responsibilities:
- Provides a canonical catalog item for each title
- Supports cross-media lookup and metadata binding
- Acts as the shared reference for user library entries

Relationships:
- One media item can appear in many `UserLibrary` records

Rules / assumptions:
- `media_type` is required
- Title is required for catalog identity
- External IDs are optional and may be null when the item is not linked to an external source

---

### 3. UserLibrary

Association entity that connects a user to a media item and tracks their personal relationship to it.

Important fields:
- `id`: unique primary key
- `user_id`: foreign key to `users.id`
- `media_item_id`: foreign key to `media_items.id`
- `status`: enum value representing current watch/play state (`PLAN_TO_WATCH`, `IN_PROGRESS`, `COMPLETED`, `DROPPED`)
- `rating`: optional numeric rating from 1 to 10
- `updated_at`: timestamp of the last modification

Responsibilities:
- Stores the relationship between a user and a media item
- Tracks personal progress and user evaluation
- Prevents duplicate library entries for the same pair of user and media item

Relationships:
- Many `UserLibrary` rows belong to one user
- Many `UserLibrary` rows reference one media item

Rules / assumptions:
- A user cannot add the same media item twice to the same library
- `rating` must be between 1 and 10 when provided
- Status defaults to `PLAN_TO_WATCH` when no explicit value is provided

---

## Relationship summary

The domain model follows a classic many-to-one association pattern:

- `User` to `UserLibrary`: 1:N
- `MediaItem` to `UserLibrary`: 1:N
- `UserLibrary` is the join table between users and media items

This model supports the core OmniLog requirement of letting users maintain a personal library of games and shows while preserving a reusable catalog of media titles.

## Example flow

A typical workflow is:

1. A user registers an account.
2. The user adds a media title to their library.
3. A `UserLibrary` row is created for the pair `(user_id, media_item_id)`.
4. The user updates `status` and optionally `rating`.
5. `updated_at` is refreshed whenever the row changes.

This pattern keeps the catalog clean while storing all personal tracking state in the association table.

## Design notes

The current implementation is intentionally simple and domain-focused. It supports the project's minimum viable media-tracking workflow without introducing more advanced concepts such as custom lists, chapter-level tracking, review moderation, or AI recommendations. Those features can be layered on top of this structure later.
