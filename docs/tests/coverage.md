# Code coverage

Issue #297. These numbers feed the Software Testing Report (#296). The first numbers were measured on 2026-11-25. They were measured again on **2026-11-26**, after #234 was merged with `main` (commit `c1fbcc9` of `test_work`), so that every number of the test documents comes from the same code. The commands are in section 5.

## 1. Summary

| Part | Lines covered | Gate in CI | Where the gate is |
|---|---|---|---|
| Backend (`backend/app`) | **95.86%** (2847 of 2970 statements), 87.36% of branches | 90% | `--cov-fail-under=90` in `.github/workflows/ci.yml` |
| Backend with the live API tests | **95.10%** (2026-11-25, before the duplicate list routes were removed) | none (manual run only) | job summary of a manual CI run |
| Frontend (`frontend/src`) | **34.54%** of lines (533 of 1543), 34.09% of statements, 62.85% of functions, 46.65% of branches | lines 25%, statements 25%, functions 40%, branches 35% | `coverage.thresholds` in `frontend/vitest.config.mts` |

Before #297 the backend measured **88.65%** with a gate of 70%. New tests for the keyless catalog sources and for the embeddings command raised it to 94.96% (2026-11-25). The removal of the dead list routes (#344) and the new tests of #234 raised it to 95.86%. No file was excluded to raise the number.

NFR-05 asks for at least 70%. The CI gate is stricter, about 5 points under the measured value, so the coverage cannot fall without notice. Raise the gates when tests are added. Never lower them to make a change pass.

## 2. Backend per package

2026-11-26, the same command as CI (section 5): **1106 passed, 0 failed, 4 skipped** (the 3 live API tests without keys, and 1 test that runs only when Redis is down).

| Package | Statements | Missed | Covered |
|---|---|---|---|
| `api` | 322 | 3 | 99.07% |
| `core` | 400 | 18 | 95.50% |
| `integrations` | 592 | 45 | 92.40% |
| `models` | 196 | 0 | 100.00% |
| `schemas` | 210 | 1 | 99.52% |
| `seed` | 201 | 6 | 97.01% |
| `services` | 912 | 47 | 94.85% |
| top level files (`main.py`, `embeddings.py`, `sync.py`, ...) | 137 | 3 | 97.81% |
| **Total** | **2970** | **123** | **95.86%** |

### What is not covered and why

| File | Covered | Reason |
|---|---|---|
| `integrations/openai_client.py` | 78.38% | Error paths of the real OpenAI client (timeouts, bad answers). The tests use the fake client in `tests/requirements/fake_openai.py` |
| `services/media_service.py` | 80.00% | The duplicate check of `POST /media`, which is off by default since #218 |
| `core/errors.py` | 85.71% | Two branches of `_safe_text` (a NaN or Infinity, and a value that is not text or a number, in a validation error) and one line of the handler for an outside service error |
| `seed/__main__.py` | 86.49% | Error output of the command line tool |
| `integrations/genres.py` | 86.67% | Wrong data in a genre list: a name that is not text, an empty name, a name that is too long, more genres than the maximum |
| `services/recommendations_service.py` | 88.24% | The early return when the vector query already fills the page, and the fallback after a failed vector query |
| `core/database.py` | 90.91% | The SQLite fallback for a local machine without PostgreSQL. CI always has PostgreSQL |

`services/list_service.py` and `api/lists.py` (35% and 60% on 2026-11-25) are gone: #344 removed the dead copies.

### The live API tests

A manual run of the CI (`workflow_dispatch`) also runs `tests/requirements/test_epic3_catalog_live.py` against the real IGDB and TMDB, with `--cov-append`. On 2026-11-25 (run 45578219029) the total went from 95.06% to 95.10%. The difference is small, because the fake HTTP tests already run almost all of the client code.

The same run showed that the live IGDB test failed: IGDB now writes the name as "Life Is Strange". The search worked, only the test compared the exact case. The test now compares without case and prints the titles when it fails.

## 3. Frontend per folder

2026-11-26, `npm run test:coverage` (Vitest 5.1.0 with `@vitest/coverage-v8`, a development tool only) on Node 24.22.3: **44 test files, 342 tests passed**.

| Folder | Lines | Lines covered | Branches covered |
|---|---|---|---|
| `src/app` | 226 | 63.7% | 59.6% |
| `src/components/auth` | 11 | 100.0% | 100.0% |
| `src/components/layout` | 819 | 5.0% | 8.6% |
| `src/components/library` | 3 | 100.0% | 100.0% |
| `src/components/lists` | 15 | 60.0% | 50.0% |
| `src/components/search` | 8 | 100.0% | 100.0% |
| `src/components/states` | 15 | 100.0% | 100.0% |
| `src/components/title` | 58 | 100.0% | 88.8% |
| `src/context` | 7 | 85.7% | 50.0% |
| `src/lib` | 18 | 94.4% | 100.0% |
| `src/lib/actions` | 200 | 29.5% | 23.4% |
| `src/lib/auth` | 15 | 100.0% | 100.0% |
| `src/lib/server` | 128 | 99.2% | 97.3% |
| `src/proxy.ts` | 20 | 100.0% | 81.8% |

The total is low because `src/components/layout` holds the animated background and the dashboard, more than half of all frontend lines, and no test renders them. The friends page (`src/components/social`, `src/lib/services`) was removed by #333. The code that talks to the backend (`src/lib/server`, `src/lib/auth`, `src/proxy.ts`) is close to 100%. Which frontend tests belong to which requirement is in section 4 of [traceability](traceability.md). The thresholds are a few points under the measured values. They are not set higher than what the tests reach.

## 4. In every CI run

- The backend job writes "Backend coverage: N% of lines (gate 90%)" to the job summary and uploads `coverage.xml` and the HTML report (`htmlcov/`) as the artifact `backend-coverage`.
- The frontend job writes the four frontend numbers to the job summary and uploads the HTML report as the artifact `frontend-coverage`.
- SonarQube reads the same `coverage.xml` (#299).

## 5. How to repeat

Environment of the numbers of 2026-11-26: a Linux machine (Ubuntu 24.04, Intel Xeon, 2 cores, 7 GB), Python 3.15.0b4 with the locked packages of `backend/requirements.txt` and `tests/requirements-test.txt` (pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3), PostgreSQL 16.15 with pgvector 0.6.0, Redis 7.0.15, Node 24.22.3. The machine could not pull Docker images, so PostgreSQL and Redis ran without Docker. The coverage does not depend on the speed of the machine.

Environment of the numbers of 2026-11-25: Apple M3 Pro, 11 cores, macOS 27.2.1, Docker Desktop with 11 CPUs and 7.7 GB. Backend in `python:3.15-slim` (Python 3.15.2), PostgreSQL 16.16 with pgvector 0.8.7 and Redis 7.4.12 from `docker-compose.yml`. Frontend in `node:24-slim` (Node 24.22.3). CI runs on GitHub's `ubuntu-latest` and gave 95.06% for the same code.

Backend, from the repository root, with PostgreSQL and Redis running (`docker compose up -d`):

```bash
python -m pytest tests -v --cov=backend/app --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=90
```

The HTML report is in `htmlcov/index.html`.

Backend with the live APIs (needs real keys in `backend/.env`):

```bash
RUN_LIVE_API_TESTS=1 python -m pytest tests/requirements/test_epic3_catalog_live.py -v --cov=backend/app --cov-append
```

Frontend, from `frontend/`:

```bash
npm run test:coverage
```

The HTML report is in `frontend/coverage/index.html`.
