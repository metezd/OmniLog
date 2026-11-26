# Changelog

All notable changes to this project are written in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions follow [Semantic Versioning](https://semver.org). The rules for versions and releases are in [CONTRIBUTING.md](CONTRIBUTING.md#versioning-and-releases).

## [Unreleased]

### Added

- `scripts/import_lists.py`, which imports a movie list from a CSV file or a Letterboxd export through the API, and the coverage of `scripts/` in CI and SonarQube (#336).
- `Cache-Control: private, max-age=300, stale-while-revalidate=600` on successful catalog search and title details answers, and a warm-up ping from the login and register pages that wakes a sleeping backend, at most once a minute (#250).
- `docs/design/render-pdf.sh`, which renders the Software Design Report to PDF with pandoc and Chromium in Docker (#295).
- The check "AI disclosure" on pull requests: the section "AI assistance" must have one ticked box, and the label `ai-assisted` must be set when AI helped (#309).
- An outgoing limit for IGDB: the new setting `IGDB_MAX_REQUESTS_PER_SECOND` (default 3, `0` turns it off) spaces the calls of a process, retries included, so IGDB does not answer 429. A call that would wait more than 5 seconds fails at once and the saved copy is used.
- The manual sync loads the details of many games with one IGDB query for every 100 games (`where id = (...)`) instead of one request per game. It falls back to one request per game when the batch fails.
- Penetration retest after the fixes, with three new checks and a browser check of the frontend (#306).
- The Software Testing Report (`docs/tests/software-testing-report.md`), which ties the tests, coverage, performance, security, SonarQube and TDD results together (#296).
- The code review log (`docs/code-review-log.md`) with all merged pull requests and their reviews, and a review rota in `CONTRIBUTING.md` (#293).
- HTTP load test (`tests/performance/load_test.py`), a script that runs it against the production stack (`tests/performance/run_stack.sh`) and the manual workflow "Performance". The results and the limit of the server are in `docs/tests/performance.md` (#298).
- A CI check that every user story and non-functional requirement is named by tests (`tests/test_requirements_traceability.py`), the matrix in `docs/tests/traceability.md`, and new tests for US-01 and NFR-05 (#300).

### Changed

- The AI usage page, the notes of Sidar Ürey and the register of AI mistakes show the work up to 2026-11-26: eight new caught mistakes (17 in all), the AI disclosure check and the current controls (#308, #310).
- `.github/CODEOWNERS` gives each of the six members the area of their role in the Charter, and a test checks that every path in it exists (#293).
- The design report PDF and the architecture diagrams show the current stack (Node 26, Python 3.15, bcrypt, migrations up to 0013, the OpenAI API in use), and the docs give the real coverage gate of CI, 90% (#295).
- The backend coverage gate in CI is 90% instead of 70%, about 5 points under the measured 94.96%. The frontend has coverage with measured thresholds (`npm run test:coverage`). Every CI run writes the numbers to the job summary and keeps the HTML reports. The new tests also found double spaces in TVMaze descriptions, which are fixed (#297).

### Fixed

- A local PostgreSQL that is not running no longer makes the API switch to an empty SQLite file that answered "ready" and then 500. The API now stops at the start with a clear message, and the SQLite code is removed (#371).
- A local SonarQube scan found 2 bugs, 1 vulnerability and 12 code smells. All are fixed (an unreachable `raise`, a password in an example comment, a form label without its field, a regular expression that could backtrack). The CI scan now also reads the frontend coverage. The results are in `docs/tests/sonarqube.md` (#299).
- The login and register limits on Render count the browser address again, not the address of the frontend for everybody. The new setting `FORWARDED_TRUSTED_HOPS` reads it from the right end of `X-Forwarded-For`, so a client cannot choose it by writing the left end (#251).
- `docker-compose.yml` publishes PostgreSQL on `localhost:5432` again, which CI, `backend/.env.example` and the docs use. It was moved to `5433`, so the Docker Compose smoke test found no database, fell back to SQLite and failed on the migrations. `POSTGRES_PORT` now picks another port when 5432 is taken.
- An empty `REDIS_URL` no longer stops the cache and the rate limits with an error. The in-process cache is used instead (#251).
- `render.yaml` sets the health check path `/api/health` of the frontend service, as `docs/deployment.md` says. Before, Render had no health check for `omnilog-web` (#292).

### Removed

- The unused frontend packages `axios`, `react-hook-form` and `recharts`, and the unused image `frontend/public/kagan.jpg` (#295).

### Security

- The poster proxy `GET /api/poster` no longer follows a redirect of the poster host, so a redirect cannot lead the server to another address. More tests for the proxy (#332).
- Penetration finding F7 is fixed and the missing headers are added: no `Server` or `X-Powered-By` header, `X-Frame-Options`, `Content-Security-Policy` and `Permissions-Policy` from the API on every answer (also on a 500), the browser headers from the frontend, and HSTS and the same headers from Caddy (#304).
- Penetration finding F3 is fixed: the update schema of a title checks `poster_url` too, and the frontend sends a Content-Security-Policy with a nonce for scripts and only the app, `data:`, `blob:` and the TMDB and IGDB image hosts for images (#303).
- Penetration finding F1 is fixed: on Render the login and register limits count the right-most address of `X-Forwarded-For`, which the proxy writes, and the browser address that the frontend sends with the new shared key `FRONTEND_PROXY_SECRET`. A fake first address no longer resets the limit (#301).
- Penetration findings F4, F5 and F6 are fixed: NUL bytes in any text and a too large `external_api_id` give 422 instead of 500, a 422 no longer repeats the rejected value (also no 500 for deeply nested JSON), and a body over 1 MB gets 413 from the API and from Caddy (#302).
- `POST /media` is off by default and answers 404. The new setting `ALLOW_MEDIA_CREATE` turns it on, and then `poster_url` must be an `https` address on `image.tmdb.org` or `images.igdb.com`. `GET /media/{id}` now needs a login (#218).

## [0.8.0] - 2026-11-24

### Added

- Authentication with register, login and JWT, and `GET /auth/me` (US-02, US-03).
- Catalog and library: add, rate and update titles, search in IGDB and TMDB with a Redis cache, title details with description and genres (US-04, US-05, US-08, US-09).
- Custom lists and the activity diary, with `DELETE` endpoints for library entries, list items and lists (US-06, US-07).
- Episodic logging: chapter ratings, playtime and decisions, with the seed command `python -m app.seed` (US-10 to US-12).
- Personal statistics with a Redis cache (US-15).
- Reviews with spoiler detection (US-14) and personalized, embedding-based recommendations with a popularity fallback (US-13).
- The manual sync command `python -m app.sync` and the embeddings command `python -m app.embeddings`.
- Rate limits on login, register, search and review.
- Next.js frontend that calls the backend from its server code, with the login token in an `httpOnly` cookie.
- Production Docker stack with PostgreSQL (pgvector), Redis, the backend, the frontend and a Caddy proxy with HTTPS, and a Render blueprint (`render.yaml`).
- CI for the backend, the frontend and the Docker stack, with a coverage gate of 70%, dependency audits and a check of the lock files.
- Security checks: Gitleaks, Trivy, zizmor, Ruff security rules, ESLint security rules, static security tests and a report-only Semgrep job.
- Dependabot for Python, npm, GitHub Actions and Docker.
- Project documents: Charter, requirements, analysis, design and plan.
- The API documentation is now off on Render too (`ENABLE_DOCS=false`).
- Local penetration test with its report, TDD evidence and AI usage notes (#252).
- AI usage notes of Sidar Ürey (`docs/ai-usage/sidar-urey.md`, #315).
- The evidence of AI use beyond autocomplete: agent pull requests, Copilot review results, instruction files and a review session (`docs/ai-usage/evidence.md`, #311).
- Contribution rules with a branching model, versioning, code review, a pull request template, issue templates and CODEOWNERS.
- The AI assistance convention: a section in the pull request template, the label `ai-assisted`, the commit trailer `Assisted-by:` and the rule that the author explains every line (#309).
- A release workflow that creates a GitHub Release from a version tag, and a ruleset that protects `main`.
- Health endpoints `GET /health` and `GET /health/ready` for the Render health check.
- Security headers on every API response and the `ENABLE_DOCS` switch for the API documentation.
- Paging with `limit` and `offset` on the diary, the library and the lists, and indexes on `diary_entries` (migration 0013).
- Frontend: the S-01 landing page with the ASCII background and the liquid-glass style, the statistics screen and its tests. The friends page is marked as a demo with sample data (#123, #124).

### Changed

- The version of the backend, the frontend package and the Git tags is now one number (`0.8.0`), and a test checks that the files agree.
- Render deploys `main` only after the GitHub checks pass.
- The Dependabot auto-merge workflow uses rebase, so it follows the linear history rule.
- `GET /stats` caps the playtime histogram at 100+ hours and 21 buckets (#216).
- The database URL is normalized for PostgreSQL, and the connection falls back cleanly for local development.
- The backend dependencies are pinned in lock files, and `bcrypt` replaces `passlib`.
- Python 3.14 in the GitHub workflows and 3.15.0 in `render.yaml`.

### Fixed

- A review is saved before the spoiler check runs, and the spoiler fields stay empty when the check fails.
- Render: the Redis service uses the type `keyvalue`, the backend starts with proxy headers and the frontend uses Node 26.

### Security

- `python-jose` is replaced by PyJWT, and access tokens must carry the `exp` and `sub` claims (the `iat` claim is added).
- A dependency audit (`pip-audit`) runs in CI.

### Removed

- The old root `env.example` (its `SECRET_KEY` value was too short for the backend, and `backend/.env.example` replaces it) and the unused starter images in `frontend/public`.
