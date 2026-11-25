# Requirements traceability

Issue #300. This feeds the Software Testing Report (#296). Made on 2026-11-25.

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
| US-03 | Log in | `test_epic2_auth_edge_cases.py` (22), `test_epic2_login_identifier_edge_cases.py` (18), `test_epic2_token_lifetime.py` (3), `test_epic2_users.py` (2) | 45 |
| US-04 | Add a title to my library with a status | `test_epic2_removal.py` (35), `test_epic2_users.py` (3), `test_epic3_library_edge_cases.py` (22) | 60 |
| US-05 | Rate a title and update its status | `test_epic2_users.py` (3), `test_epic3_library_edge_cases.py` (22) | 25 |
| US-06 | Create custom lists | `test_epic2_journal_edge_cases.py` (27), `test_epic2_removal.py` (35), `test_epic2_users.py` (3) | 65 |
| US-07 | View my activity diary | `test_epic2_journal_edge_cases.py` (27), `test_epic2_removal.py` (35), `test_epic2_users.py` (16), `test_epic4_chapter_rating_edge_cases.py` (49), `test_epic4_decision_edge_cases.py` (44), `test_epic4_playtime_edge_cases.py` (34) | 205 |
| US-08 | Search the catalog | `test_epic3_catalog.py` (5), `test_epic3_catalog_search_edge_cases.py` (1), `test_epic3_description_and_genres.py` (1), `test_epic3_title_details_edge_cases.py` (1), `test_public_catalog_sources.py` (21) | 29 |
| US-09 | View title details with seasons and chapters | `test_epic3_catalog.py` (5), `test_epic3_catalog_live.py` (1), `test_epic3_catalog_search_edge_cases.py` (52), `test_epic3_description_and_genres.py` (57), `test_epic3_library_edge_cases.py` (2), `test_epic3_title_details_edge_cases.py` (52), `test_epic4_decision_points_in_details.py` (4), `test_epic4_seed_game_chapters.py` (22), `test_public_catalog_sources.py` (21) | 216 |
| US-10 | Rate an individual chapter or episode | `test_epic4_chapter_rating_edge_cases.py` (49), `test_epic4_episodic.py` (7) | 56 |
| US-11 | Log playtime per chapter | `test_epic4_episodic.py` (2), `test_epic4_playtime_edge_cases.py` (34) | 36 |
| US-12 | Record branching decisions | `test_epic4_decision_edge_cases.py` (44), `test_epic4_decision_points_in_details.py` (4), `test_epic4_episodic.py` (7), `test_epic4_seed_game_chapters.py` (22) | 77 |
| US-13 | Cross-media recommendations | `test_embeddings_command.py` (5), `test_epic5_ai.py` (26) | 31 |
| US-14 | Spoiler detection in reviews | `test_epic5_ai.py` (26), `test_nfr.py` (1) | 27 |
| US-15 | View personal statistics | `test_epic6_analytics.py` (2), `test_epic6_stats_cache.py` (11), `test_epic6_stats_edge_cases.py` (24) | 37 |
| NFR-01 | Cached catalog searches are fast. | `test_epic3_catalog.py` (5), `test_epic3_catalog_search_edge_cases.py` (52), `test_epic3_description_and_genres.py` (57), `test_epic3_title_details_edge_cases.py` (52), `test_nfr.py` (7) | 173 |
| NFR-02 | Protected endpoints require authentication. | `test_epic2_auth_edge_cases.py` (4), `test_epic2_journal_edge_cases.py` (2), `test_epic2_login_identifier_edge_cases.py` (18), `test_epic3_catalog_search_edge_cases.py` (1), `test_epic3_description_and_genres.py` (1), `test_epic3_title_details_edge_cases.py` (1), `test_epic4_chapter_rating_edge_cases.py` (49), `test_epic4_decision_edge_cases.py` (44), `test_epic4_playtime_edge_cases.py` (34), `test_epic6_stats_edge_cases.py` (24), `test_nfr.py` (1) | 179 |
| NFR-03 | Passwords are never stored or returned in plain text. | `test_nfr.py` (1), `test_password_hashing.py` (12) | 13 |
| NFR-04 | The API survives external API failures. | `test_epic3_catalog_search_edge_cases.py` (52), `test_epic3_description_and_genres.py` (57), `test_epic3_title_details_edge_cases.py` (52), `test_nfr.py` (7), `test_rate_limits.py` (11) | 179 |
| NFR-05 | Backend code is covered by automated tests. | `test_coverage_gate.py` (4) | 4 |

Every story and every NFR is named by at least two test files, except NFR-05. NFR-05 is a property of the whole suite: CI measures it with `--cov-fail-under`, and `tests/test_coverage_gate.py` checks the gate settings. This reason is written in the test.

### Added for this issue

The earlier snapshot found two requirements with one test file only:

- **US-01**: two new tests in `test_epic1_infrastructure.py`, an edge case (`/health` needs no token and ignores a broken one) and a negative case (`POST /health` gets 405, not a false "healthy"). The tests of `/health/ready` in `tests/test_health.py` now name US-01 in their module docstring.
- **NFR-05**: `tests/test_coverage_gate.py` checks that the CI gate is at least the required 70%, that `CONTRIBUTING.md` uses the same gate as CI, that no file is left out of the measurement with `omit` or an exclusion, and that the frontend has thresholds. `test_nfr.py` no longer names NFR-05, because it does not test it.

## 3. Non-functional requirements with the measured values

| ID | Requirement | Limit | Measured | How |
|---|---|---|---|---|
| NFR-01 | Cached catalog searches are fast | p95 under 500 ms over 100 requests | **3.3 to 3.4 ms** for the cached search and **2.6 to 2.7 ms** for `/stats` (3 runs). Over HTTP through Caddy: p95 29 ms for the cached search with 10 users, and the whole mix under 500 ms up to 40 users ([performance](performance.md)) | `test_nfr01_*` in Docker with Redis, 2026-11-25 |
| NFR-02 | Protected endpoints require authentication | 401 without a valid token | **23 of 23** protected endpoints answer 401 | `test_nfr02_protected_endpoints_require_token` (23 cases) |
| NFR-03 | Passwords are never stored or returned in plain text | stored value differs, no response contains a password or hash | **passed** | `test_nfr03_*`, `test_password_hashing.py` |
| NFR-04 | The API survives external API failures | cached data or 503, never an unhandled 500 | **passed** for IGDB and TMDB down, OpenAI down for reviews and recommendations | `test_nfr04_*` (3 tests) and the edge case files |
| NFR-05 | Backend code is covered by automated tests | at least 70% line coverage | **94.96%** (gate in CI: 90%) | [coverage](coverage.md) |

The NFR-01 values in process are far under the limit, because they measure the code and the database without the network or other users. The HTTP load test is the second kind of evidence for the same requirement.
