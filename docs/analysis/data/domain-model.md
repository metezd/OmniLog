# Domain Model: OmniLog

This document describes the full domain model of OmniLog. It covers all six epics of the Project Charter. It replaces the earlier draft that only covered the API integration entities.

The final model is approved by the Product Owner (Mete Özdoğan). Section 8 lists the open points and how each one was answered. This document was checked against the code on 19.11.2026. Parts of the model that are in the design only are marked **not built**.

Related documents:
- [er-diagram.md](er-diagram.md) has the E-R diagrams, the data dictionary and the embedding review.
- [../domain-model.md](../domain-model.md) and [../er.md](../er.md) describe the first slice of the code (users, titles and the library). They are kept as a record and this document is the current model.
- [traceability.md](traceability.md) links requirements to entities and data flows.

## 1. Scope

The model supports these functions:
- accounts and login (Epic 2)
- a personal library with status and rating (Epic 2)
- custom lists and an activity diary (Epic 2)
- a shared catalog filled from IGDB and TMDB, with seasons and chapters (Epic 3)
- chapter ratings, playtime and branching decisions (Epic 4)
- recommendations and review spoiler detection (Epic 5). The recommendations use the genres of the library. Embeddings are not built
- personal statistics (Epic 6)

Statistics (Epic 6) need no tables of their own. They are computed from the other entities.

## 2. Entity overview

| # | Entity | Table | Epic | Status |
|---|---|---|---|---|
| 1 | User | `users` | 2 | Implemented. The field `is_admin` is not built |
| 2 | MediaItem | `media_items` | 3 | Implemented. `source_id`, `external_id`, `normalized_payload`, `created_at` and `updated_at` are not built |
| 3 | UserLibrary | `user_libraries` | 2 | Implemented |
| 4 | CustomList | `custom_lists` | 2 | Implemented |
| 5 | CustomListItem | `custom_list_items` | 2 | Implemented |
| 6 | DiaryEntry (earlier called ActivityEvent) | `diary_entries` | 2 | Implemented |
| 7 | ExternalSource | `external_sources` | 3 | Not built |
| 8 | Genre | `genres`, `media_item_genres` | 3 | Implemented (migration 0010) |
| 9 | Season | `seasons` | 3 | Implemented (US-09) |
| 10 | Chapter | `chapters` | 3 and 4 | Implemented (US-09) |
| 11 | SyncJobLog | `sync_job_logs` | 3 | Not built |
| 12 | ChapterProgress | `chapter_progress` | 4 | Implemented (US-10) |
| 13 | PlaytimeLog | `playtime_logs` | 4 | Implemented (US-11) |
| 14 | DecisionPoint and DecisionOption | `decision_points`, `decision_options` | 4 | Implemented (US-12, migration 0008) |
| 15 | UserDecision | `user_decisions` | 4 | Implemented (US-12, migration 0008) |
| 16 | Review | `reviews` | 5 | Implemented (US-14, migration 0011) |
| 17 | MediaEmbedding | `media_embeddings` | 5 | Not built |
| 18 | UserTasteVector | `user_taste_vectors` | 5 | Not built (optional) |
| 19 | CacheEntry | Redis keys, no table | 3 and 6 | Implemented for search, title details and statistics. The recommendation key is not built |

## 3. Entity descriptions

### 3.1 User
A person with an account. The user owns a library, lists, an activity diary, progress records and reviews.
- Key fields: `id`, `username`, `email`, `hashed_password`, `created_at`.
- Not built: the field `is_admin` of the design. It would let the Operator start a manual sync (UC-EP3-03). The manual sync is a command (`python -m app.sync`) that needs no role. There is no Operator role in the code.
- Rules: username and email are unique. The password is only stored as a hash. A username never contains `@` (BR-18), so a login value with `@` can only be an email.

### 3.2 MediaItem
One title in the shared catalog. It can be a game, a series or a movie.
- Key fields: `id`, `title`, `media_type`, `poster_url`, `release_date`, `description`, `external_api_id`, `last_synced`.
- `description` (migration 0010) is loaded when the details of a title are opened. The design planned it for the embedding text.
- `last_synced` is set when the details, genres and seasons of a title are loaded. This happens when the details are opened (US-09). A search result alone does not set it, and adding a title to the library does not set it either. While the outside service is down, a title with a `last_synced` value is answered from the saved copy.
- `external_api_id` (an integer) with `media_type` identifies the title at IGDB or TMDB. The design planned `source_id`, `external_id`, `normalized_payload`, `created_at` and `updated_at` instead. They are not built.
- Rules: `title` and `media_type` are required. The pair (`media_type`, `external_api_id`) is unique.

### 3.3 UserLibrary
The link between a user and a media item. It holds the personal state.
- Key fields: `id`, `user_id`, `media_item_id`, `status`, `rating`, `updated_at`.
- Rules: one row per user and media item. The rating is from 1 to 10. The default status is `PLAN_TO_WATCH`.

### 3.4 CustomList and CustomListItem
A named list that a user builds, for example "Best narrative games". The item table links a list to media items.
- Rules: the list name is not empty (1 to 200 characters) and is unique for one user. A media item can appear only once in a list. A list can be deleted with its items, and an item can be taken out of a list. Both add a diary event.

### 3.5 DiaryEntry (earlier called ActivityEvent)
One entry of the activity diary. It records an action of the user. The table is `diary_entries`, with the columns `action` and `details` (a short text) in place of the planned `event_type` and `payload`.
- Event types (the values of `action`): `LIBRARY_ADDED`, `STATUS_CHANGED`, `RATED`, `CHAPTER_RATED`, `PLAYTIME_LOGGED`, `DECISION_RECORDED`, `LIST_CREATED`, `LIST_ITEM_ADDED`, `LIBRARY_REMOVED`, `LIST_ITEM_REMOVED`, `LIST_DELETED`, `REVIEW_POSTED`.
- Rules: events are only appended. They are never edited or deleted. A removal is a new event and the older events about the same title stay. The diary shows them newest first. The table has an index on `(user_id, created_at DESC)` for this list and one on `media_item_id` for the delete cascade of a title (migration 0013). The diary is read in pages with `limit` and `offset` (default 100, at most 500).

### 3.6 ExternalSource (not built)
An outside data provider. The values are `IGDB` and `TMDB`.
- Key fields: `name`, `base_url`, `auth_meta`, `rate_limit_meta`.
- Rule: the real API keys are never stored in this table. They stay in environment variables or a secret manager. The code reads the keys from the environment (`IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET`, `TMDB_API_KEY`) and has no table for sources.

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
- Rules: an option must belong to the decision point. A user has one decision per decision point. A new choice replaces the old one. The request names the decision point with the optional `decision_point_id`. A chapter with exactly one decision point needs no id, and a chapter with several is refused until the request names one. The decisions of games come from the seed file (see section 8, point 3).

### 3.11 Review
The written review of a user for a library entry.
- Key fields: `text`, `contains_spoiler`, `spoiler_score`, `spoiler_model_version`.
- Rules: `contains_spoiler` is set by the spoiler classifier. The column allows NULL: NULL means "not checked" (OpenAI failed). A library entry has one review, and posting again replaces it (`updated_at` is then set). The classifier is OpenAI (model `SPOILER_MODEL`) when `OPENAI_API_KEY` is set. Without a key, a list of local patterns is used. When OpenAI does not answer, the review is still saved and the three spoiler fields stay NULL.

### 3.12 MediaEmbedding and UserTasteVector (not built)
These two entities are in the design only. There are no tables, no models and no migrations. The OpenAI client has a function that asks for embeddings, but nothing calls it. The recommendations (US-13) rank the titles that the user does not own by the genres of the library, weighted by the ratings. The text below is the design.

`MediaEmbedding` stores one vector for each media item and embedding model. The vector is built from the title, genres and description. All media types share the same vector space. This is what makes cross-media recommendations possible.

`UserTasteVector` is an optional cache of the average vector of a user's liked titles. It can also be computed on demand.

### 3.13 SyncJobLog (not built)
The history of catalog sync jobs. One row for each run.
- Key fields: `external_source_id`, `job_name`, `trigger`, `started_at`, `finished_at`, `status`, `records_processed`, `error_text`.

### 3.14 CacheEntry (Redis only)
Cached responses with a time to live. It is not a table in the relational database. The key patterns are in [er-diagram.md](er-diagram.md), section 7. If Redis is down, an in-process cache takes its place.

## 4. Relationships

| From | To | Cardinality | Meaning |
|---|---|---|---|
| User | UserLibrary | 1 to N | A user has many library entries |
| MediaItem | UserLibrary | 1 to N | A title is in many libraries |
| User | CustomList | 1 to N | A user owns many lists |
| CustomList | CustomListItem | 1 to N | A list has many items |
| MediaItem | CustomListItem | 1 to N | A title can be in many lists |
| User | DiaryEntry | 1 to N | A user has many diary events |
| MediaItem | DiaryEntry | 1 to N (optional) | An event can refer to a title |
| ExternalSource | MediaItem | 1 to N | Not built. A source provides many titles |
| ExternalSource | SyncJobLog | 1 to N | Not built. A source has many sync runs |
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
| MediaItem | MediaEmbedding | 1 to N | Not built. One vector for each embedding model |
| User | UserTasteVector | 1 to 1 | Not built. One cached profile vector |

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
| BR-08 | The pair (media type, external id) identifies one catalog record. The design planned (source, external id). | US-08, US-09 |
| BR-09 | Outside data is fresh while it is in the Redis cache (`DETAILS_CACHE_TTL_SECONDS`, default 24 hours). When the cache is empty the outside service is called. If that fails, a saved copy (`last_synced` is set) is returned, even when it is old. The design planned a check of `now - last_synced` against a TTL. That check is not built. | US-08, US-09 |
| BR-10 | The chapter rating is a whole number from 1 to 5. | US-10 |
| BR-11 | A chapter must belong to the title of the library entry. | US-10 to US-12 |
| BR-12 | A playtime entry is at least 1 minute. The total is the sum of entries. | US-11 |
| BR-13 | The chosen option must belong to the decision point. Only the latest choice is kept. | US-12 |
| BR-14 | Recommendations match the target type when one is given and never include titles already in the library. | US-13 |
| BR-15 | A review is stored with a spoiler flag set by the classifier. | US-14 |
| BR-16 | The statistics only use the data of the logged-in user. | US-15 |
| BR-17 | Deleting a user deletes their library, lists, diary, progress and reviews. The database does this with cascading foreign keys. No endpoint deletes a user. | NFR-03 |
| BR-18 | A username never contains `@`, so a login value with `@` is an email. The database checks it (`chk_username_no_at`, migration 0009). | US-02, US-03 |
| BR-19 | Not built. Adding a title with an external ID to the library would load its details and genres if not already synced. | US-04, US-09, US-15 |

## 6. Normalization notes

- The sources use different names for the same thing. For example, one source says `game` and another says `video_game`. The normalize step must create one canonical `media_type`.
- Dates, image URLs and genre names are also normalized.
- The catalog (`media_items`) is shared. Everything personal is stored in other tables. This keeps the catalog clean.
- Genres are stored in their own table. This makes the genre breakdown of Epic 6 a simple query.

## 7. Changes compared with earlier documents

| Topic | Earlier version | Now | Reason |
|---|---|---|---|
| Media primary key | UUID in the draft domain model | Integer | The code and the tests use integer ids |
| External id | `external_api_id` (integer) in code | The design has `source_id` plus `external_id` (text). The code kept `external_api_id` and made it unique together with `media_type` | One id alone cannot tell IGDB from TMDB. The media type does the same job for the three types |
| Type field | `type` | `media_type` | Same name as in the code |
| Genres | `genres` array in `media` | `genres` table and a link table | Easier statistics |
| Sync log link | `sync_job_log` linked to media | Linked to `external_sources` | A sync job works on a source, not on one title |
| Cache | `CacheEntry` as a table with a media link | Redis keys only | Redis holds the cache. No table is needed |
| Diary | `activity_events` with `event_type` and a JSON `payload` | `diary_entries` with `action` and a short text `details` | The code only needs a line of text for each event |

## 8. Open points for approval

Each point was checked against the code on 19.11.2026.

| # | Question | Answer |
|---|---|---|
| 1 | Database | **Answered: PostgreSQL.** The models, the migrations and the tests are written for PostgreSQL, the Compose files start a PostgreSQL image, and the decision code uses `ON CONFLICT`, which is PostgreSQL syntax. JSONB and pgvector are not used yet. The leftover SQLite fallback of `backend/app/core/database.py` was removed in #371. |
| 2 | Rating scales | **Answered and built.** Library 1 to 10, chapters and episodes 1 to 5 (BR-04 and BR-10). |
| 3 | Chapter and decision point data for games | **Answered and built as a seed file:** `backend/app/seed/game_chapters.json`, loaded with `python -m app.seed`. The shipped file holds Life is Strange (IGDB id 7599) with 5 chapters and 6 decision points. Operator endpoints are not built and would need `is_admin` (point 6). |
| 4 | Decision points per chapter | **Answered and built.** The request has an optional `decision_point_id`. It can be left out for a chapter with one decision point and is required when the chapter has several. |
| 5 | Reviews per library entry | **Answered and built.** One review for each entry, and posting again replaces the old one. |
| 6 | Admin role | **Not built.** There is no `is_admin` column, no Operator role and no admin endpoint. |
| 7 | Genres and descriptions for unopened titles (#125) | **Answered and built.** Details load when the details of a title are opened (`GET /catalog/{id}`) and when a title is added to the library (`ensure_title_details` in `catalog_service.py`, called by `library_service`). A failure of the outside service is logged and never blocks the addition (NFR-04). The manual sync (`python -m app.sync`, UC-EP3-03) loads the details of titles that were never opened or added, using `sync_titles`. |
| 8 | Embeddings and vector tables | **Not built.** `media_embeddings` and `user_taste_vectors` have no tables. The recommendations rank by genre. The model (`text-embedding-3-small`, 1536) is only a setting. |
