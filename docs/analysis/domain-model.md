# Domain Model

> **Note:** this document is the record of the first slice of the code: users, titles and the library. It is no longer the full picture. The code now has more tables, and `media_items` has more columns than shown here (`description` and `last_synced`). The current model for all six epics is in [data/domain-model.md](data/domain-model.md).

This document summarizes the first slice of the domain model of OmniLog. The scope is limited to the entities that existed at that time and the relationships needed to support media tracking and personal library management.

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
- When a title with an external ID is added to a user's library and its details have not been synced yet, its description and genres are automatically fetched and saved (issue #125).

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
- Adding a catalog title to the library ensures its genres and description are populated from external sources (Option 1 for issue #125) so that statistics (US-15) and recommendations (US-13) have complete data. Failure of external services does not block library addition (NFR-04).

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

This first slice was intentionally simple. It supported the minimum media-tracking workflow without custom lists, chapter-level tracking, review moderation or recommendations. Those features were layered on top of this structure later and are described in [data/domain-model.md](data/domain-model.md).
