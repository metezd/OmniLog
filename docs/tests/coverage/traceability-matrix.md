# Traceability Matrix and Coverage Summary

**Project:** OmniLog | **Course:** CMPE 331 | **Branch:** `test_work` | **Run date:** 19.11.2026

This file shows which tests cover which requirements, how many of the requirements and acceptance criteria are covered, and how much of the code is covered. It is generated from the real test run (`raw/backend-junit.xml`, `raw/backend-coverage.json`). The raw outputs of the run are in [`raw/`](raw/). The interpretation of the numbers is in [`coverage-report.md`](coverage-report.md).

## 1. Requirement coverage

- **Requirements with at least one passing test:** 19 of 19 user stories and NFRs that have a test (NFR-05 is checked by the coverage run itself, see below). With NFR-05, all **20 of 20** requirements are covered.
- **Acceptance criteria with a passing test:** 40 of 40 (section 3).
- **Test cases in the backend run:** 756 (753 passed, 0 failed, 3 skipped). One test function can run several times with different parameters, so the number of test cases is larger than the number of functions.
- **Code coverage of `backend/app`:** 91.3 % of statements and 78.3 % of branches (requirement NFR-05: at least 70 %, so it is met).

| Req | Epic | Priority | Requirement | Test cases | Passed | Skipped | Test files | Statement coverage of its code | Result |
|---|---|---|---|---:|---:|---:|---|---:|---|
| US-01 | 1 | Must | Service health check | 11 | 11 | 0 | `test_epic1_infrastructure.py`, `test_health.py` | 100.0 % | Covered |
| US-02 | 2 | Must | Register an account | 44 | 44 | 0 | `test_epic2_auth_edge_cases.py`, `test_epic2_login_identifier_edge_cases.py`, `test_epic2_users.py` | 100.0 % | Covered |
| US-03 | 2 | Must | Log in | 48 | 48 | 0 | `test_epic2_auth_edge_cases.py`, `test_epic2_login_identifier_edge_cases.py`, `test_epic2_token_lifetime.py`, `test_epic2_users.py`, `test_security_tokens.py` | 100.0 % | Covered |
| US-04 | 2 | Must | Add a title to my library | 49 | 49 | 0 | `test_epic2_removal.py`, `test_epic2_users.py`, `test_epic3_library_edge_cases.py` | 100.0 % | Covered |
| US-05 | 2 | Must | Rate a title, update its status | 17 | 17 | 0 | `test_epic2_users.py`, `test_epic3_library_edge_cases.py` | 100.0 % | Covered |
| US-06 | 2 | Should | Create custom lists | 53 | 53 | 0 | `test_epic2_journal_edge_cases.py`, `test_epic2_removal.py`, `test_epic2_users.py` | 100.0 % | Covered |
| US-07 | 2 | Should | View my activity diary | 186 | 186 | 0 | `test_epic2_journal_edge_cases.py`, `test_epic2_removal.py`, `test_epic2_users.py`, `test_epic4_chapter_rating_edge_cases.py`, `test_epic4_decision_edge_cases.py`, `test_epic4_playtime_edge_cases.py` | 100.0 % | Covered |
| US-08 | 3 | Must | Search the catalog | 45 | 43 | 2 | `test_catalog_cache.py`, `test_epic3_catalog.py`, `test_epic3_catalog_live.py`, `test_epic3_catalog_search_edge_cases.py`, `test_epic3_title_details_edge_cases.py` | 82.2 % | Covered |
| US-09 | 3 | Must | Title details with seasons and chapters | 147 | 144 | 3 | `test_epic3_catalog.py`, `test_epic3_catalog_live.py`, `test_epic3_description_and_genres.py`, `test_epic3_library_edge_cases.py`, `test_epic3_title_details_edge_cases.py`, `test_epic4_decision_points_in_details.py`, `test_epic4_seed_game_chapters.py` | 83.4 % | Covered |
| US-10 | 4 | Must | Rate a chapter or episode | 68 | 68 | 0 | `test_epic4_chapter_rating_edge_cases.py`, `test_epic4_episodic.py` | 100.0 % | Covered |
| US-11 | 4 | Should | Log playtime per chapter | 51 | 51 | 0 | `test_epic4_episodic.py`, `test_epic4_playtime_edge_cases.py` | 100.0 % | Covered |
| US-12 | 4 | Should | Record branching decisions | 103 | 103 | 0 | `test_epic4_decision_edge_cases.py`, `test_epic4_decision_points_in_details.py`, `test_epic4_episodic.py`, `test_epic4_seed_game_chapters.py` | 98.5 % | Covered |
| US-13 | 5 | Should | Cross-media recommendations | 14 | 14 | 0 | `test_epic5_ai.py`, `test_epic5_review_and_recommendation_edge_cases.py`, `test_openai_client.py` | 84.5 % | Covered |
| US-14 | 5 | Could | Spoiler detection in reviews | 20 | 20 | 0 | `test_epic5_ai.py`, `test_epic5_review_and_recommendation_edge_cases.py`, `test_openai_client.py` | 91.2 % | Covered |
| US-15 | 6 | Should | View personal statistics | 95 | 95 | 0 | `test_epic3_description_and_genres.py`, `test_epic6_analytics.py`, `test_epic6_stats_cache.py`, `test_epic6_stats_edge_cases.py` | 100.0 % | Covered |
| NFR-01 | - | - | Performance: cached search p95 < 500 ms | 22 | 22 | 0 | `test_catalog_cache.py`, `test_epic3_catalog_search_edge_cases.py`, `test_epic3_title_details_edge_cases.py`, `test_nfr.py` | 96.7 % | Covered |
| NFR-02 | - | - | Security: protected endpoints need a token | 303 | 303 | 0 | `test_epic2_auth_edge_cases.py`, `test_epic2_journal_edge_cases.py`, `test_epic2_login_identifier_edge_cases.py`, `test_epic3_catalog_search_edge_cases.py`, `test_epic3_title_details_edge_cases.py`, `test_epic4_chapter_rating_edge_cases.py`, `test_epic4_decision_edge_cases.py`, `test_epic4_playtime_edge_cases.py`, `test_epic5_review_and_recommendation_edge_cases.py`, `test_epic6_stats_edge_cases.py`, `test_nfr.py`, `test_security_checks.py`, `test_security_static.py`, `test_security_tokens.py` | 100.0 % | Covered |
| NFR-03 | - | - | Security: passwords are hashed | 65 | 65 | 0 | `test_nfr.py`, `test_security_static.py` | 100.0 % | Covered |
| NFR-04 | - | - | Reliability: survive outside failures | 73 | 73 | 0 | `test_catalog_cache.py`, `test_epic3_catalog_search_edge_cases.py`, `test_epic3_description_and_genres.py`, `test_epic3_title_details_edge_cases.py`, `test_health.py`, `test_nfr.py`, `test_openai_client.py` | 92.2 % | Covered |
| NFR-05 | - | - | Maintainability: coverage >= 70 % | - | - | - | `pytest --cov` in CI (`--cov-fail-under=70`) | 91.3 % (all modules) | Met |

Notes:

- A test case is counted for every requirement that it names in its name or docstring. Tests that name two requirements (for example `NFR-02` and `US-04`) are counted for both, so the column sums are larger than the total number of tests.
- Tests without an ID in their name (cache, health, token and static security tests) were assigned by hand: `test_catalog_cache` to NFR-01, NFR-04, US-08; `test_openai_client` to NFR-04, US-13, US-14; `test_health` to US-01, NFR-04; `test_security_checks`, `test_security_static` and `test_security_tokens` to NFR-02, NFR-03, US-03.
- "Statement coverage of its code" is the share of executed statements in the source modules that implement the requirement (the list of modules is in section 4). A module that serves several requirements is counted for each of them.

## 2. Non-functional requirements: how they are verified

| NFR | Criterion | Verified by | Result |
|---|---|---|---|
| NFR-01 | p95 < 500 ms over 100 cached requests | `test_nfr.py::test_nfr01_cached_search_p95_under_500ms`, `..._cached_stats_p95_under_500ms`; load test `tests/nonfunctional/run_load_test.py` | Met: 6.2 ms (search) and 4.2 ms (stats) in-process; load test see [non-func-tests](../non-func-tests/README.md) |
| NFR-02 | 401 without a token | `test_nfr02_protected_endpoints_require_token` (22 endpoints), `test_security_tokens.py` (6 JWT attacks), `test_security_checks.py` | Met: 22 of 22 endpoints answer 401 |
| NFR-03 | Password hashed, never returned | `test_nfr03_password_is_hashed_and_never_returned`, static checks | Met |
| NFR-04 | No unhandled 500 when IGDB, TMDB or OpenAI fail | `test_nfr04_*`, `test_epic3_*_edge_cases.py` (timeouts, refused keys, outages), `test_openai_client.py` | Met |
| NFR-05 | >= 70 % coverage | `pytest --cov=backend/app` | Met: 91.3 % lines, 78.3 % branches |

## 3. Acceptance-criteria matrix

Every Given/When/Then criterion of [`user-stories.md`](../../requirements/user-stories.md) is linked to one test that checks it. Many criteria have additional edge-case tests (see section 1 for the number of test cases per story).

| Story | Acceptance criterion | Test file | Test | Result |
|---|---|---|---|---|
| US-01 | GET /health returns 200 and {"status": "healthy"} | `test_epic1_infrastructure.py` | `test_us01_health_returns_ok` | Passed |
| US-02 | Valid data gives 201, no password or hash in the answer | `test_epic2_users.py` | `test_us02_register_user` | Passed |
| US-02 | Existing email or username gives 409 | `test_epic2_users.py` | `test_us02_register_duplicate_email_conflict` | Passed |
| US-02 | Invalid email or empty username gives 422 | `test_epic2_users.py` | `test_us02_register_invalid_email_rejected` | Passed |
| US-03 | Correct credentials give 200 and a JWT | `test_epic2_users.py` | `test_us03_login_returns_token` | Passed |
| US-03 | Wrong password gives 401 and no token | `test_epic2_users.py` | `test_us03_login_wrong_password_rejected` | Passed |
| US-04 | POST /library gives 201 and the entry is listed | `test_epic2_users.py` | `test_us04_add_to_library` | Passed |
| US-04 | Adding the same title again gives 409 | `test_epic2_users.py` | `test_us04_add_duplicate_entry_conflict` | Passed |
| US-04 | Without a login the answer is 401 | `test_epic2_users.py` | `test_us04_add_to_library_requires_authentication` | Passed |
| US-05 | PATCH with rating 8 returns rating 8 | `test_epic2_users.py` | `test_us05_rate_and_update_status` | Passed |
| US-05 | Rating 0 or 11 gives 422, entry unchanged | `test_epic2_users.py` | `test_us05_rating_out_of_range_rejected` | Passed |
| US-05 | Entry of another user gives 404 or 403 | `test_epic2_users.py` | `test_us05_cannot_update_other_users_entry` | Passed |
| US-06 | POST /lists with a name gives 201 | `test_epic2_users.py` | `test_us06_create_custom_list` | Passed |
| US-06 | A title can be added to the list | `test_epic2_users.py` | `test_us06_add_title_to_list` | Passed |
| US-06 | Empty list name gives 422 | `test_epic2_users.py` | `test_us06_empty_list_name_rejected` | Passed |
| US-06 | Same list name twice gives 409 | `test_epic2_journal_edge_cases.py` | `test_duplicate_list_name_returns_409` | Passed |
| US-07 | Added and rated events are returned, newest first | `test_epic2_users.py` | `test_us07_activity_diary` | Passed |
| US-07 | A new user gets an empty list and 200 | `test_epic2_users.py` | `test_us07_empty_diary_for_new_user` | Passed |
| US-08 | Search finds "Life is Strange" with title, poster and date | `test_epic3_catalog.py` | `test_us08_search_catalog` | Passed |
| US-08 | A query with no match gives an empty list and 200 | `test_epic3_catalog.py` | `test_us08_search_no_results_returns_empty_list` | Passed |
| US-08 | A repeated search is answered from the cache | `test_epic3_catalog_search_edge_cases.py` | `test_equal_searches_share_one_cache_entry` | Passed |
| US-09 | A series has seasons and episodes | `test_epic3_catalog.py` | `test_us09_series_details_include_seasons_and_episodes` | Passed |
| US-09 | An episodic game has chapters | `test_epic3_catalog.py` | `test_us09_title_details_with_chapters` | Passed |
| US-09 | An unknown id gives 404 | `test_epic3_catalog.py` | `test_us09_unknown_title_returns_404` | Passed |
| US-09 | Opening a loaded series again makes no TMDB call | `test_epic3_title_details_edge_cases.py` | `test_a_second_request_does_not_call_tmdb` | Passed |
| US-09 | TMDB down and series never loaded gives 503 | `test_epic3_title_details_edge_cases.py` | `test_outage_without_a_saved_copy_returns_503` | Passed |
| US-10 | PUT rating 4 is saved | `test_epic4_episodic.py` | `test_us10_rate_chapter` | Passed |
| US-10 | Rating 6 or 0 gives 422 | `test_epic4_episodic.py` | `test_us10_chapter_rating_out_of_range_rejected` | Passed |
| US-11 | 90 min and 30 min add up to 120 min | `test_epic4_episodic.py` | `test_us11_log_playtime` | Passed |
| US-11 | Negative playtime gives 422 | `test_epic4_episodic.py` | `test_us11_negative_playtime_rejected` | Passed |
| US-12 | The chosen option is stored and returned | `test_epic4_episodic.py` | `test_us12_record_decision` | Passed |
| US-12 | An option that is not allowed gives 422 | `test_epic4_episodic.py` | `test_us12_invalid_decision_rejected` | Passed |
| US-12 | Only the latest choice is kept | `test_epic4_episodic.py` | `test_us12_decision_can_be_changed` | Passed |
| US-13 | Completed game gives non-empty series list, none owned | `test_epic5_ai.py` | `test_us13_cross_media_recommendations` | Passed |
| US-13 | Empty library gives a list and 200 | `test_epic5_ai.py` | `test_us13_recommendations_with_empty_library` | Passed |
| US-14 | Review with a plot event is stored with contains_spoiler = true | `test_epic5_ai.py` | `test_us14_spoiler_detected` | Passed |
| US-14 | Review without plot details is stored with contains_spoiler = false | `test_epic5_ai.py` | `test_us14_non_spoiler_review_not_flagged` | Passed |
| US-15 | 3 games and 1 series show 75 % and 25 % | `test_epic6_analytics.py` | `test_us15_personal_statistics` | Passed |
| US-15 | Ratings 8, 8, 6 give 2 entries for 8 and 1 for 6 | `test_epic6_analytics.py` | `test_us15_personal_statistics` | Passed |
| US-15 | Empty library gives zero counts and 200 | `test_epic6_analytics.py` | `test_us15_statistics_for_empty_library` | Passed |

**40 of 40 acceptance criteria have a passing test (100 %).**

## 4. Source modules per requirement

| Req | Source modules (`backend/app/`) |
|---|---|
| US-01 | `main.py` |
| US-02 | `api/auth.py`, `services/auth_service.py`, `core/security.py`, `core/usernames.py`, `schemas/user.py` |
| US-03 | `api/auth.py`, `services/auth_service.py`, `core/security.py`, `api/deps.py` |
| US-04 | `api/library.py`, `services/library_service.py`, `api/media.py`, `services/media_service.py`, `schemas/library.py` |
| US-05 | `api/library.py`, `services/library_service.py`, `schemas/library.py` |
| US-06 | `api/journal.py`, `services/journal_service.py`, `schemas/journal.py` |
| US-07 | `api/journal.py`, `services/journal_service.py`, `services/diary_service.py` |
| US-08 | `api/catalog.py`, `services/catalog_service.py`, `integrations/igdb.py`, `integrations/tmdb.py`, `integrations/common.py`, `integrations/genres.py`, `core/cache.py` |
| US-09 | `api/catalog.py`, `services/catalog_service.py`, `integrations/tmdb.py`, `integrations/common.py`, `core/cache.py` |
| US-10 | `api/chapters.py`, `services/chapter_service.py`, `schemas/chapter.py` |
| US-11 | `api/chapters.py`, `services/chapter_service.py`, `schemas/chapter.py` |
| US-12 | `api/chapters.py`, `services/chapter_service.py`, `seed/loader.py`, `seed/schema.py`, `seed/__main__.py` |
| US-13 | `api/recommendations.py`, `integrations/openai_client.py` |
| US-14 | `services/review_service.py`, `schemas/review.py`, `api/library.py`, `integrations/openai_client.py` |
| US-15 | `api/stats.py`, `services/stats_service.py`, `schemas/stats.py` |
| NFR-01 | `core/cache.py` |
| NFR-02 | `api/deps.py`, `core/security.py` |
| NFR-03 | `services/auth_service.py`, `core/security.py` |
| NFR-04 | `core/errors.py`, `integrations/common.py`, `integrations/openai_client.py` |

## 5. Test files

| Test file | Test functions | Test cases | Requirements |
|---|---:|---:|---|
| `tests/requirements/test_catalog_cache.py` | 7 | 7 | NFR-01, NFR-04, US-08 |
| `tests/requirements/test_epic1_infrastructure.py` | 4 | 4 | US-01 |
| `tests/requirements/test_epic2_auth_edge_cases.py` | 22 | 22 | NFR-02, US-02, US-03 |
| `tests/requirements/test_epic2_journal_edge_cases.py` | 27 | 27 | NFR-02, US-06, US-07 |
| `tests/requirements/test_epic2_login_identifier_edge_cases.py` | 18 | 30 | NFR-02, US-02, US-03 |
| `tests/requirements/test_epic2_removal.py` | 35 | 37 | US-04, US-06, US-07 |
| `tests/requirements/test_epic2_token_lifetime.py` | 3 | 3 | US-03 |
| `tests/requirements/test_epic2_users.py` | 16 | 16 | US-02, US-03, US-04, US-05, US-06, US-07 |
| `tests/requirements/test_epic3_catalog.py` | 5 | 5 | US-08, US-09 |
| `tests/requirements/test_epic3_catalog_live.py` | 3 | 3 | US-08, US-09 |
| `tests/requirements/test_epic3_catalog_search_edge_cases.py` | 41 | 53 | NFR-01, NFR-02, NFR-04, US-08 |
| `tests/requirements/test_epic3_description_and_genres.py` | 35 | 50 | NFR-04, US-09, US-15 |
| `tests/requirements/test_epic3_library_edge_cases.py` | 22 | 22 | US-04, US-05, US-09 |
| `tests/requirements/test_epic3_title_details_edge_cases.py` | 52 | 69 | NFR-01, NFR-02, NFR-04, US-08, US-09 |
| `tests/requirements/test_epic4_chapter_rating_edge_cases.py` | 49 | 70 | NFR-02, US-07, US-10 |
| `tests/requirements/test_epic4_decision_edge_cases.py` | 44 | 62 | NFR-02, US-07, US-12 |
| `tests/requirements/test_epic4_decision_points_in_details.py` | 4 | 4 | US-09, US-12 |
| `tests/requirements/test_epic4_episodic.py` | 7 | 7 | US-10, US-11, US-12 |
| `tests/requirements/test_epic4_playtime_edge_cases.py` | 34 | 49 | NFR-02, US-07, US-11 |
| `tests/requirements/test_epic4_seed_game_chapters.py` | 22 | 34 | US-09, US-12 |
| `tests/requirements/test_epic5_ai.py` | 4 | 4 | US-13, US-14 |
| `tests/requirements/test_epic5_review_and_recommendation_edge_cases.py` | 12 | 14 | NFR-02, US-13, US-14 |
| `tests/requirements/test_epic6_analytics.py` | 2 | 2 | US-15 |
| `tests/requirements/test_epic6_stats_cache.py` | 11 | 11 | US-15 |
| `tests/requirements/test_epic6_stats_edge_cases.py` | 23 | 34 | NFR-02, US-15 |
| `tests/requirements/test_nfr.py` | 7 | 28 | NFR-01, NFR-02, NFR-03, NFR-04 |
| `tests/requirements/test_openai_client.py` | 8 | 8 | NFR-04, US-13, US-14 |
| `tests/test_health.py` | 7 | 7 | NFR-04, US-01 |
| `tests/test_security_checks.py` | 4 | 4 | NFR-02 |
| `tests/test_security_static.py` | 12 | 64 | NFR-02, NFR-03 |
| `tests/test_security_tokens.py` | 6 | 6 | NFR-02, US-03 |
| **Total** | **546** | **756** | |
