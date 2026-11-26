# Quality findings and mitigation plan

Part of #234 (Software Test Document). First written on 2026-11-19 on `test_work`. **Updated on 2026-11-26** after `main` was merged into `test_work`: every finding was checked again against the current code (`c1fbcc9`), and the SonarQube findings of #349 were added.

The findings come from the static analysis ([static analysis](static-analysis.md)), SonarQube ([sonarqube](sonarqube.md)), the coverage run ([coverage](coverage.md)), the load test ([performance](performance.md)) and the review of the test files. The findings of the penetration test (F1 to F7) have their own table in the [penetration test report](penetration/README.md) and in section 7 of the [Software Testing Report](software-testing-report.md). Severity uses the SonarQube scale (Blocker, High, Medium, Low).

## 1. Summary

| ID | Severity | Finding | Status on 2026-11-26 | Fixed by |
|---|---|---|---|---|
| S-01 | **Blocker** (SonarQube vulnerability) | A database password in an example comment (`secrets:S6698`) | **Fixed** | #349 |
| S-02 | SonarQube bug | An unreachable second `raise` in `api/library.py` (`python:S1763`) | **Fixed** | #349 |
| S-03 | SonarQube bug | The same expression on both sides of an assertion in a test (`python:S5863`) | **Fixed** (false positive, the test was rewritten) | #349 |
| Q-01 | **High** | Dead and duplicated list delete code | **Fixed** | #344 (#305) |
| Q-02 | **High** | `GET /recommendations` had no limit and was slow under load | **Fixed** | #258 |
| Q-03 | Medium | No rate limit on login | **Fixed** | #236, #340 (F1) |
| Q-04 | Medium | Silent fallback to SQLite | Open, accepted for local development | none |
| Q-05 | Low | Byte-order mark in 7 Python files | **Fixed** | (checked on 2026-11-26) |
| Q-06 | Medium | Functions with complexity 11 to 14 | Open, accepted | none |
| Q-07 | Medium | `datetime.utcnow()` is deprecated | **Fixed** | #235 |
| Q-08 | Medium | Low frontend coverage | Partly fixed | #334, #333 |
| Q-09 | Low | `<img>` elements (ESLint warnings) | **Fixed** | #333, #326, #342 |
| Q-10 | Low | Fallback catalog providers barely tested | **Fixed** | #334 |
| Q-11 | Medium | The catalog search edge case tests were lost | **Open, new** (found on 2026-11-26) | proposed in section 3 |
| Q-12 | Medium | The API locks up at 80 users (database pool) | Open | proposed in [performance](performance.md), section 6 |

Blocker and High: **3 found (S-01, Q-01, Q-02), 3 fixed**, none open.

## 2. SonarQube findings of severity Blocker or High, and the bugs

The scan of #349 (SonarQube Community Build 26.11, 2026-11-25) found 2 bugs, 1 vulnerability and 12 code smells on `main` at `74f1f3a`. After #349: 0 of each, quality gate passed, ratings A/A/A. `test_work` changes no file under `backend/app` or `frontend/src` (`git diff main -- backend/app frontend/src` is empty), so the result is the same for this branch. Screenshots of the scan before and after are in [sonarqube](sonarqube.md).

| ID | Rule | File and line | Severity | What was done | Status |
|---|---|---|---|---|---|
| S-01 | `secrets:S6698` | `backend/app/core/config.py:19` | Blocker (vulnerability) | Only the development password of `docker-compose.yml`, in an example comment. The comment now shows `<user>:<password>` | Fixed in #349 |
| S-02 | `python:S1763` | `backend/app/api/library.py:83` | Bug | A second `raise` after the `except` block could never run. Removed | Fixed in #349 |
| S-03 | `python:S5863` | `tests/requirements/test_password_hashing.py:69` | Bug | False positive: the two bcrypt hashes of the same password differ because of the salt. Rewritten with two named hashes, and both are verified | Fixed in #349 |

The 12 code smells (a regex that could backtrack, a label without its field, ten `NaN` instead of `Number.NaN`) are low and were all fixed in #349. Their list is in section 2 of [sonarqube](sonarqube.md).

## 3. The other findings

### Q-01 (High): dead and duplicated list delete code. Fixed

`backend/app/api/lists.py` and `backend/app/services/list_service.py` repeated `DELETE /lists/{id}` and `DELETE /lists/{id}/items/{media_item_id}` of `journal.py`, but `journal.py` was registered first, so the copies never ran, and they did not clear the statistics cache. #344 removed both files. `tests/test_route_registration.py` now checks that the OpenAPI document has no duplicate operation, which is the warning that showed the copies.

### Q-02 (High): `GET /recommendations` had no limit. Fixed

On 2026-11-19 the endpoint loaded every title of the type, ranked them in Python and returned all of them: p95 587 ms with 10 users. #258 moved it to `services/recommendations_service.py`: the ranking is a pgvector query in the database, `limit` is 10 by default and at most 50 (`Query(ge=1, le=50)`), and the genres are loaded with `selectinload`. `test_us13_large_catalog_has_bounded_queries_and_response` (`test_epic5_ai.py`) checks that a catalog of 5 000 titles gives a small page with a bounded number of queries, and `test_us13_recommendations_rejects_out_of_range_limit` checks the limit. The pgvector retest of #351 ran 7 of 7 checks on the real vector query.

### Q-03 (Medium): no rate limit on login. Fixed

#236 added rate limits for login, register, search and review (`backend/app/core/rate_limit.py`, with Redis and an in-process fallback). The penetration test then found that the limit could be bypassed behind Render's proxy (F1, High), which #340 fixed. Tests: `test_rate_limits.py`, `test_f1_render_rate_limit.py`.

### Q-04 (Medium): silent fallback to SQLite. Open, accepted

`backend/app/core/database.py` still switches to `sqlite:///./omnilog_local.db` when the address is `localhost`, `127.0.0.1` or `::1` and nothing answers on the port. A remote host (the Docker service `db`, a managed database) is never replaced, so the production stacks are not affected. The risk stays for a single machine with a stopped PostgreSQL.

- **Mitigation (not done):** allow the fallback only with an explicit setting such as `ALLOW_SQLITE_FALLBACK=1`, and stop at start-up otherwise. Add a test for both cases.
- **Owner:** backend.

### Q-05 (Low): byte-order mark. Fixed

No Python file under `backend/` or `tests/` starts with a byte-order mark any more (`grep -rlI $'^\xEF\xBB\xBF' backend tests --include=*.py` finds nothing), and Radon now reads every file.

### Q-06 (Medium): complexity. Open, accepted

8 functions have grade C (11 to 14) in Radon, against 6 on 2026-11-19, because `sync.py: main` and `api/deps.py: client_address` (the F1 fix) are new. The list is in section 2 of [static analysis](static-analysis.md). All of them have tests, and SonarQube's cognitive complexity limit is not crossed (0 code smells). Splitting them is a refactoring for after the code freeze. Target: none above 10.

### Q-07 (Medium): `datetime.utcnow()`. Fixed

#235 added `backend/app/core/clock.py`, which gives the same naive UTC time without the deprecated call. The test run of 2026-11-26 printed 2 warnings, against about 1 950 on 2026-11-19. The 2 left are short JWT keys that `test_security_tokens.py` uses on purpose.

### Q-08 (Medium): frontend coverage. Partly fixed

32.8% of lines on 2026-11-19, **34.54%** on 2026-11-26. #334 put `@vitest/coverage-v8` and thresholds in the frontend and shows the numbers in every CI run, and #333 removed the friends page, which had no tests. Still open: `src/components/layout` (the animated background and the dashboard, 5% of 819 lines), `src/lib/actions` (29.5%) and the diary page (US-07, see section 4 of [traceability](traceability.md)).

- **Mitigation:** tests for the server actions and the diary page with the existing MSW setup in `frontend/tests/mocks`. Then raise the thresholds in `vitest.config.mts`.
- **Owner:** frontend.

### Q-09 (Low): `<img>` elements. Fixed

ESLint gives 0 warnings (2026-11-26). The five warnings were on the friends page, which #333 removed. The one `<img>` left (`PosterImage.tsx`) is on purpose: posters go through `/api/poster`, which takes only the TMDB and IGDB image hosts (#326, #342).

### Q-10 (Low): fallback catalog providers. Fixed

#334 added `tests/requirements/test_public_catalog_sources.py` (21 tests) for the keyless sources (TVMaze, iTunes, Steam). Line coverage: `integrations/tmdb.py` 52% to **96.8%**, `integrations/igdb.py` 64% to **91.5%**.

### Q-11 (Medium): the catalog search edge case tests were lost. Open, new

- **Evidence:** on 2026-11-19 commit `310010a` (#228) replaced `tests/requirements/test_epic3_catalog_search_edge_cases.py` (41 test functions for US-08: sign-in to IGDB, retries, the cache of a repeated search, limits of the query) with an almost exact copy of `test_epic3_title_details_edge_cases.py`. Since then the file tests title details (US-09) a second time, and the traceability matrix counts only 1 test of this file for US-08. The acceptance criterion "a repeated search is answered from the cache" is checked only for its speed (section 3 of [traceability](traceability.md)).
- **Check:** the old file (`git show 310010a^:tests/requirements/test_epic3_catalog_search_edge_cases.py`) was run on today's code: **52 of 53 cases pass**. The one failure, `test_control_characters_in_the_query_are_removed`, expects 200, but since #341 (F4) a query with control characters gets 422 on purpose.
- **Risk:** a change to the search, the IGDB sign-in or the search cache can break without a failing test. Coverage hides it, because other tests still run the lines.
- **Mitigation:** in a separate pull request, put the old file back under its name, change the one test to expect 422, and delete the duplicate. Run the traceability script again: US-08 should be named by many more tests.
- **Owner:** backend (catalog).

### Q-12 (Medium): the API locks up at 80 users. Open

The load test of 2026-11-25 and the re-run of 2026-11-26 both lock up at 80 users with `QueuePool limit of size 5 overflow 10 reached`. The SQLAlchemy pool (15 connections) is smaller than the thread pool of FastAPI (40). Mitigation and owner: recommendation 1 in section 6 of [performance](performance.md).
