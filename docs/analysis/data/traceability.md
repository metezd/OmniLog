# Traceability Table: All Epics

This table links every user story and non-functional requirement to its use case, DFD process, data entities, endpoints, tests and analysis document. Use it to check that the requirements, the DFDs, the data model and the tests agree.

It was checked against the code on 19.11.2026. The last full run of the test suite gave 735 passed and 7 skipped (the live API tests), with 91% line coverage of `backend/app`.

The detailed Epic 3 requirements (R-EP3-01 to R-EP3-09) are in [traceability-epic3.md](traceability-epic3.md).

Analysis status values: draft, reviewed, accepted. Implementation status values: Implemented, Partly implemented, Not implemented.

## 1. Requirements to design and code

| Req ID | Epic | Priority | Use case | DFD process | Data entities | Endpoint | Analysis document | Analysis status | Implementation |
|---|---|---|---|---|---|---|---|---|---|
| US-01 | 1 | Must | UC-EP1-01 | 1.0 | - | `GET /health`, `GET /health/ready` | behavior/dfd-level0-1.md | accepted | Implemented |
| US-02 | 2 | Must | UC-EP2-01 | 2.1 | `users` | `POST /auth/register` | behavior/dfd-epic2-journal.md | accepted | Implemented |
| US-03 | 2 | Must | UC-EP2-02 | 2.2 | `users` | `POST /auth/login`, `GET /auth/me` | behavior/dfd-epic2-journal.md | accepted | Implemented |
| US-04 | 2 | Must | UC-EP2-03 | 2.3, 2.5 | `user_libraries`, `media_items`, `diary_entries` | `POST /library`, `GET /library`, `DELETE /library/{id}` (extension) | behavior/dfd-epic2-journal.md | accepted | Implemented |
| US-05 | 2 | Must | UC-EP2-04 | 2.3, 2.5 | `user_libraries`, `diary_entries` | `PATCH /library/{id}` | behavior/dfd-epic2-journal.md | accepted | Implemented |
| US-06 | 2 | Should | UC-EP2-05 | 2.4, 2.5 | `custom_lists`, `custom_list_items`, `diary_entries` | `POST /lists`, `GET /lists`, `POST /lists/{id}/items`, `GET /lists/{id}`, `DELETE /lists/{id}/items/{media_item_id}` and `DELETE /lists/{id}` (extensions) | behavior/dfd-epic2-journal.md | accepted | Implemented |
| US-07 | 2 | Should | UC-EP2-06 | 2.5, 2.6 | `diary_entries` | `GET /diary` | behavior/dfd-epic2-journal.md | accepted | Implemented |
| US-08 | 3 | Must | UC-EP3-05 | 3.2, 3.3, 3.4, 3.5 | `media_items`, `genres` | `GET /catalog/search` | behavior/dfd-epic3-catalog.md | accepted | Implemented |
| US-09 | 3 | Must | UC-EP3-06 | 3.1, 3.3, 3.4, 3.5 | `media_items`, `genres`, `media_item_genres`, `seasons`, `chapters`, `decision_points`, `decision_options` | `GET /catalog/{id}` | behavior/dfd-epic3-catalog.md | accepted | Implemented. The manual sync (UC-EP3-03) is the command `python -m app.sync`. There is no sync endpoint and no lookup by outside id |
| US-10 | 4 | Must | UC-EP4-01 | 4.1, 4.2 | `chapter_progress`, `chapters` | `PUT /library/{id}/chapters/{chapter_id}/rating` | behavior/dfd-epic4-episodic.md | accepted | Implemented |
| US-11 | 4 | Should | UC-EP4-02 | 4.1, 4.3, 4.5 | `chapter_progress`, `playtime_logs` | `POST .../playtime`, `GET .../chapters/{chapter_id}` | behavior/dfd-epic4-episodic.md | accepted | Implemented |
| US-12 | 4 | Should | UC-EP4-03 | 4.1, 4.4, 4.5 | `decision_points`, `decision_options`, `user_decisions` | `PUT .../decision` | behavior/dfd-epic4-episodic.md | accepted | Implemented. The decision points of games come from the seed file |
| US-13 | 5 | Should | UC-EP5-01, UC-EP5-02 | 5.3 (5.1 and 5.2 are not built) | `user_libraries`, `media_items`, `genres`. The design also has `media_embeddings` and `user_taste_vectors`, which are not built | `GET /recommendations` | behavior/dfd-epic5-ai.md | accepted | Partly implemented. It ranks by genre. No embeddings |
| US-14 | 5 | Could | UC-EP5-03 | 5.4, 5.5 | `reviews`, `diary_entries` | `POST /library/{id}/review`, `GET /library/{id}/review` | behavior/dfd-epic5-ai.md | accepted | Implemented |
| US-15 | 6 | Should | UC-EP6-01 | 6.1 to 6.5 | `user_libraries`, `media_items`, `genres`, `chapter_progress` | `GET /stats` | behavior/dfd-epic6-analytics.md | accepted | Implemented, with the Redis cache |
| NFR-01 | All | - | - | 3.1, 3.2, 6.5 and D9 | Redis keys | `GET /catalog/search`, `GET /stats` | behavior/dfd-epic3-catalog.md | accepted | Implemented |
| NFR-02 | All | - | - | 1.0 | - | Every endpoint except the public ones listed in `dfd-level0-1.md` | behavior/dfd-level0-1.md | accepted | Implemented |
| NFR-03 | All | - | - | 2.1 | `users` | All user responses | behavior/dfd-epic2-journal.md | accepted | Implemented |
| NFR-04 | All | - | UC-EP3-04 | 3.7, 5.5 | - | Catalog endpoints and the review endpoint | behavior/dfd-epic3-catalog.md | accepted | Implemented |
| NFR-05 | All | - | - | - | - | - | requirement-analysis-report.md | accepted | Implemented. The CI gate is 70% and the last local run measured 91% |

## 2. Stories to tests

All tests are in `tests/`. The acceptance tests of a story are named `test_usNN_*` in the file for its epic. The other files hold the edge cases. A test file can serve more than one story.

| Req ID | Acceptance tests (function names) | Edge-case and supporting files |
|---|---|---|
| US-01 | `test_epic1_infrastructure.py`: `test_us01_health_returns_ok` | `test_health.py` (`/health` and `/health/ready`), `test_epic1_infrastructure.py` (startup stops without `DATABASE_URL` or with a short `SECRET_KEY`) |
| US-02 | `test_epic2_users.py`: `test_us02_register_user`, `test_us02_register_duplicate_email_conflict`, `test_us02_register_invalid_email_rejected` | `test_epic2_auth_edge_cases.py`, `test_epic2_login_identifier_edge_cases.py` (the `@` rule) |
| US-03 | `test_epic2_users.py`: `test_us03_login_returns_token`, `test_us03_login_wrong_password_rejected` | `test_epic2_auth_edge_cases.py`, `test_epic2_login_identifier_edge_cases.py` (login by username or email, `GET /auth/me`), `test_epic2_token_lifetime.py`, `test_security_tokens.py` |
| US-04 | `test_epic2_users.py`: `test_us04_add_to_library`, `test_us04_add_duplicate_entry_conflict`, `test_us04_add_to_library_requires_authentication` | `test_epic3_library_edge_cases.py`, `test_epic2_removal.py` (removal, an extension) |
| US-05 | `test_epic2_users.py`: `test_us05_rate_and_update_status`, `test_us05_rating_out_of_range_rejected`, `test_us05_cannot_update_other_users_entry` | `test_epic3_library_edge_cases.py` |
| US-06 | `test_epic2_users.py`: `test_us06_create_custom_list`, `test_us06_add_title_to_list`, `test_us06_empty_list_name_rejected` | `test_epic2_journal_edge_cases.py`, `test_epic2_removal.py` |
| US-07 | `test_epic2_users.py`: `test_us07_activity_diary`, `test_us07_empty_diary_for_new_user` | `test_epic2_journal_edge_cases.py`, the diary checks in the Epic 4 edge-case files |
| US-08 | `test_epic3_catalog.py`: `test_us08_search_catalog`, `test_us08_search_no_results_returns_empty_list` | `test_epic3_catalog_search_edge_cases.py`, `test_catalog_cache.py`, `test_epic3_catalog_live.py` (skipped unless `RUN_LIVE_API_TESTS=1`) |
| US-09 | `test_epic3_catalog.py`: `test_us09_title_details_with_chapters`, `test_us09_series_details_include_seasons_and_episodes`, `test_us09_unknown_title_returns_404` | `test_epic3_title_details_edge_cases.py`, `test_epic3_description_and_genres.py`, `test_epic4_decision_points_in_details.py`, `test_epic4_seed_game_chapters.py`, `test_epic3_manual_sync.py` (UC-EP3-03) |
| US-10 | `test_epic4_episodic.py`: `test_us10_rate_chapter`, `test_us10_chapter_rating_out_of_range_rejected` | `test_epic4_chapter_rating_edge_cases.py` |
| US-11 | `test_epic4_episodic.py`: `test_us11_log_playtime`, `test_us11_negative_playtime_rejected` | `test_epic4_playtime_edge_cases.py` |
| US-12 | `test_epic4_episodic.py`: `test_us12_record_decision`, `test_us12_invalid_decision_rejected`, `test_us12_decision_can_be_changed` | `test_epic4_decision_edge_cases.py`, `test_epic4_decision_points_in_details.py`, `test_epic4_seed_game_chapters.py` |
| US-13 | `test_epic5_ai.py`: `test_us13_cross_media_recommendations`, `test_us13_recommendations_with_empty_library` | `test_nfr.py` (token required). **Gap:** no test checks the order of the ranking by genre |
| US-14 | `test_epic5_ai.py`: `test_us14_spoiler_detected`, `test_us14_non_spoiler_review_not_flagged` | `test_openai_client.py` (the OpenAI classifier and the embedding function, with a fake client), `test_nfr.py` (`test_nfr04_review_survives_openai_down_and_is_saved`). **Gap:** no test checks that a second review replaces the first, that another user's entry gives 404, or that `GET` returns `null` before a review |
| US-15 | `test_epic6_analytics.py`: `test_us15_personal_statistics`, `test_us15_statistics_for_empty_library` | `test_epic6_stats_edge_cases.py`, `test_epic6_stats_cache.py`, `test_epic3_description_and_genres.py` (the genres that feed the breakdown) |
| NFR-01 | `test_nfr.py`: `test_nfr01_cached_search_p95_under_500ms`, `test_nfr01_cached_stats_p95_under_500ms` | `test_epic3_catalog_search_edge_cases.py`, `test_epic3_title_details_edge_cases.py` |
| NFR-02 | `test_nfr.py`: `test_nfr02_protected_endpoints_require_token` | `test_security_checks.py`, `test_security_static.py`, `test_security_tokens.py` |
| NFR-03 | `test_nfr.py`: `test_nfr03_password_is_hashed_and_never_returned` | `test_epic2_auth_edge_cases.py` |
| NFR-04 | `test_nfr.py`: `test_nfr04_survives_external_api_failure`, `test_nfr04_recommendations_survive_openai_down`, `test_nfr04_review_survives_openai_down_and_is_saved` | `test_epic3_catalog_search_edge_cases.py`, `test_epic3_title_details_edge_cases.py`, `test_openai_client.py`. Note: the recommendations never call OpenAI, so `test_nfr04_recommendations_survive_openai_down` passes without testing a fallback |
| NFR-05 | The coverage gate in `.github/workflows/ci.yml` (`--cov-fail-under=70`) | The last local run measured 91% line coverage of `backend/app` |

The business rules BR-10 to BR-13 are checked in the Epic 4 edge-case files, and BR-16 in `test_epic6_stats_edge_cases.py`. BR-18 (no `@` in a username) is checked in `test_epic2_login_identifier_edge_cases.py`.

## 3. Consistency checks

| Check | Result |
|---|---|
| Every user story has a DFD process | Yes |
| Every DFD process is used by at least one story | No. The processes 5.1 and 5.2 (embeddings) and 3.6 (sync) of the design are not built |
| Every table in the E-R diagram is read or written by a DFD process | No. `external_sources`, `sync_job_logs`, `media_embeddings` and `user_taste_vectors` are in the design only and have no table |
| Every endpoint in the code appears in a DFD | Yes. `POST /media` and `GET /media/{id}` are helpers for the catalog and have no process of their own |
| Every data store in Level 1 is used by a Level 2 document | Yes, except D8 and D10, which are not built |
| Every story has an acceptance test | Yes |
| Every behavior of a story has a test | No. See the gaps for US-13 and US-14 in section 2 |

Add a row to this table for every new or changed requirement in each PR.
