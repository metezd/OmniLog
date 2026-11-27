# Code coverage

Issue #297. These numbers feed the Software Testing Report (#296). Every number below comes from a command that was run on 2026-11-27 against `main` at `853c440` (#381). The commands are in section 5.

Since #367 the backend measure covers `backend/app` **and** `scripts/` (`--cov=backend/app --cov=scripts`), so it is not the same measure as the 94.96% of 2026-11-25, which counted `backend/app` only.

## 1. Summary

| Part | Lines covered | Gate in CI | Where the gate is |
|---|---|---|---|
| Backend (`backend/app` and `scripts/`) | **96.04%** (3469 of 3612 statements) | 90% | `--cov-fail-under=90` in `.github/workflows/ci.yml` |
| Backend with the live API tests | **95.10%** (2026-11-25, `backend/app` only) | none (manual run only) | job summary of a manual CI run |
| Frontend (`frontend/src`) | **36.51%** of lines (582 of 1594), 36.07% of statements, 64.72% of functions, 48.78% of branches | lines 25%, statements 25%, functions 40%, branches 35% | `coverage.thresholds` in `frontend/vitest.config.mts` |

Before this issue the backend measured **88.65%** with a gate of 70%. New tests for the keyless catalog sources and for the embeddings command raised it to 94.96%. No file was excluded to raise the number.

NFR-05 asks for at least 70%. The CI gate is now stricter, about 6 points under the measured value, so the coverage cannot fall without notice. Raise the gates when tests are added. Never lower them to make a change pass.

## 2. Backend per package

Measured in Docker, the same way as CI (section 5). **1479 passed, 4 skipped**, 0 failed.

| Package | Statements | Missed | Covered |
|---|---|---|---|
| `api` | 341 | 3 | 99.12% |
| `core` | 570 | 26 | 95.44% |
| `integrations` | 703 | 48 | 93.17% |
| `models` | 201 | 0 | 100.00% |
| `schemas` | 222 | 1 | 99.55% |
| `seed` | 201 | 6 | 97.01% |
| `services` | 991 | 50 | 94.95% |
| top level files (`main.py`, `embeddings.py`, `sync.py`, ...) | 147 | 3 | 97.96% |
| `scripts/` (`import_lists.py`) | 236 | 6 | 97.46% |
| **Total** | **3612** | **143** | **96.04%** |

### What is not covered and why

| File | Covered | Reason |
|---|---|---|
| `services/media_service.py` | 80.00% | The duplicate check of `POST /media`, which is off by default since #218 |
| `integrations/openai_client.py` | 83.51% | Error paths of the real OpenAI client (timeouts, bad answers). The tests use the fake client in `tests/requirements/fake_openai.py` |
| `core/errors.py` | 85.71% | `_safe_text` for a NaN or a value that is neither text nor a number in an error location, and the 503 handler of `ExternalServiceError`, which no test reaches because the services catch the error first |
| `seed/__main__.py` | 86.49% | Error output of the command line tool |
| `integrations/genres.py` | 86.67% | A genre name that is not text, empty after cleaning, or longer than the column. The fakes send only normal names |
| `services/recommendations_service.py` | 88.24% | A full page of vector results, and the fallback when the vector query itself fails |
| `core/rate_limit.py` | 88.54% | The in-process store when it holds 10 000 keys, and Redis failing in the middle of a count or a read |
| `services/catalog_service.py` | 91.79% | A search that fails with nothing saved, a second insert race of the same title, and broken season data in the cache |

The dead list routes (`api/lists.py`, `services/list_service.py`) were removed in #344, and the SQLite fallback of `core/database.py` in #371, so they are gone from the list.

### The live API tests

A manual run of the CI (`workflow_dispatch`) also runs `tests/requirements/test_epic3_catalog_live.py` against the real IGDB and TMDB, with `--cov-append`. On 2026-11-25 (run 45578219029) the total went from 95.06% to 95.10%. The difference is small, because the fake HTTP tests already run almost all of the client code.

The same run showed that the live IGDB test failed: IGDB now writes the name as "Life Is Strange". The search worked, only the test compared the exact case. The test now compares without case and prints the titles when it fails.

## 3. Frontend per folder

Measured with `npm run test:coverage` (Vitest 5.1.0 with `@vitest/coverage-v8`, a development tool only) on Node 26, the version of `frontend/Dockerfile` (#379). **48 test files, 375 tests passed.**

| Folder | Lines | Lines covered | Branches covered |
|---|---|---|---|
| `src/app` | 229 | 62.9% | 60.2% |
| `src/components/auth` | 11 | 100.0% | 100.0% |
| `src/components/common` | 8 | 100.0% | 100.0% |
| `src/components/layout` | 819 | 5.1% | 9.1% |
| `src/components/library` | 3 | 100.0% | 100.0% |
| `src/components/lists` | 15 | 60.0% | 50.0% |
| `src/components/search` | 8 | 100.0% | 100.0% |
| `src/components/states` | 15 | 100.0% | 100.0% |
| `src/components/title` | 75 | 100.0% | 93.6% |
| `src/context` | 7 | 85.7% | 50.0% |
| `src/lib` | 26 | 96.2% | 100.0% |
| `src/lib/actions` | 206 | 31.6% | 24.8% |
| `src/lib/auth` | 15 | 100.0% | 100.0% |
| `src/lib/server` | 137 | 99.3% | 97.4% |
| `src/proxy.ts` | 20 | 100.0% | 81.8% |

The total is low because `src/components/layout` holds the animated background and the dashboard, half of all frontend lines, and no test renders them. The friends page (`src/components/social`) and the unused `src/lib/services` were removed, so they are not in the list any more. The code that talks to the backend (`src/lib/server`, `src/lib/auth`, `src/proxy.ts`) is close to 100%. The thresholds are a few points under the measured values, as the issue asks. They are not set higher than what the tests reach.

## 4. In every CI run

- The backend job writes "Backend coverage: N% of lines (gate 90%)" to the job summary and uploads `coverage.xml` and the HTML report (`htmlcov/`) as the artifact `backend-coverage`.
- The frontend job writes the four frontend numbers to the job summary and uploads the HTML report as the artifact `frontend-coverage`.
- SonarQube reads the same `coverage.xml` (#299).

## 5. How to repeat

Environment of the numbers above (2026-11-27, `853c440`): Apple M3 Pro, 11 cores, macOS 27.2.1, Docker Desktop. Backend in `python:3.15-slim-bookworm` (Python 3.15.2, pytest 9.2.0), PostgreSQL 16 with pgvector (`pgvector/pgvector:pg16`) and Redis 7.4. Frontend in `node:26-alpine` (Node 26.13.1, Vitest 5.1.0). CI runs on GitHub's `ubuntu-latest`; its job summary gives the number of every run.

Backend, from the repository root, with PostgreSQL and Redis running (`docker compose up -d`):

```bash
python -m pytest tests -v --cov=backend/app --cov=scripts --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=90
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
