# Requirements traceability

Issue #300. This feeds the Software Testing Report (#296). Made on 2026-11-25. Section 2 was generated again on 2026-11-26 after #234 was merged with `main`, and sections 3 and 4 (acceptance criteria and frontend tests) come from #234.

## 1. How the matrix is made

`tests/tools/requirements_matrix.py` reads the user stories from the story table in [`docs/requirements/user-stories.md`](../requirements/user-stories.md) and the non-functional requirements from the NFR table in [`docs/requirements/requirements-specification.md`](../requirements/requirements-specification.md). Then it looks for each ID in the names and docstrings of every test function in `tests/**/test_*.py`. `US-01` in a docstring and `us01` in a test name both count, but not `US-010`.

The docstring of a module or a class counts for every test in it, because many files name their stories once at the top. So the number of tests is an **upper bound**: it counts the tests in files that are about a requirement, not only the tests that check it directly. A parametrized test counts once.

`tests/test_requirements_traceability.py` runs in every CI run. It fails when:

- fewer than 15 stories or 5 NFRs are read (a changed table format cannot make the check empty),
- a requirement is not named by any test,
- a requirement is named by only one test file and has no written reason,
- a test is marked `xfail` or `not_built` (the helper of the requirements phase is gone, and `git grep -n "not_built\|xfail" -- tests` finds nothing).

The check was tried once by adding a `US-16` row to the story table that no test names: the test failed with `no test names these requirements in its name or docstring: ['US-16']`, and passed again after the row was removed.

To print the matrix again:

```bash
python tests/tools/requirements_matrix.py
```

## 2. Matrix

| Requirement | Subject | Test files | Tests |
|---|---|---|---|
| US-01 | Service health check | `test_epic1_infrastructure.py` (4), `test_health.py` (7) | 11 |
| US-02 | Register an account | `test_epic2_auth_edge_cases.py` (22), `test_epic2_login_identifier_edge_cases.py` (18), `test_epic2_users.py` (16) | 56 |
| US-03 | Log in | `test_epic2_auth_edge_cases.py` (22), `test_epic2_login_identifier_edge_cases.py` (18), `test_epic2_token_lifetime.py` (3), `test_epic2_users.py` (2), `test_f1_render_rate_limit.py` (6) | 51 |
| US-04 | Add a title to my library with a status | `test_epic2_removal.py` (35), `test_epic2_users.py` (3), `test_epic3_library_edge_cases.py` (22), `test_malformed_input.py` (20) | 80 |
| US-05 | Rate a title and update its status | `test_epic2_users.py` (3), `test_epic3_library_edge_cases.py` (22) | 25 |
| US-06 | Create custom lists | `test_epic2_journal_edge_cases.py` (27), `test_epic2_removal.py` (35), `test_epic2_users.py` (3), `test_malformed_input.py` (20) | 85 |
| US-07 | View my activity diary | `test_epic2_journal_edge_cases.py` (27), `test_epic2_removal.py` (35), `test_epic2_users.py` (16), `test_epic4_chapter_rating_edge_cases.py` (49), `test_epic4_decision_edge_cases.py` (44), `test_epic4_playtime_edge_cases.py` (34) | 205 |
| US-08 | Search the catalog | `test_epic3_catalog.py` (5), `test_epic3_catalog_search_edge_cases.py` (1), `test_epic3_description_and_genres.py` (1), `test_epic3_title_details_edge_cases.py` (1), `test_malformed_input.py` (20), `test_poster_url.py` (3), `test_public_catalog_sources.py` (21) | 52 |
| US-09 | View title details with seasons and chapters | `test_epic3_catalog.py` (5), `test_epic3_catalog_live.py` (1), `test_epic3_catalog_search_edge_cases.py` (52), `test_epic3_description_and_genres.py` (57), `test_epic3_library_edge_cases.py` (2), `test_epic3_title_details_edge_cases.py` (52), `test_epic4_decision_points_in_details.py` (4), `test_epic4_seed_game_chapters.py` (22), `test_public_catalog_sources.py` (21) | 216 |
| US-10 | Rate an individual chapter or episode | `test_epic4_chapter_rating_edge_cases.py` (49), `test_epic4_episodic.py` (7) | 56 |
| US-11 | Log playtime per chapter | `test_epic4_episodic.py` (2), `test_epic4_playtime_edge_cases.py` (34) | 36 |
| US-12 | Record branching decisions | `test_epic4_decision_edge_cases.py` (44), `test_epic4_decision_points_in_details.py` (4), `test_epic4_episodic.py` (7), `test_epic4_seed_game_chapters.py` (22), `test_malformed_input.py` (20) | 97 |
| US-13 | Cross-media recommendations | `test_embeddings_command.py` (5), `test_epic5_ai.py` (26), `test_epic5_review_and_recommendation_edge_cases.py` (10) | 41 |
| US-14 | Spoiler detection in reviews | `test_epic5_ai.py` (26), `test_epic5_review_and_recommendation_edge_cases.py` (10), `test_malformed_input.py` (20), `test_nfr.py` (1) | 57 |
| US-15 | View personal statistics | `test_epic6_analytics.py` (2), `test_epic6_stats_cache.py` (11), `test_epic6_stats_edge_cases.py` (24) | 37 |
| NFR-01 | Cached catalog searches are fast. | `test_epic3_catalog.py` (5), `test_epic3_catalog_search_edge_cases.py` (52), `test_epic3_description_and_genres.py` (57), `test_epic3_title_details_edge_cases.py` (52), `test_nfr.py` (7) | 173 |
| NFR-02 | Protected endpoints require authentication. | `test_epic2_auth_edge_cases.py` (4), `test_epic2_journal_edge_cases.py` (2), `test_epic2_login_identifier_edge_cases.py` (18), `test_epic3_catalog_search_edge_cases.py` (1), `test_epic3_description_and_genres.py` (1), `test_epic3_title_details_edge_cases.py` (1), `test_epic4_chapter_rating_edge_cases.py` (49), `test_epic4_decision_edge_cases.py` (44), `test_epic4_playtime_edge_cases.py` (34), `test_epic5_review_and_recommendation_edge_cases.py` (10), `test_epic6_stats_edge_cases.py` (24), `test_f1_render_rate_limit.py` (6), `test_nfr.py` (1) | 195 |
| NFR-03 | Passwords are never stored or returned in plain text. | `test_malformed_input.py` (20), `test_nfr.py` (1), `test_password_hashing.py` (12) | 33 |
| NFR-04 | The API survives external API failures. | `test_epic3_catalog_search_edge_cases.py` (52), `test_epic3_description_and_genres.py` (57), `test_epic3_title_details_edge_cases.py` (52), `test_nfr.py` (7), `test_rate_limits.py` (11) | 179 |
| NFR-05 | Backend code is covered by automated tests. | `test_coverage_gate.py` (4) | 4 |

Every story and every NFR is named by at least two test files, except NFR-05. NFR-05 is a property of the whole suite: CI measures it with `--cov-fail-under`, and `tests/test_coverage_gate.py` checks the gate settings. This reason is written in the test.

### Added for this issue

The earlier snapshot found two requirements with one test file only:

- **US-01**: two new tests in `test_epic1_infrastructure.py`, an edge case (`/health` needs no token and ignores a broken one) and a negative case (`POST /health` gets 405, not a false "healthy"). The tests of `/health/ready` in `tests/test_health.py` now name US-01 in their module docstring.
- **NFR-05**: `tests/test_coverage_gate.py` checks that the CI gate is at least the required 70%, that `CONTRIBUTING.md` uses the same gate as CI, that no file is left out of the measurement with `omit` or an exclusion, and that the frontend has thresholds. `test_nfr.py` no longer names NFR-05, because it does not test it.

## 3. Acceptance criteria

The matrix of section 2 counts tests per requirement. This one goes one level down: every Given/When/Then criterion of [`user-stories.md`](../requirements/user-stories.md) is linked to the test that checks it. Many criteria have more edge case tests (section 2). Each test below was checked in the JUnit report of the run of 2026-11-26 (1106 passed, 0 failed).

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
| US-08 | A repeated search is answered from the cache | `test_nfr.py` | `test_nfr01_cached_search_p95_under_500ms` | **Partly**: only the speed of the repeated search is checked, see the note below |
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


**39 of 40 criteria have a passing test, 1 is covered only in part.** The test that counted the calls to IGDB for a repeated search (`test_equal_searches_share_one_cache_entry`) was lost on 2026-11-19, when commit `310010a` (#228) replaced `test_epic3_catalog_search_edge_cases.py` with a copy of the title details tests. The 41 search tests of the old file still pass on today's code (52 of 53 cases, the one failure is the intended 422 for control characters of #341). They are finding Q-11 of the [mitigation plan](mitigation-plan.md).

## 4. Frontend tests

The frontend tests (Vitest, `frontend/tests/`) do not name requirement IDs, so the script of section 1 does not count them. They were mapped by hand, through the screens of [`screen-list.md`](../analysis/ui/screen-list.md). Run of 2026-11-26: **342 tests in 44 files, 0 failed**.

| Requirement | Screen | Frontend test files (tests) | What they check |
|---|---|---|---|
| US-01 | none | `app/api/health.test.ts` (2) | The health route of the frontend answers |
| US-02 | S-02 | `components/auth/RegisterForm.test.tsx` (6), `components/auth/AuthField.test.tsx` (6), `lib/actions/auth.test.ts` (26, with US-03) | The form, field errors, the server action and the answers of the backend |
| US-03 | S-03 | `components/auth/LoginForm.test.tsx` (9), `components/auth/AuthBanner.test.tsx` (3), `components/auth/AuthCard.test.tsx` (2), `lib/actions/auth.test.ts`, `lib/server/session.test.ts` (28), `lib/auth/token.test.ts` (7), `app/session-expired.test.ts` (1) | Login, the `HttpOnly` session cookie and its lifetime, an ended or refused token |
| US-04, US-05 | S-04 | `components/library/LibraryPage.test.tsx` (4), `components/library/LibraryEntryCard.test.tsx` (2), `components/search/AddToLibraryButton.test.tsx` (2), `components/title/LibraryControls.test.tsx` (3), `lib/server/data.test.ts` (21, with US-06) | Add, list, change the status and the rating, remove |
| US-06 | S-07, S-08 | `components/lists/CreateListForm.test.tsx` (2), `components/lists/DeleteListButton.test.tsx` (1), `lib/server/data.test.ts` | Create and delete a list, take a title out of a list |
| US-07 | S-09 | `lib/server/data.test.ts` | Only the call `GET /diary`. **The diary page itself has no test** |
| US-08 | S-05 | `components/search/SearchPage.test.tsx` (5), `components/search/SearchResultCard.test.tsx` (2), `lib/media.test.ts` (9) | Search page, results, labels, release year |
| US-09 to US-12 | S-06 | `components/title/TitleDetailPage.test.tsx` (7), `components/title/ChapterProgressCard.test.tsx` (3) | Title details with seasons, episodes and chapters, chapter rating, playtime and decisions, the saved review on the page |
| US-13 | S-10 | `app/recommendations/page.test.tsx` (9) | The recommendations page, empty and error states |
| US-14 | S-06 | `components/title/ReviewSection.test.tsx` (12), `lib/actions/library.test.ts` (6) | Writing a review, the spoiler flag, blank text, 404, 422 and 503 answers |
| US-15 | S-11 | `app/stats/page.test.tsx` (14) | The statistics page and its states |
| NFR-02 | all | `proxy.test.ts` (13), `lib/auth/routes.test.ts` (13), `lib/server/authed.test.ts` (9), `lib/server/user.test.ts` (5) | Protected pages send a visitor without a session to the login page, and the token goes only to the backend |
| NFR-04 | S-15 | `components/states/states.test.tsx` (9), `lib/server/error-state.test.ts` (10), `lib/server/backend.test.ts` (35) | 401, 404 and 503 from the backend become an error state and never a raw error text |
| Security (F3, F7) | all | `next-config.test.ts` (2), `app/api/poster.test.ts` (5), `app/api/poster-route.test.ts` (14), `security/eslint-security-rules.test.ts` (17), `security/happy-dom.test.ts` (2) | The Content-Security-Policy and security headers, the poster proxy only for the TMDB and IGDB image hosts, the security lint rules |
| (test setup) | none | `components/layout/*.test.tsx` (8), `lib/utils.test.ts` (3), `mocks/*.test.ts` (5) | Landing page, navigation, footer, helpers and the mock server of the tests |

The counts of the rows add up to more than 342, because `lib/actions/auth.test.ts` and `lib/server/data.test.ts` serve more than one row. Every user story has frontend tests; the weakest is **US-07**, where only the data call is tested and not the diary page. That gap is part of finding Q-08 of the [mitigation plan](mitigation-plan.md).

## 5. Non-functional requirements with the measured values

| ID | Requirement | Limit | Measured | How |
|---|---|---|---|---|
| NFR-01 | Cached catalog searches are fast | p95 under 500 ms over 100 requests | **3.3 to 3.4 ms** for the cached search and **2.6 to 2.7 ms** for `/stats` (3 runs). Over HTTP through Caddy: p95 29 ms for the cached search with 10 users, and the whole mix under 500 ms up to 40 users ([performance](performance.md)) | `test_nfr01_*` in Docker with Redis, 2026-11-25 |
| NFR-02 | Protected endpoints require authentication | 401 without a valid token | **23 of 23** protected endpoints answer 401 | `test_nfr02_protected_endpoints_require_token` (23 cases) |
| NFR-03 | Passwords are never stored or returned in plain text | stored value differs, no response contains a password or hash | **passed** | `test_nfr03_*`, `test_password_hashing.py` |
| NFR-04 | The API survives external API failures | cached data or 503, never an unhandled 500 | **passed** for IGDB and TMDB down, OpenAI down for reviews and recommendations | `test_nfr04_*` (3 tests) and the edge case files |
| NFR-05 | Backend code is covered by automated tests | at least 70% line coverage | **95.86%** on 2026-11-26 (gate in CI: 90%) | [coverage](coverage.md) |

The NFR-01 values in process are far under the limit, because they measure the code and the database without the network or other users. The HTTP load test is the second kind of evidence for the same requirement.
