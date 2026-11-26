# Software Testing Report

Issue #296, part of #252 (section D). Related: #157, #234.

This report ties the test work of the project together. It links to the detailed documents and does not copy them. Every number comes from a command that was run, and the command and the date are next to it (section 12). The first version measured `main` at `74f1f3a` (25.11.2026). On 26.11.2026 the review of #234 asked for one set of documents with current numbers, so #234 was merged with `main` (`e23f225`) and the tests, the coverage, the traceability matrix, the static analysis and the load test were run again on that code (`test_work` at `c1fbcc9`). The documents of #234 were merged into the ones of `main`; the list is in the [test documentation](README.md).

## 1. Summary

| Area | Result | Date | Details |
|---|---|---|---|
| Backend tests | **1106 passed, 0 failed, 4 skipped** (3 live API tests without keys, 1 test that runs only when Redis is down) | 26.11.2026 | Section 4 |
| Frontend tests | **342 passed, 0 failed** in 44 files | 26.11.2026 | Section 4 |
| Requirement traceability | Every user story (15) and NFR (5) is named by tests, checked in CI. **39 of 40** acceptance criteria have a passing test, 1 in part (Q-11). Every story has frontend tests | 26.11.2026 | Section 4, [traceability](traceability.md) |
| Coverage | Backend **95.86%** of lines (CI gate 90%), frontend **34.54%** of lines (thresholds 25 to 40%) | 26.11.2026 | Section 5, [coverage](coverage.md) |
| Performance | p95 under 500 ms up to **40 users** on one uvicorn process (20 users with one CPU), about 500 requests/s; the API **locks up at 80 users** (database pool). Re-run on the current code: the same shape, limits held up to **20 users** on 2 vCPU | 25./26.11.2026 | Section 6, [performance](performance.md) |
| Penetration test | First run 7 findings (1 high). Retest: **31 of 31** checks passed locally and **31 of 31** through Caddy on the production stack, **7 of 7** pgvector checks, OWASP ZAP **0 failed** | 25./26.11.2026 | Section 7, [penetration](penetration/README.md) |
| SonarQube | Quality gate passed. After the fixes **0 bugs, 0 vulnerabilities, 0 hotspots, 0 code smells**, ratings A/A/A (#349). The CI job is ready but waits for a token | 25.11.2026 | Section 8, [sonarqube](sonarqube.md) |
| Static analysis | Ruff, Bandit, `pip-audit`, `npm audit`, ESLint and `tsc`: **0 findings**. Radon: average complexity A (3.14), 8 functions of grade C | 26.11.2026 | Section 8, [static analysis](static-analysis.md) |
| Quality findings | 3 of severity Blocker or High, **all 3 fixed**. 15 in all: 10 fixed, 1 partly, 4 open (Q-04, Q-06, Q-11, Q-12) | 26.11.2026 | [Mitigation plan](mitigation-plan.md) |
| TDD | 14 of 15 stories had their test first. **9 fix cycles** have a red `test:` commit and a green `fix:` commit | 25./26.11.2026 | Section 9, [TDD evidence](tdd-evidence.md) |

## 2. Strategy

| Level | What it checks | Tool | Where |
|---|---|---|---|
| Requirement tests | Each user story and NFR, with positive, negative and edge cases | pytest with FastAPI's test client | `tests/requirements/` |
| Traceability check | Every story and NFR is named by at least two test files, or a reason is written | pytest | `tests/test_requirements_traceability.py` |
| Static security tests | Dangerous code patterns (secrets in logs, raw SQL, eval), configuration of production files | pytest reading the source | `tests/test_security_static.py`, `tests/test_security_checks.py` |
| Hardening tests | Security headers on every status, tokens, docs switch, uvicorn options | pytest | `tests/test_security_hardening.py`, `tests/test_security_tokens.py` |
| Frontend tests | Components, server actions, the backend client, the proxy and its Content-Security-Policy | Vitest with Testing Library, happy-dom, MSW | `frontend/tests/` |
| Performance | NFR-01 in process, and an HTTP load test of the production stack | pytest; a script with httpx and asyncio | `tests/requirements/test_nfr.py`, `tests/performance/` |
| Penetration | Black-box attacks over HTTP, an automated scanner, a browser check | Python script, OWASP ZAP, Chrome | `tests/pentest/`, [penetration](penetration/README.md) |
| Static analysis | Bugs, vulnerabilities, smells, duplication, coverage | SonarQube Community Build, Ruff, ESLint, Semgrep, zizmor, Gitleaks, Trivy | `sonar-project.properties`, `.github/workflows/` |

The backend tests use a real **PostgreSQL** (with pgvector in Docker and CI) and **Redis** when it runs; when Redis is down they use the in-process fallback, which is also tested. The outside services are replaced: IGDB and TMDB by a fake at the HTTP level (`tests/requirements/fake_external_apis.py`), OpenAI by `tests/requirements/fake_openai.py`. Three live tests call the real IGDB and TMDB on a manual CI run only.

## 3. Environment

| | Numbers of this report | CI |
|---|---|---|
| Machine | Apple M3 Pro, 11 cores, 18 GB, macOS 27.2.1, Docker Desktop with 11 CPUs and 7.7 GB. **Not the production machine** | GitHub `ubuntu-latest` |
| Backend | `python:3.15-slim` (Python 3.15.2), the version of `backend/Dockerfile`; pytest 9.2.0, pytest-cov 7.1.0 | Python 3.15 |
| Database | PostgreSQL 16.16 with pgvector 0.8.7 (`docker-compose.yml`) | the same image |
| Redis | 7.4.12 | 7 |
| Frontend | `node:24-slim` (Node 24.22.3), Vitest 5.1.0 | Node 24 |
| Production | Render free plan (`render.yaml`) or the Docker stack (`docker-compose.prod.yml`) | |

The numbers of 26.11.2026 after the merge of #234 (backend and frontend tests, coverage, traceability, static analysis, the re-run of the load test) come from a second machine: Linux (Ubuntu 24.04), Intel Xeon with **2 vCPU** and 7 GB, Python 3.15.0b4 with the locked packages, PostgreSQL 16.15 with pgvector 0.6.0, Redis 7.0.15 and Node 24.22.3, without Docker (the images could not be pulled there). Test results and coverage do not depend on the machine; the load test does, so its re-run is shown on its own (section 6).

The TDD runs of #345 were made on Windows 11 with Python 3.13.9 and PostgreSQL 17, and repeated on the machine above. Render has far less CPU than this machine, so the performance numbers are an upper bound for it (section 6).

## 4. Requirement tests

The matrix is generated by `python tests/tools/requirements_matrix.py` and kept in [traceability](traceability.md). Run on 26.11.2026 against `test_work` at `c1fbcc9`:

| Requirement | Subject | Test files | Tests that name it |
|---|---|---|---|
| US-01 | Service health check | 2 | 11 |
| US-02 | Register an account | 3 | 56 |
| US-03 | Log in | 5 | 51 |
| US-04 | Add a title to my library with a status | 4 | 80 |
| US-05 | Rate a title and update its status | 2 | 25 |
| US-06 | Create custom lists | 4 | 85 |
| US-07 | View my activity diary | 6 | 205 |
| US-08 | Search the catalog | 7 | 52 |
| US-09 | View title details with seasons and chapters | 9 | 216 |
| US-10 | Rate an individual chapter or episode | 2 | 56 |
| US-11 | Log playtime per chapter | 2 | 36 |
| US-12 | Record branching decisions | 5 | 97 |
| US-13 | Cross-media recommendations | 3 | 41 |
| US-14 | Spoiler detection in reviews | 4 | 57 |
| US-15 | View personal statistics | 3 | 37 |
| NFR-01 | Cached catalog searches are fast | 5 | 173 |
| NFR-02 | Protected endpoints require authentication | 13 | 195 |
| NFR-03 | Passwords are never stored or returned in plain text | 3 | 33 |
| NFR-04 | The API survives external API failures | 5 | 179 |
| NFR-05 | Backend code is covered by automated tests | 1 | 4 |

A module or class docstring counts for every test in it, so the test numbers are an upper bound. NFR-05 has one file on purpose: it is a property of the whole suite, measured by the CI gate (the reason is written in the check). No test is marked `xfail` or `not_built`.

Two more views are in [traceability](traceability.md): every Given/When/Then **acceptance criterion** with the test that checks it (39 of 40 passed, 1 in part: the repeated search, see Q-11 in section 10), and the **frontend tests** per requirement (342 tests; every story has some, the weakest is US-07 with only the data call tested).

The NFRs with the measured value:

| NFR | Limit | Measured |
|---|---|---|
| NFR-01 | p95 under 500 ms over 100 requests | 3.3 to 3.4 ms (cached search) and 2.6 to 2.7 ms (`/stats`) in process; over HTTP p95 29 ms for the cached search with 10 users |
| NFR-02 | 401 without a valid token | 23 of 23 protected endpoints |
| NFR-03 | No plain password stored or returned | Passed |
| NFR-04 | Cached data or 503, never an unhandled 500 | Passed for IGDB, TMDB and OpenAI down |
| NFR-05 | At least 70% line coverage | 95.86% |

## 5. Coverage

Measured on 26.11.2026 after the merge of #234 (section 12). Details, the lowest files and the reasons are in [coverage](coverage.md).

| Backend package | Statements | Missed | Covered |
|---|---|---|---|
| `api` | 322 | 3 | 99.07% |
| `core` | 400 | 18 | 95.50% |
| `integrations` | 592 | 45 | 92.40% |
| `models` | 196 | 0 | 100.00% |
| `schemas` | 210 | 1 | 99.52% |
| `seed` | 201 | 6 | 97.01% |
| `services` | 912 | 47 | 94.85% |
| top level files | 137 | 3 | 97.81% |
| **Total** | **2970** | **123** | **95.86%** |

What is not covered: the error paths of the real OpenAI client (the tests use a fake), the duplicate check of `POST /media` (off by default), the SQLite fallback for a machine without PostgreSQL, and a few error outputs of command line tools. The dead list routes (`api/lists.py`, `services/list_service.py`) were removed by #344, which is why the total went up from 94.99%. With the live API tests the total was 95.10% (25.11.2026). Branch coverage is 87.36%. No file is left out of the measurement (checked by `tests/test_coverage_gate.py`).

Frontend: **34.54%** of lines (533 of 1543) and 34.09% of statements. The code that talks to the backend (`src/lib/server`, `src/lib/auth`, `src/proxy.ts`) is near 100%. The total is low because the animated background in `src/components/layout` (about half of the frontend lines) has no tests. The thresholds in `vitest.config.mts` sit a few points under the measured values.

## 6. Performance

Two kinds of evidence: the NFR-01 tests in process (section 4) and an HTTP load test of the production stack (`docker-compose.prod.yml`, Caddy with HTTPS, one uvicorn process), 30 seconds per run, on 25.11.2026. Details in [performance](performance.md).

| Users | Requests/s | p95, no CPU limit | p95, backend on 1 CPU | Errors |
|---|---|---|---|---|
| 5 | 536 | 12 ms | 92 ms | 0% |
| 10 | 495 | 31 ms | 197 ms | 0% |
| 20 | 542 | 60 ms | 486 ms | 0% |
| 40 | 508 | 177 ms | **1 109 ms** | 0% |
| 80 | **6** | **30 203 ms** | **30 118 ms** | **43%** / **52%** |

**Conclusion.** The limits (p95 under 500 ms, errors under 1%) hold up to 40 users without a CPU limit and up to 20 users with one CPU. One process serves about 500 requests/s here and about 120 with one CPU. At 80 users the API locked up in all three tries: the SQLAlchemy pool has 15 connections while FastAPI runs up to 40 requests at once, and the waiting threads time out after 30 seconds (`QueuePool limit of size 5 overflow 10 reached`). This limit is not hidden: it is the first next step in section 11. Render's free plan has much less CPU, so the knee there is lower.

**Re-run on the current code (26.11.2026).** After #234 was merged with `main`, the same script ran again on `c1fbcc9`, against one uvicorn process without Caddy on the 2 vCPU machine of section 3, which also ran the load generator:

| Users | Requests/s | p95 | Errors |
|---|---|---|---|
| 5 | 153 | 45 ms | 0% |
| 10 | 167 | 105 ms | 0% |
| 20 | 168 | 208 ms | 0% |
| 40 | 154 | **566 ms** | 0% |
| 80 | **5** | **30 082 ms** | **52%** |

The shape is the same as with one CPU on 25.11.2026: the limits hold up to 20 users, and the API locks up at 80 users with the same `QueuePool` error. The changes since `74f1f3a` did not change the performance. Raw results: `tests/performance/results/2026-11-26/`.

## 7. Security tests and penetration test

**Static and hardening tests** run in every CI run: secrets and dangerous calls in the code, the production settings (`ENABLE_DOCS=false`, no wildcard CORS, `--no-server-header`), the security headers on 200, 404, 422, 429 and 500 answers, forged and expired tokens, and the Content-Security-Policy of the frontend. CI also runs Gitleaks, Trivy, Semgrep, zizmor, Ruff security rules, ESLint security rules, `pip-audit` and `npm audit`.

**The penetration test** (23.11.2026, [report](penetration/README.md)) found 7 issues. Their status now:

| ID | Severity | Finding | Status | Pull request |
|---|---|---|---|---|
| F1 | High | Login limit could be bypassed with a fake `X-Forwarded-For` on Render | Fixed. The backend counts the address that the proxy writes, the frontend sends the browser address with a shared key | #340 (first step #329) |
| F2 | Medium | API documentation public on Render | Fixed | #260 |
| F3 | Medium | Any user could add titles with any image address | Fixed. `POST /media` off by default, `poster_url` only from the TMDB and IGDB image hosts, a Content-Security-Policy in the frontend | #328, #342 |
| F4 | Low | NUL bytes and a too large id gave 500 | Fixed | #341 |
| F5 | Low | A 422 repeated the rejected password | Fixed | #341 |
| F6 | Low | No body size limit, large values sent back | Fixed, 413 in the API and in Caddy | #341 |
| F7 | Info | `Server: uvicorn` | Fixed, with the missing browser headers | #343 |
| new | Low | JSON nested 3000 levels deep gave 500 | Fixed | #341 |

**Retest.** Locally after the fixes: 31 checks, 31 passed (25.11.2026, #348). On the production stack with Docker (26.11.2026, #351): through Caddy **31 of 31**, `GET /recommendations` with pgvector **7 of 7** (a known-vector check shows that the vector query really runs), and an **OWASP ZAP** API scan of all 30 operations with **0 failed and 118 passed** rules. Its 3 warnings were triaged: SQL injection is a false positive (the 429 and 422 answers differ, every query uses bound parameters), the "server error" is the expected 503 of the search without keys, and a missing `Cross-Origin-Resource-Policy` header is accepted as low. A browser check showed injected HTML as text, an `HttpOnly` login cookie, redirects when logged out, and a blocked image from another host.

**Not tested:** the hosted system on Render. It needs the agreement of the team and one harmless request each for F1 and the headers.

## 8. SonarQube

The CI job "SonarQube" is ready (#322) but is skipped while the secret `SONAR_TOKEN` is not set: SonarCloud is free only for public repositories, and this one is private. So the analysis ran with SonarQube Community Build 26.11 in Docker on 25.11.2026 (#349):

| Measure | First scan | After #349 |
|---|---|---|
| Quality gate | Passed | Passed |
| Bugs / vulnerabilities / hotspots | 2 / 1 (Blocker) / 0 | **0 / 0 / 0** |
| Code smells / duplication | 12 / 0.0% | **0 / 0.0%** |
| Ratings (reliability / security / maintainability) | C / E / A | **A / A / A** |
| Coverage of `backend/app` | 95.0% | 95.0% |
| Coverage of `frontend/src` (lines and conditions) | 41.6% | 41.6% |

The Blocker was a development password in an example comment, the two bugs an unreachable `raise` and a test assertion with the same expression on both sides (a false positive, rewritten). Screenshots of the dashboard and of the issue list, before and after the fixes, are in [sonarqube](sonarqube.md) (taken on 26.11.2026 from a new scan of both versions, with the same numbers). The steps to repeat the scan and to turn the CI job on are in the same document. #234 adds tests and documents only: `git diff main -- backend/app frontend/src` is empty, so the scan is valid for it too. Each finding of severity Blocker or High, with what was done, is in section 2 of the [mitigation plan](mitigation-plan.md): all of them are fixed.

**Other static analysis** (26.11.2026, [static analysis](static-analysis.md)): Ruff security rules, Bandit, `pip-audit`, `npm audit`, ESLint and the TypeScript compiler report **0 findings**. Radon gives an average complexity of A (3.14) and 8 functions of grade C (11 to 14), all with tests (Q-06).

## 9. TDD evidence

Details in [TDD evidence](tdd-evidence.md) (#345, #350).

- The requirement tests were written on 12.10.2026, before the code of 14 of the 15 user stories. Only US-01 came before its test.
- Five story groups were run again from the real commits: the tests failed on the code before the feature and passed with it.
- Nine fixes of the testing phase (F1, F3, F4, F5 with deep JSON, F6, F7, D10 and two SonarQube findings) each have a red `test:` commit and a green `fix:` commit, in the backend and, where they changed it, in the frontend.

## 10. Defects found by testing

| ID | What | Found by | Severity | Fix | Test |
|---|---|---|---|---|---|
| F1 | Login and register limits could be bypassed with a fake `X-Forwarded-For` on Render | Penetration test | High | #340 | `test_f1_render_rate_limit.py`, RATE-02 |
| F1b | The first F1 fix (#329) still let a direct call choose its address | New tests of #340 | High | #340 | `test_f1_us03_thirty_fake_forwarded_addresses_are_limited` |
| F2 | `/docs` public on Render | Penetration test (config review) | Medium | #260 | `test_docs_are_off_in_every_production_config` |
| F3 | Any image address in `poster_url`, open catalog writes | Penetration test | Medium | #328, #342 | `test_media_access.py`, `test_poster_url.py`, `proxy.test.ts` |
| F4 | NUL bytes and large ids gave 500 | Penetration test | Low | #341 | `test_malformed_input.py` |
| F5 | Password repeated in a 422 | Penetration test | Low | #341 | `test_f5_nfr03_a_rejected_password_is_not_repeated` |
| F6 | No body size limit | Penetration test | Low | #341 | `test_f6_*` |
| F7 | `Server` header, missing browser headers, no headers on a 500 | Penetration test, hardening tests | Info | #343 | `test_security_hardening.py`, `next-config.test.ts` |
| DJ | JSON nested 3000 levels deep gave 500 | Extra penetration run | Low | #341 | `test_us06_deeply_nested_json_*` |
| D10 | Duplicate list delete routes | Coverage and OpenAPI warning | Low | #344 | `test_route_registration.py` |
| P1 | API locks up at 80 users (database pool smaller than the thread pool) | Load test | Medium | Open, section 11 | `tests/performance/load_test.py` |
| C1 | `docker-compose.yml` published PostgreSQL on 5433, so the Compose smoke test fell back to SQLite | CI Docker Compose smoke test | Medium (CI) | #329 | the smoke test |
| C2 | A rate limit test failed when 11 bcrypt logins crossed a minute | CI backend tests (flaky) | Low (test) | #331 | the same tests with a fixed clock |
| C3 | The live IGDB test compared the exact case of "Life is Strange" | Manual CI run with real keys | Low (test) | #334 | `test_epic3_catalog_live.py` |
| C4 | TVMaze descriptions kept double spaces | New coverage tests | Low | #334 | `test_public_catalog_sources.py` |
| S1 | Unreachable `raise`, a password in a comment, a label without its field, a regex that could backtrack | SonarQube | Low to Blocker (comment) | #349 | `ChapterProgressCard.test.tsx`, `backend.test.ts` |
| Q-02 | `GET /recommendations` had no limit, p95 587 ms with 10 users (19.11.2026) | Load test of #234 | High | #258 | `test_us13_large_catalog_has_bounded_queries_and_response` |
| Q-03 | No rate limit on login | Static analysis and review of #234 | Medium | #236, #340 | `test_rate_limits.py` |
| Q-11 | The 41 catalog search edge case tests were replaced by a copy of the title details tests in `310010a` (#228) | Review of the acceptance criteria (#234) | Medium (test) | **Open**, mitigation plan | the old file passes 52 of 53 cases on today's code |
| T1 | After the merge of `main`, 5 tests of #234 failed: they expected the old answers of the review endpoints and a genre ranking that the embeddings replaced | Merge of `main` into #234 | Low (test) | #234 (`c1fbcc9`) | `test_epic5_review_and_recommendation_edge_cases.py`, with a new test of the rating threshold that fails when the threshold changes |

All quality findings, also the ones that are not defects (complexity, the SQLite fallback, frontend coverage), are in the [mitigation plan](mitigation-plan.md).

## 11. Residual risks and next steps

1. **Database pool (P1).** Give the SQLAlchemy pool at least as many connections as the thread pool, with a short `pool_timeout`, check the connection limit of the database plan, and run the load test again. Consider 2 to 4 uvicorn workers on a plan with more cores.
2. **Render not checked.** How the proxy of Render fills `X-Forwarded-For`, and which headers it adds, were not checked on the deployed service. One harmless request each, after the team agrees.
3. **SonarQube in CI.** A repository admin must make the repository public or choose a paid plan or a reachable server, then set `SONAR_TOKEN`, `SONAR_PROJECT_KEY` and `SONAR_ORGANIZATION`.
4. **Frontend coverage** is 34%. Tests for the layout and the dashboard would raise it.
5. **Small hardening:** `Cross-Origin-Resource-Policy` on the API, and HSTS raised from one day to one year after a week without problems.
6. **Live API tests** need the keys and run only on a manual CI run.
7. **Lost search tests (Q-11).** Put the old `test_epic3_catalog_search_edge_cases.py` back in a separate pull request, with the one test changed to expect 422.
8. **SQLite fallback (Q-04).** Allow it only with an explicit setting.
9. **Review (#293):** this report needs a review by a teammate who did not write it.

## 12. How to repeat

The backend and frontend numbers of sections 1, 4 and 5 (26.11.2026), as CI runs them, from the repository root with `docker compose up -d` running:

```bash
python -m pytest tests -v --cov=backend/app --cov-report=term-missing --cov-report=xml --cov-fail-under=90
```

```bash
cd backend && alembic upgrade head && alembic check
```

```bash
cd frontend && npm ci && npm run lint && npx tsc --noEmit && npm run test:coverage && npm run build
```

The traceability matrix (section 4):

```bash
python tests/tools/requirements_matrix.py
```

The load test of the production stack (section 6, 25.11.2026):

```bash
SECONDS_PER_RUN=30 tests/performance/run_stack.sh tests/performance/results/local 5 10 20 40 80
```

```bash
BACKEND_CPUS=1 SECONDS_PER_RUN=30 tests/performance/run_stack.sh tests/performance/results/local-1-cpu 5 10 20 40 80
```

The penetration retest on the production stack with pgvector and ZAP (section 7, 26.11.2026, #351):

```bash
tests/pentest/run_stack.sh
```

The penetration script against a local API (section 7, see the start options in the [report](penetration/README.md)):

```bash
PENTEST_SECRET=<SECRET_KEY of the local API> python tests/pentest/run_pentest.py --base-url http://127.0.0.1:8000 --out results.json
```

The re-run of the load test on the current code (section 6, 26.11.2026), against a local API started with `RATE_LIMIT_ENABLED=false` and `ALLOW_MEDIA_CREATE=true` (test settings only):

```bash
for users in 5 10 20 40 80; do python tests/performance/load_test.py --base-url http://127.0.0.1:8000 --users $users --seconds 30 --json users-$users.json; done
```

The static analysis (section 8): the commands are in section 4 of [static analysis](static-analysis.md).

SonarQube (section 8): the steps are in [sonarqube](sonarqube.md) (#349). The red and green runs (section 9): the commands are in section 6 of the [TDD evidence](tdd-evidence.md).
