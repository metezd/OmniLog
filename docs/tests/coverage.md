# Code coverage

Issue #297. These numbers feed the Software Testing Report (#296). Every number below comes from a command that was run on 2026-11-25. The commands are in section 5.

## 1. Summary

| Part | Lines covered | Gate in CI | Where the gate is |
|---|---|---|---|
| Backend (`backend/app`) | **94.96%** (2769 of 2916 statements) | 90% | `--cov-fail-under=90` in `.github/workflows/ci.yml` |
| Backend with the live API tests | **95.10%** | none (manual run only) | job summary of a manual CI run |
| Frontend (`frontend/src`) | **31.33%** of lines (508 of 1621), 30.88% of statements, 51.73% of functions, 42.71% of branches | lines 25%, statements 25%, functions 40%, branches 35% | `coverage.thresholds` in `frontend/vitest.config.mts` |

Before this issue the backend measured **88.65%** with a gate of 70%. New tests for the keyless catalog sources and for the embeddings command raised it to 94.96%. No file was excluded to raise the number.

NFR-05 asks for at least 70%. The CI gate is now stricter, about 5 points under the measured value, so the coverage cannot fall without notice. Raise the gates when tests are added. Never lower them to make a change pass.

## 2. Backend per package

Measured in Docker, the same way as CI (section 5). 1009 passed, 4 skipped.

| Package | Statements | Missed | Covered |
|---|---|---|---|
| `api` | 331 | 12 | 96.37% |
| `core` | 308 | 17 | 94.48% |
| `integrations` | 592 | 45 | 92.40% |
| `models` | 196 | 0 | 100.00% |
| `schemas` | 209 | 1 | 99.52% |
| `seed` | 201 | 6 | 97.01% |
| `services` | 935 | 63 | 93.26% |
| top level files (`main.py`, `embeddings.py`, `sync.py`, ...) | 144 | 3 | 97.92% |
| **Total** | **2916** | **147** | **94.96%** |

### What is not covered and why

| File | Covered | Reason |
|---|---|---|
| `services/list_service.py` | 34.78% | Dead code. `journal.py` registers the same routes first, so these never run. #305 removes them |
| `api/lists.py` | 60.00% | The same dead routes (#305) |
| `integrations/openai_client.py` | 78.38% | Error paths of the real OpenAI client (timeouts, bad answers). The tests use the fake client in `tests/requirements/fake_openai.py` |
| `services/media_service.py` | 80.00% | The duplicate check of `POST /media`, which is off by default since #218 |
| `core/database.py` | 81.82% | The SQLite fallback for a local machine without PostgreSQL. CI always has PostgreSQL |
| `seed/__main__.py` | 86.49% | Error output of the command line tool |
| `integrations/igdb.py` | 91.53% | Error answers of the Twitch sign-in. Only the live IGDB gives them |

### The live API tests

A manual run of the CI (`workflow_dispatch`) also runs `tests/requirements/test_epic3_catalog_live.py` against the real IGDB and TMDB, with `--cov-append`. On 2026-11-25 (run 45578219029) the total went from 95.06% to 95.10%. The difference is small, because the fake HTTP tests already run almost all of the client code.

The same run showed that the live IGDB test failed: IGDB now writes the name as "Life Is Strange". The search worked, only the test compared the exact case. The test now compares without case and prints the titles when it fails.

## 3. Frontend per folder

Measured with `npm run test:coverage` (Vitest 5.1.0 with `@vitest/coverage-v8`, a development tool only) on Node 24. 42 test files, 315 tests passed.

| Folder | Lines | Lines covered | Branches covered |
|---|---|---|---|
| `src/app` | 232 | 61.6% | 58.5% |
| `src/components/auth` | 11 | 100.0% | 100.0% |
| `src/components/layout` | 819 | 5.0% | 8.6% |
| `src/components/library` | 3 | 100.0% | 100.0% |
| `src/components/lists` | 15 | 60.0% | 50.0% |
| `src/components/search` | 8 | 100.0% | 100.0% |
| `src/components/social` | 61 | 0.0% | 0.0% |
| `src/components/states` | 15 | 100.0% | 100.0% |
| `src/components/title` | 58 | 100.0% | 88.8% |
| `src/context` | 7 | 85.7% | 50.0% |
| `src/lib` | 18 | 94.4% | 100.0% |
| `src/lib/actions` | 200 | 29.5% | 23.4% |
| `src/lib/auth` | 15 | 100.0% | 100.0% |
| `src/lib/server` | 120 | 99.2% | 97.1% |
| `src/lib/services` | 35 | 0.0% | 0.0% |
| `src/proxy.ts` | 4 | 100.0% | 100.0% |

The total is low for two reasons. `src/components/layout` holds the animated background and the dashboard, half of all frontend lines, and no test renders them. `src/components/social` is the friends page, which still shows sample data. The code that talks to the backend (`src/lib/server`, `src/lib/auth`, `src/proxy.ts`) is close to 100%. The thresholds are a few points under the measured values, as the issue asks. They are not set higher than what the tests reach.

## 4. In every CI run

- The backend job writes "Backend coverage: N% of lines (gate 90%)" to the job summary and uploads `coverage.xml` and the HTML report (`htmlcov/`) as the artifact `backend-coverage`.
- The frontend job writes the four frontend numbers to the job summary and uploads the HTML report as the artifact `frontend-coverage`.
- SonarQube reads the same `coverage.xml` (#299).

## 5. How to repeat

Environment of the numbers above: Apple M3 Pro, 11 cores, macOS 27.2.1, Docker Desktop with 11 CPUs and 7.7 GB. Backend in `python:3.15-slim` (Python 3.15.2, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3), PostgreSQL 16.16 with pgvector 0.8.7 and Redis 7.4.12 from `docker-compose.yml`. Frontend in `node:24-slim` (Node 24.22.3). CI runs on GitHub's `ubuntu-latest` and gave 95.06% for the same code.

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
