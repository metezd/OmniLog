# OmniLog - Requirements Definition (User Stories)

Requirements are written in **user story** format with **Given / When / Then** acceptance criteria (BDD style). They are derived from the six epics in the Project Charter. Each story has at least one functional test in `tests/requirements/`, and the non-functional requirements (NFR) have their own test cases.

**Priority** uses MoSCoW: Must, Should, Could.

Roles: **Visitor** (not logged in), **User** (logged in), **Developer/Operator** (maintains the system).

---

## Epic 1 - Backend Infrastructure and Database Foundation

### US-01 Service health check
**As a** developer/operator, **I want** a health endpoint, **so that** I can verify that the backend service is running after a deployment.
**Priority:** Must

Acceptance criteria:
- Given the backend is running, when I send `GET /health`, then I receive status 200 and the body `{"status": "healthy"}`.

**Status:** already implemented in `backend/app/main.py`.

---

## Epic 2 - User Management and Social Journal

### US-02 Register an account
**As a** visitor, **I want** to register with a username, email and password, **so that** I can keep my own media library.
**Priority:** Must

Acceptance criteria:
- Given valid username, email and password, when I `POST /auth/register`, then an account is created (status 201) and the response does not contain the password or its hash.
- Given an email or username that already exists, when I register, then I receive status 409.
- Given an invalid email format or an empty username, when I register, then I receive status 422.

### US-03 Log in
**As a** registered user, **I want** to log in with my credentials, **so that** I can access my private data.
**Priority:** Must

Acceptance criteria:
- Given correct credentials, when I `POST /auth/login`, then I receive status 200 and a JWT access token.
- Given a wrong password, when I log in, then I receive status 401 and no token.

### US-04 Add a title to my library with a status
**As a** user, **I want** to add a game or series to my library and set a status (plan to watch/play, in progress, completed, dropped), **so that** I can track what I consume.
**Priority:** Must

Acceptance criteria:
- Given I am logged in and the title exists, when I `POST /library` with `media_item_id` and `status`, then the entry is created (status 201) and appears in `GET /library`.
- Given the title is already in my library, when I add it again, then I receive status 409.
- Given I am not logged in, when I call `POST /library`, then I receive status 401.

### US-05 Rate a title and update its status
**As a** user, **I want** to give a title a rating from 1 to 10 and change its status later, **so that** my library reflects my opinion and progress.
**Priority:** Must

Acceptance criteria:
- Given a library entry of mine, when I `PATCH /library/{id}` with `rating` 8, then the entry is updated and returns rating 8.
- Given a rating of 0 or 11, when I update an entry, then I receive status 422 and the entry is unchanged.
- Given a library entry that belongs to another user, when I try to update it, then I receive status 404 or 403.

### US-06 Create custom lists
**As a** user, **I want** to create custom lists (for example "Best narrative games") and add titles to them, **so that** I can organise my media my own way.
**Priority:** Should

Acceptance criteria:
- Given I am logged in, when I `POST /lists` with a name, then the list is created (status 201).
- Given an existing list and a title, when I `POST /lists/{id}/items` with `media_item_id`, then the title appears in the list.
- Given an empty list name, when I create a list, then I receive status 422.
- Given I already have a list with the same name, when I create a list, then I receive status 409.

### US-07 View my activity diary
**As a** user, **I want** to see a chronological diary of my recent actions (added, rated, completed), **so that** I can look back at my media history.
**Priority:** Should

Acceptance criteria:
- Given I added and rated a title, when I `GET /diary`, then both events are returned, newest first.
- Given I am a new user with no activity, when I `GET /diary`, then I receive an empty list with status 200.

---

## Epic 3 - Multi-Media Aggregation and Cataloging

### US-08 Search the catalog
**As a** user, **I want** to search games and TV series by title, **so that** I can find a title to add without typing its details.
**Priority:** Must

Acceptance criteria:
- Given the title "Life is Strange" exists in IGDB, when I `GET /catalog/search?q=Life is Strange&type=GAME`, then the results include it with title, poster URL and release date.
- Given a query that matches nothing, when I search, then I receive an empty list with status 200.
- Given a repeated identical search, when the result is already cached, then it is returned without calling the external API again.

### US-09 View title details with seasons and chapters
**As a** user, **I want** to open a title and see its metadata, artwork and its seasons, episodes or chapters, **so that** I can track progress at a fine level.
**Priority:** Must

Acceptance criteria:
- Given a series with seasons, when I `GET /catalog/{id}`, then the response includes its seasons and episodes.
- Given an episodic game, when I `GET /catalog/{id}`, then the response includes its chapters.
- Given an unknown id, when I request it, then I receive status 404.
- Given a series whose seasons are already loaded, when I open it again, then the answer comes without a new call to TMDB.
- Given TMDB is not available and the series was never loaded, when I open it, then I receive status 503.

---

## Epic 4 - Granular Episodic and Decision Logging

### US-10 Rate an individual chapter or episode
**As a** user, **I want** to give each chapter or episode a 1 to 5 star rating, **so that** I can compare the parts of a story.
**Priority:** Must

Acceptance criteria:
- Given a chapter in a title of my library, when I `PUT /library/{id}/chapters/{chapter_id}/rating` with 4, then the rating is saved.
- Given a rating of 6 or 0, when I submit it, then I receive status 422.

### US-11 Log playtime per chapter
**As a** user, **I want** to log the time I spent on a chapter, **so that** I can see how long each part took me.
**Priority:** Should

Acceptance criteria:
- Given a chapter, when I `POST` a playtime of 90 minutes and later another 30, then the chapter total is 120 minutes.
- Given a negative playtime, when I submit it, then I receive status 422.

### US-12 Record branching decisions
**As a** player of an episodic narrative game, **I want** to record the choice I made at a decision point, **so that** I can compare my path with other players.
**Priority:** Should

Acceptance criteria:
- Given a chapter with a decision point and options A and B, when I record option A, then my choice is stored and returned on the chapter.
- Given a choice that is not one of the allowed options, when I record it, then I receive status 422.
- Given I changed my mind, when I record option B, then only the latest choice is kept.

---

## Epic 5 - AI-Powered Cross-Media Engine and Review Moderation

### US-13 Cross-media recommendations
**As a** user, **I want** recommendations of TV series based on games I played (and the other way around), **so that** I can discover media across formats.
**Priority:** Should

Acceptance criteria:
- Given I completed at least one game, when I `GET /recommendations?target=SERIES`, then I receive a non-empty list of series, none already in my library.
- Given my library is empty, when I request recommendations, then I receive an empty list or generic popular titles with status 200.

### US-14 Spoiler detection in reviews
**As a** user, **I want** reviews that contain spoilers to be flagged automatically, **so that** I am not spoiled when reading other reviews.
**Priority:** Could

Acceptance criteria:
- Given a review text that reveals a major plot event, when it is submitted, then it is stored with `contains_spoiler = true`.
- Given a review without plot details, when it is submitted, then it is stored with `contains_spoiler = false`.

---

## Epic 6 - Analytics Dashboard

### US-15 View personal statistics
**As a** user, **I want** to see statistics about my library (genre breakdown, rating distribution, playtime, game vs. series ratio), **so that** I understand my consumption habits.
**Priority:** Should

Acceptance criteria:
- Given a library with 3 games and 1 series, when I `GET /stats`, then the media split shows 75% games and 25% series.
- Given ratings of 8, 8 and 6, when I `GET /stats`, then the rating distribution shows 2 entries for 8 and 1 for 6.
- Given an empty library, when I `GET /stats`, then all counts are zero and the status is 200.

---

## Non-Functional Requirements

| ID | Category | Requirement | Measurable criterion |
|---|---|---|---|
| NFR-01 | Performance | Cached catalog searches are fast. | 95th percentile response time under 500 ms over 100 repeated requests |
| NFR-02 | Security | Protected endpoints require authentication. | Requests to `/library`, `/lists`, `/diary`, `/stats` without a valid token return 401 |
| NFR-03 | Security | Passwords are never stored or returned in plain text. | Stored password differs from the plain text, and no API response contains `password` or `hashed_password` |
| NFR-04 | Reliability | The API survives external API failures. | When IGDB/TMDB is unavailable, catalog endpoints return cached data or a clear 503, never an unhandled 500 |
| NFR-05 | Maintainability | Backend code is covered by automated tests. | Line coverage of at least 70% measured with `pytest-cov` (checked in the Testing phase) |

---

## Traceability: stories to tests

| Story | Epic | Priority | Planned test file | Test function |
|---|---|---|---|---|
| US-01 | 1 | Must | `test_epic1_infrastructure.py` | `test_us01_health_returns_ok` |
| US-02 | 2 | Must | `test_epic2_users.py` | `test_us02_register_user` |
| US-03 | 2 | Must | `test_epic2_users.py` | `test_us03_login_returns_token` |
| US-04 | 2 | Must | `test_epic2_users.py` | `test_us04_add_to_library` |
| US-05 | 2 | Must | `test_epic2_users.py` | `test_us05_rate_and_update_status` |
| US-06 | 2 | Should | `test_epic2_users.py` | `test_us06_create_custom_list` |
| US-07 | 2 | Should | `test_epic2_users.py` | `test_us07_activity_diary` |
| US-08 | 3 | Must | `test_epic3_catalog.py` | `test_us08_search_catalog` |
| US-09 | 3 | Must | `test_epic3_catalog.py` | `test_us09_title_details_with_chapters` |
| US-10 | 4 | Must | `test_epic4_episodic.py` | `test_us10_rate_chapter` |
| US-11 | 4 | Should | `test_epic4_episodic.py` | `test_us11_log_playtime` |
| US-12 | 4 | Should | `test_epic4_episodic.py` | `test_us12_record_decision` |
| US-13 | 5 | Should | `test_epic5_ai.py` | `test_us13_cross_media_recommendations` |
| US-14 | 5 | Could | `test_epic5_ai.py` | `test_us14_spoiler_detection` |
| US-15 | 6 | Should | `test_epic6_analytics.py` | `test_us15_personal_statistics` |
| NFR-01 to NFR-04 | - | - | `test_nfr.py` | `test_nfr01_...` to `test_nfr04_...` |
| NFR-05 | - | - | measured in the Testing phase | `pytest --cov` |
