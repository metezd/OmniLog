# Domain Model: OmniLog

This document describes the full domain model of OmniLog. It covers all six epics of the Project Charter. It replaces the earlier draft that only covered the API integration entities.

The final model is approved by the Product Owner (Mete Özdoğan). Open points that need his decision are listed in section 8.

Related documents:
- [er-diagram.md](er-diagram.md) has the E-R diagrams, the data dictionary and the embedding review.
- [../domain-model.md](../domain-model.md) and [../er.md](../er.md) describe the baseline that is already implemented in `backend/app/models/entities.py`.
- [traceability.md](traceability.md) links requirements to entities and data flows.

## 1. Scope

The model supports these functions:
- accounts and login (Epic 2)
- a personal library with status and rating (Epic 2)
- custom lists and an activity diary (Epic 2)
- a shared catalog filled from IGDB and TMDB, with seasons and chapters (Epic 3)
- chapter ratings, playtime and branching decisions (Epic 4)
- embeddings, recommendations and review spoiler detection (Epic 5)
- personal statistics (Epic 6)

Statistics (Epic 6) need no tables of their own. They are computed from the other entities.

## 2. Entity overview

| # | Entity | Table | Epic | Status |
|---|---|---|---|---|
| 1 | User | `users` | 2 | Implemented (one column proposed) |
| 2 | MediaItem | `media_items` | 3 | Implemented (columns proposed) |
| 3 | UserLibrary | `user_libraries` | 2 | Implemented |
| 4 | CustomList | `custom_lists` | 2 | Proposed |
| 5 | CustomListItem | `custom_list_items` | 2 | Proposed |
| 6 | ActivityEvent | `activity_events` | 2 | Proposed |
| 7 | ExternalSource | `external_sources` | 3 | Proposed |
| 8 | Genre | `genres`, `media_item_genres` | 3 | Implemented (migration 0010) |
| 9 | Season | `seasons` | 3 | Implemented (US-09) |
| 10 | Chapter | `chapters` | 3 and 4 | Implemented (US-09) |
| 11 | SyncJobLog | `sync_job_logs` | 3 | Proposed |
| 12 | ChapterProgress | `chapter_progress` | 4 | Implemented (US-10) |
| 13 | PlaytimeLog | `playtime_logs` | 4 | Implemented (US-11) |
| 14 | DecisionPoint and DecisionOption | `decision_points`, `decision_options` | 4 | Proposed |
| 15 | UserDecision | `user_decisions` | 4 | Proposed |
| 16 | Review | `reviews` | 5 | Proposed |
| 17 | MediaEmbedding | `media_embeddings` | 5 | Proposed |
| 18 | UserTasteVector | `user_taste_vectors` | 5 | Proposed and optional |
| 19 | CacheEntry | Redis keys, no table | 3, 5 and 6 | Proposed |

## 3. Entity descriptions

### 3.1 User
A person with an account. The user owns a library, lists, an activity diary, progress records and reviews.
- Key fields: `id`, `username`, `email`, `hashed_password`, `created_at`.
- Proposed new field: `is_admin`. It lets the Operator start a manual sync (UC-EP3-03).
- Rules: username and email are unique. The password is only stored as a hash.

### 3.2 MediaItem
One title in the shared catalog. It can be a game, a series or a movie.
- Key fields: `id`, `title`, `media_type`, `poster_url`, `release_date`.
- Proposed new fields: `description`, `source_id`, `external_id`, `normalized_payload`, `last_synced`, `created_at`, `updated_at`. `last_synced` is implemented (US-09). It is empty until the seasons of a series are loaded, so a search result alone does not set it.
- `description` is needed because the embedding text is built from it.
- `source_id` and `external_id` replace the implemented column `external_api_id`.
- Rules: `title` and `media_type` are required. The pair (`source_id`, `external_id`) is unique when both are present.

### 3.3 UserLibrary
The link between a user and a media item. It holds the personal state.
- Key fields: `id`, `user_id`, `media_item_id`, `status`, `rating`, `updated_at`.
- Rules: one row per user and media item. The rating is from 1 to 10. The default status is `PLAN_TO_WATCH`.

### 3.4 CustomList and CustomListItem
A named list that a user builds, for example "Best narrative games". The item table links a list to media items.
- Rules: the list name is not empty and is unique for one user. A media item can appear only once in a list.

### 3.5 ActivityEvent
One entry of the activity diary. It records an action of the user.
- Event types: `LIBRARY_ADDED`, `STATUS_CHANGED`, `RATED`, `CHAPTER_RATED`, `PLAYTIME_LOGGED`, `DECISION_RECORDED`, `LIST_CREATED`, `LIST_ITEM_ADDED`, `LIBRARY_REMOVED`, `LIST_ITEM_REMOVED`, `LIST_DELETED`, `REVIEW_POSTED`.
- Rules: events are only appended. They are never edited or deleted. A removal is a new event and the older events about the same title stay. The diary shows them newest first.

### 3.6 ExternalSource
An outside data provider. The values are `IGDB` and `TMDB`.
- Key fields: `name`, `base_url`, `auth_meta`, `rate_limit_meta`.
- Rule: the real API keys are never stored in this table. They stay in environment variables or a secret manager.

### 3.7 Genre
A canonical genre name. A media item has many genres and a genre belongs to many media items.
- Rule: the genre names from IGDB and TMDB are normalized to one canonical name. Implemented as a short list of rules (`backend/app/integrations/genres.py`): the joined names of TMDB such as "Action & Adventure" are split into plain names, and every other name stays as the source wrote it.

### 3.8 Season and Chapter
A series has seasons. A season has episodes. An episodic game has chapters.
- `Chapter` has a `kind` field with the value `EPISODE` or `CHAPTER`.
- An episode points to a season. A game chapter has no season.
- Rule: the number is unique inside its season (or inside its game when there is no season).

### 3.9 ChapterProgress and PlaytimeLog
The personal record of one user for one chapter.
- `ChapterProgress` holds the chapter rating (1 to 5) and the playtime total in minutes.
- `PlaytimeLog` holds each single playtime entry. The total is the sum of the entries.
- Rules: one progress row per library entry and chapter. Each logged playtime is at least 1 minute.

### 3.10 DecisionPoint, DecisionOption and UserDecision
A decision point is a branching moment inside a chapter. It has two or more options such as A and B. The user decision stores which option the user chose.
- Rules: an option must belong to the decision point. A user has one decision per decision point. A new choice replaces the old one.

### 3.11 Review
The written review of a user for a library entry.
- Key fields: `text`, `contains_spoiler`, `spoiler_score`, `spoiler_model_version`.
- Rule: `contains_spoiler` is set by the spoiler classifier. It is empty (NULL) when the classifier has not run yet.

### 3.12 MediaEmbedding and UserTasteVector
`MediaEmbedding` stores one vector for each media item and embedding model. The vector is built from the title, genres and description. All media types share the same vector space. This is what makes cross-media recommendations possible.

`UserTasteVector` is an optional cache of the average vector of a user's liked titles. It can also be computed on demand.

### 3.13 SyncJobLog
The history of catalog sync jobs. One row for each run.
- Key fields: `external_source_id`, `job_name`, `trigger`, `started_at`, `finished_at`, `status`, `records_processed`, `error_text`.

### 3.14 CacheEntry (Redis only)
Cached responses with a time to live. It is not a table in the relational database. The key patterns are in [er-diagram.md](er-diagram.md), section 7.

## 4. Relationships

| From | To | Cardinality | Meaning |
|---|---|---|---|
| User | UserLibrary | 1 to N | A user has many library entries |
| MediaItem | UserLibrary | 1 to N | A title is in many libraries |
| User | CustomList | 1 to N | A user owns many lists |
| CustomList | CustomListItem | 1 to N | A list has many items |
| MediaItem | CustomListItem | 1 to N | A title can be in many lists |
| User | ActivityEvent | 1 to N | A user has many diary events |
| MediaItem | ActivityEvent | 1 to N (optional) | An event can refer to a title |
| ExternalSource | MediaItem | 1 to N | A source provides many titles |
| ExternalSource | SyncJobLog | 1 to N | A source has many sync runs |
| MediaItem | Genre | N to N | Through `media_item_genres` |
| MediaItem | Season | 1 to N | A series has seasons |
| Season | Chapter | 1 to N | A season has episodes |
| MediaItem | Chapter | 1 to N | An episodic game has chapters |
| UserLibrary | ChapterProgress | 1 to N | One progress row per chapter |
| Chapter | ChapterProgress | 1 to N | A chapter has progress from many users |
| ChapterProgress | PlaytimeLog | 1 to N | A progress row has many playtime entries |
| Chapter | DecisionPoint | 1 to N | A chapter has decision points |
| DecisionPoint | DecisionOption | 1 to N | A decision point has options |
| UserLibrary | UserDecision | 1 to N | A library entry has many decisions |
| DecisionPoint | UserDecision | 1 to N | A decision point has many user choices |
| UserLibrary | Review | 1 to 1 | One review for each library entry |
| MediaItem | MediaEmbedding | 1 to N | One vector for each embedding model |
| User | UserTasteVector | 1 to 1 | One cached profile vector |

## 5. Business rules

| ID | Rule | Story |
|---|---|---|
| BR-01 | Username and email are unique. | US-02 |
| BR-02 | The password is stored as a hash and never returned. | US-02, NFR-03 |
| BR-03 | A user has at most one library entry for a title. | US-04 |
| BR-04 | The library rating is from 1 to 10. | US-05 |
| BR-05 | A user can only read and change their own data. | US-05, NFR-02 |
| BR-06 | A list name is not empty and is unique per user. A title appears once in a list. | US-06 |
| BR-07 | Every library change, rating and status change creates a diary event. | US-07 |
| BR-08 | The pair (source, external id) identifies one catalog record. | US-08, US-09 |
| BR-09 | A record is stale when `now - last_synced` is longer than the TTL. | US-08, US-09 |
| BR-10 | The chapter rating is a whole number from 1 to 5. | US-10 |
| BR-11 | A chapter must belong to the title of the library entry. | US-10 to US-12 |
| BR-12 | A playtime entry is at least 1 minute. The total is the sum of entries. | US-11 |
| BR-13 | The chosen option must belong to the decision point. Only the latest choice is kept. | US-12 |
| BR-14 | Recommendations match the target type and never include titles already in the library. | US-13 |
| BR-15 | A review is stored with a spoiler flag set by the classifier. | US-14 |
| BR-16 | The statistics only use the data of the logged-in user. | US-15 |
| BR-17 | Deleting a user deletes their library, lists, diary, progress and reviews. | NFR-03 |

## 6. Normalization notes

- The sources use different names for the same thing. For example, one source says `game` and another says `video_game`. The normalize step must create one canonical `media_type`.
- Dates, image URLs and genre names are also normalized.
- The catalog (`media_items`) is shared. Everything personal is stored in other tables. This keeps the catalog clean.
- Genres are stored in their own table. This makes the genre breakdown of Epic 6 a simple query.

## 7. Changes compared with earlier documents

| Topic | Earlier version | Now | Reason |
|---|---|---|---|
| Media primary key | UUID in the draft domain model | Integer | The code and the tests use integer ids |
| External id | `external_api_id` (integer) in code | `source_id` plus `external_id` (text) | One id alone cannot tell IGDB from TMDB |
| Type field | `type` | `media_type` | Same name as in the code |
| Genres | `genres` array in `media` | `genres` table and a link table | Easier statistics |
| Sync log link | `sync_job_log` linked to media | Linked to `external_sources` | A sync job works on a source, not on one title |
| Cache | `CacheEntry` as a table with a media link | Redis keys only | Redis holds the cache. No table is needed |

## 8. Open points for approval

| # | Question | Proposal |
|---|---|---|
| 1 | Database | PostgreSQL is needed for JSONB and pgvector. The code uses SQLite now. Decide in the design phase. |
| 2 | Rating scales | Keep 1 to 10 for the library and 1 to 5 for chapters. This is the current open issue in the requirement specification. |
| 3 | Chapter and decision point data for games | IGDB does not give a standard chapter list, and no source gives decision points and options. They may need to be added by hand (for example by the Operator or a seed file). **Implemented as a seed file:** `backend/app/seed/game_chapters.json`, loaded with `python -m app.seed`. Operator endpoints are not built and would need `is_admin` (point 6). |
| 4 | Decision points per chapter | The model allows many. The API in the tests assumes one. Add an optional `decision_point_id` to the request. |
| 5 | Reviews per library entry | One review for each entry. Posting again replaces the old review. |
| 6 | Admin role | Add `is_admin` to `users`. |
