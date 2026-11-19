# Quality Findings and Mitigation Plan

**Branch:** `test_work` | **Date:** 19.11.2026

Severity uses the SonarQube scale (Blocker, High, Medium, Low). **No finding of severity Blocker was found.** The two High findings are marked. Severities in section 2 are assigned by the test team; the SonarQube scan may rate the same item differently, in which case the SonarQube rating is added to the row (see [README](README.md)).

## 1. Summary

| Id | Severity | Category | Finding | Status |
|---|---|---|---|---|
| Q-01 | **High** | Maintainability, reliability | Dead and duplicated list-deletion code | Open: fix proposed |
| Q-02 | **High** | Performance | `GET /recommendations` is unbounded and slow under load | Open: fix proposed |
| Q-03 | Medium | Security | No rate limit on login (bcrypt makes each attempt expensive) | Open |
| Q-04 | Medium | Reliability, security | Silent fallback to SQLite | Open |
| Q-05 | Low | Maintainability | Byte-order mark in 7 Python files | Open |
| Q-06 | Medium | Maintainability | Six functions with complexity 11 to 14 | Open |
| Q-07 | Medium | Maintainability | `datetime.utcnow()` is deprecated (about 1 950 warnings per test run) | Open |
| Q-08 | Medium | Test coverage | Frontend line coverage is 32.8 % | Open |
| Q-09 | Low | Performance | 5 ESLint warnings: `<img>` instead of `next/image` | Open |
| Q-10 | Low | Test coverage | Fallback providers of the catalog (TVMaze, iTunes, Steam) are barely tested | Open |

## 2. Findings in detail

### Q-01 (High): dead and duplicated list-deletion code

- **Where:** `backend/app/api/lists.py`, `backend/app/services/list_service.py`. The same two endpoints (`DELETE /lists/{id}`, `DELETE /lists/{id}/items/{media_item_id}`) also exist in `backend/app/api/journal.py` and `backend/app/services/journal_service.py`.
- **Evidence:** coverage of the two files is 60 % and 30 %. In `main.py` the `lists` router is included after `journal_router`, so FastAPI always matches the `journal.py` routes first, and the code in `lists.py` is never reached. The full behaviour (204, 404, ownership, diary events, atomic commit) is tested through `journal.py` in `test_epic2_removal.py`.
- **Risk:** the two copies differ. `journal_service` clears the statistics cache (`invalidate_stats_cache`) after a deletion, `list_service` does not. If someone reorders the routers or deletes the `journal.py` copy, `/stats` would show stale numbers for up to the cache time, and the tests would not necessarily notice. Duplicated code is also what SonarQube counts as duplication and unused code.
- **Mitigation:** delete `api/lists.py` and `services/list_service.py` and the lines in `main.py` that import and include `lists` (about three lines). No test has to change, because no test reaches this code. Keep the `journal.py` version. Add a short comment in `journal.py` that the delete endpoints live there.
- **Why it was not done on the `test_work` branch:** this branch only adds tests and documents. Changing production code is left to a separate reviewed pull request by the author of issue #117.
- **Done when:** both files are gone, `pytest` passes, backend coverage is >= 92 %.

### Q-02 (High): `GET /recommendations` is unbounded and slow

- **Evidence:** load test ([results](../non-func-tests/README.md)): about 21 requests per second whatever the load, p95 587 ms with 10 users and 1.6 s with 25 users, against 4 to 35 ms for the cached `/stats`. Code: `backend/app/api/recommendations.py` loads *all* titles of the requested type, reads `item.genres` for each (one extra query per title unless the relationship is eagerly loaded), ranks them in Python and returns the whole list. Its complexity is 13.
- **Risk:** the response time and the payload grow with the size of the catalog, which grows with every search. A single user can keep the server busy with a few requests per second.
- **Mitigation:**
  1. Add `limit` (default 20, maximum 50) and sort and cut in the database or after the ranking, so the answer is bounded.
  2. Load genres with `selectinload(MediaItem.genres)` to avoid one query per title.
  3. Cache the answer per user in Redis for a short time (60 s) and clear it when the library changes, as is already done for `/stats` (`invalidate_stats_cache`).
  4. Move the ranking into `services/` (an `app/services/recommendation_service.py`), which also lowers the complexity of the endpoint.
- **Done when:** p95 under 500 ms at 25 users in `run_load_test.py` and a test checks that `limit` is applied.

### Q-03 (Medium): no rate limit on login

- **Evidence:** bcrypt at cost 12 makes every login attempt cost about 250 ms of CPU (4 logins per second per core, 25 parallel logins wait up to 7.8 s). Nothing limits how many attempts one address or one account can make.
- **Risk:** password guessing and denial of service by many login requests.
- **Mitigation:** limit login and register requests per IP and per account (for example 5 per minute) at the reverse proxy (Caddy rate limit module in `docker/Caddyfile`) or in the application (`slowapi`). Run Uvicorn with more than one worker in production. Do not lower the bcrypt cost. Add a test that the sixth attempt in a minute gets 429.

### Q-04 (Medium): silent fallback to SQLite

- **Evidence:** `backend/app/core/database.py` switches to `sqlite:///./omnilog_local.db` when the URL contains `@localhost` or `@127.0.0.1` and nothing answers on port 5432.
- **Risk:** the switch only happens when the URL names `localhost` or `127.0.0.1`, so the Docker deployment (host name `db`) is not affected. But a single-host deployment with a stopped PostgreSQL would not fail. It would start with an empty local file, and users would lose their data without any error. SQLite also lacks the PostgreSQL constraints that the models rely on (the code removes the CHECK constraints for it).
- **Mitigation:** allow the fallback only when an explicit variable such as `ALLOW_SQLITE_FALLBACK=1` is set (documented for local development), and otherwise stop at start-up with a clear error, as is already done for a missing `DATABASE_URL`. Add a test for both cases (this also raises the coverage of `database.py`, 64 % today).

### Q-05 (Low): byte-order mark in Python files

- **Where:** `backend/app/main.py`, `core/database.py`, `core/security.py`, `tests/test_security_checks.py`, `tests/test_security_tokens.py`, `tests/requirements/test_epic2_token_lifetime.py`, `tests/requirements/test_epic2_auth_edge_cases.py`.
- **Evidence:** Radon fails with "invalid non-printable character U+FEFF" on the first three. Python itself accepts the mark, but some tools do not, and the three production files are then missing from complexity metrics.
- **Mitigation:** remove the first three bytes (`sed -i '1s/^\xEF\xBB\xBF//' file`) and add a CI or pre-commit check for a leading BOM. `.editorconfig` already sets `charset = utf-8` (plain UTF-8 without BOM), so the marks were most likely added by an editor that ignores it.

### Q-06 (Medium): complexity of six functions

| Function | Complexity | Proposal |
|---|---:|---|
| `integrations/openai_client.py: embed_texts` | 14 | Split input checking, the call with retry and the answer parsing |
| `seed/__main__.py: main` | 13 | Move argument handling and reporting into separate functions |
| `api/recommendations.py: get_recommendations` | 13 | Move the ranking into a service (see Q-02) |
| `integrations/openai_client.py: classify_spoiler` | 13 | Same split as `embed_texts`. Share the retry code |
| `integrations/tmdb.py: fetch_series` | 12 | Move the season loop into a helper |
| `integrations/igdb.py: _get_access_token` | 11 | Separate "cached token valid?" from "fetch a new token" |

All six have tests, so they can be refactored safely. Target: none above 10.

### Q-07 (Medium): `datetime.utcnow()` is deprecated

- **Evidence:** a test run prints about 1 950 deprecation warnings. Python 3.12 deprecates `datetime.utcnow()`, and it returns a *naive* datetime, which is easy to compare wrongly with an aware one.
- **Mitigation:** use `datetime.now(timezone.utc)` in code and `default=lambda: datetime.now(timezone.utc)` in the models, with `DateTime(timezone=True)` columns. Because this changes column types it needs an Alembic migration, so it is a planned change and not a quick fix.

### Q-08 (Medium): frontend coverage

- **Evidence:** 32.8 % of lines. High (90 to 100 %): `lib/server`, `lib/auth`, `proxy.ts`, library, search and title pages, state components. Low or zero: `lib/actions` (17 %), `lib/services` (0 %), `components/social` (0 %), `components/layout` (2 %), pages `diary`, `lists`, `stats`, `recommendations`, `friends` (0 %).
- **Mitigation:** write tests for the server actions (they hold the form logic and the calls to the API) and the data pages, using the existing MSW setup in `tests/mocks`. Target: 60 % for `src/lib` and `src/components`. Add `@vitest/coverage-v8` to `devDependencies` and `--coverage` to the CI step so the number is tracked.

### Q-09 (Low): `<img>` elements

Five ESLint warnings in `MediaStream.tsx`, `AddFriendModal.tsx` and `FriendActivityFeed.tsx`. Posters come from outside hosts, so `next/image` needs `images.remotePatterns` in `next.config.ts`. Replace the elements once the hosts are known.

### Q-10 (Low): fallback providers

`integrations/tmdb.py` (52 %) and `igdb.py` (64 %) contain the fallbacks to TVMaze, iTunes and the Steam Store. Add tests with the existing fake of the outside APIs (`fake_external_apis.py`), one per fallback: success, empty answer, error.

## 3. SonarQube findings of severity Blocker or High

_To be filled in after the scan._ Copy the format of section 2: Id `S-nn`, rule key, file and line, evidence, risk, mitigation, done-when.

| Id | Rule key | File and line | Severity | Mitigation | Status |
|---|---|---|---|---|---|
| | | | | | |
