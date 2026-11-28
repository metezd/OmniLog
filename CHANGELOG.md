# Changelog

All notable changes to this project are written in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions follow [Semantic Versioning](https://semver.org). The rules for versions and releases are in [CONTRIBUTING.md](CONTRIBUTING.md#versioning-and-releases).

## [Unreleased]

### Added

- A user can take back what they logged: remove the review, the rating of a chapter, the newest playtime entry of a chapter or of a whole title, and a choice, with a button on the title page for each. Before, the only way was to remove the whole title from the library (#427).
- `GET /library/{entry_id}/chapters` returns the progress of every chapter of a library entry (rating, playtime, choices) in one answer, and the title page uses it. Before, the page sent one request per chapter: 300 requests and 1800 queries for a series with 300 episodes (#419).
- The setting `SPOILER_PROVIDER` (`openai` by default, or `local`): `local` checks reviews with the local patterns and keeps their text inside the system, also when `OPENAI_API_KEY` is set for the embeddings. `docs/deployment.md` has a new section 4.1 that lists what is sent to IGDB, TMDB and OpenAI, and the README says that an empty `OPENAI_API_KEY` keeps all review text inside the system (#397).
- `Strict-Transport-Security: max-age=31536000` from the API itself when the request came over HTTPS (`X-Forwarded-Proto: https`), for the Render setup. Behind Caddy the API proxy drops it and sends its own, so the header is not sent twice (#394).
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
- A second register limit per browser address, `RATE_LIMIT_REGISTER_DAY` (default `20/day`), besides `5/hour`, so that a search for registered emails gets 20 answers a day and not 120. The decision to keep `409` for a taken name and its reason are in `docs/deployment.md`, section 9.2 (#395).

### Changed

- The deployment guide, `docs/tests/sonarqube.md` and the Software Testing Report no longer say that embeddings are not built, that a friends page shows sample data, or that the SonarQube job waits for a token. The report gives the current SonarCloud state of `main` (#424).
- `/health/ready` reports `"cache": "not_configured"` when `REDIS_URL` is empty, and `"down"` only when Redis is set but does not answer. The start of the API logs which one it is (host and port, never the password), so the reason of `cache: down` on Render can be seen (#422).
- The Supabase database is migrated by the last job of `ci.yml`, only on `main` and only after the security lint, the backend tests, the Docker Compose smoke test and the frontend checks passed. The separate workflow `db-migrate.yml` started at the same moment as CI, so a migration could reach production with code whose tests failed (#421).
- `GET /recommendations` computes the taste vector with `avg()` on the `vector` column in PostgreSQL (pgvector 0.5 or newer) instead of reading every liked embedding into Python, and has a per-user limit, `RATE_LIMIT_RECOMMENDATIONS` (default `30/minute`) (#396).
- `POST /auth/register` hashes the password before it checks whether the username or email is taken, so a taken name answers in the same time as a free one and only the status shows it (#395).
- Tighter HTTP defaults of the API (#394): every answer without its own `Cache-Control` (library, lists, diary, statistics, errors) gets `no-store`, and the catalog keeps its own header. `ENABLE_DOCS` defaults to `false` (`backend/.env.example` turns it on for development). CORS runs without credentials and allows only the methods of the API and the headers `Authorization` and `Content-Type`.
- The frontend checks in CI run on the Node.js version of `frontend/Dockerfile` (26 instead of 24), and a test keeps `render.yaml`, the Dockerfiles and CI in line (#379). Render stays on Python 3.15.0, the minor version of the image, because 3.15.2 stopped the build of `omnilog-api`.
- `.github/rulesets/main.json`, `CONTRIBUTING.md` and the Dependabot workflow follow the live ruleset of `main`: merge commits instead of rebase, no linear history rule, and AI disclosure as a required check. A test keeps them in line, and the ruleset is updated with PUT instead of POST (#369).
- The AI usage page, the notes of Sidar Ürey and the register of AI mistakes show the work up to 2026-11-26: eight new caught mistakes (17 in all), the AI disclosure check and the current controls (#308, #310).
- `.github/CODEOWNERS` gives each of the six members the area of their role in the Charter, and a test checks that every path in it exists (#293).
- The design report PDF and the architecture diagrams show the current stack (Node 26, Python 3.15, bcrypt, migrations up to 0013, the OpenAI API in use), and the docs give the real coverage gate of CI, 90% (#295).
- The backend coverage gate in CI is 90% instead of 70%, about 5 points under the measured 94.96%. The frontend has coverage with measured thresholds (`npm run test:coverage`). Every CI run writes the numbers to the job summary and keeps the HTML reports. The new tests also found double spaces in TVMaze descriptions, which are fixed (#297).

### Fixed

- The animated background follows the operating system setting "reduce motion": it draws one still frame instead of a constant animation, and it follows a change of the setting. Its debug line (`omnilog.ascii | ... | chars N`) is shown only in development (#429).
- The frontend no longer stops at the first page: the library and the lists are read page by page, the title page asks only for its own library entry (new filter `GET /library?media_item_id=`), and the diary has links to older and newer events. Before, a user with more than 200 titles saw only 200, and a later title offered "Add to library" again, which answered 409 (#418).
- A full connection pool answers 503 with `Retry-After` after `DB_POOL_TIMEOUT` (default 10 seconds) instead of 500 after 30 seconds. The pool (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`) and a `statement_timeout` for the API (`DB_STATEMENT_TIMEOUT_MS`, default 15 seconds) are settings, and the migrations run without the timeout (#432).
- An `offset` above 2147483647 on `GET /diary`, `/library` and `/lists` answers 422 instead of 500. PostgreSQL could not take a value above 2^63 (#420).
- `omnilog-api` on Render uses the Supabase database. `render.yaml` no longer has the Render database `omnilog-db`, which is not used any more, and `DATABASE_URL` is set in the dashboard (`sync: false`), so a Blueprint sync does not point it back to `omnilog-db`. Its name could not be resolved any more, so every start of the API failed (#402).
- `alembic upgrade head` tries the database again for about 30 seconds (10 tries, 3 seconds apart) when it cannot be reached. On Render the name of the database could not be resolved for a few seconds after a new instance started, so the start command stopped and the deploy of `omnilog-api` was marked as failed, although a second try worked (#402).
- The workflow "Database Migration (Supabase)" failed on every push to `main` (`No 'script_location' key found`), and its red check stopped the deploys of `omnilog-api` on Render. It now builds the backend image and runs `alembic upgrade head` inside it, with a random `SECRET_KEY` for the run. `render.yaml` uses Python 3.15.0 again, because the build of `omnilog-api` failed with 3.15.2.
- `docker-compose.prod.yml` passes 11 more backend settings from `.env.prod` (`ACCESS_TOKEN_EXPIRE_MINUTES`, the cache and IGDB/TMDB call settings, `IGDB_MAX_REQUESTS_PER_SECOND` and `FRONTEND_PROXY_SECRET`), with the defaults of `config.py`. Before, a value in `.env.prod` was ignored. `env.prod.example` lists them, and a test checks that every setting of `backend/.env.example` reaches the container (#393).
- Every time in an answer of the API is sent in UTC with a `Z` (`2026-11-26T19:34:34.794654Z`) instead of without a time zone, and the diary shows it in the time zone of the browser. Before, the diary was printed in the time zone of the server and read the time as local time, so in Turkey it was 3 hours early (#383).
- Title details and reviews no longer wait for OpenAI. The embedding of a title and the OpenAI spoiler check run after the answer in a background job (`BACKGROUND_WORKERS`), and a review answers "not checked yet" until its result is written. After a failed call OpenAI is paused for `OPENAI_COOLDOWN_SECONDS` (default 60), so a broken OpenAI is not tried again on every open. Before, one request could wait about 25 seconds (#382).
- A local PostgreSQL that is not running no longer makes the API switch to an empty SQLite file that answered "ready" and then 500. The API now stops at the start with a clear message, and the SQLite code is removed (#371).
- A local SonarQube scan found 2 bugs, 1 vulnerability and 12 code smells. All are fixed (an unreachable `raise`, a password in an example comment, a form label without its field, a regular expression that could backtrack). The CI scan now also reads the frontend coverage. The results are in `docs/tests/sonarqube.md` (#299).
- The login and register limits on Render count the browser address again, not the address of the frontend for everybody. The new setting `FORWARDED_TRUSTED_HOPS` reads it from the right end of `X-Forwarded-For`, so a client cannot choose it by writing the left end (#251).
- `docker-compose.yml` publishes PostgreSQL on `localhost:5432` again, which CI, `backend/.env.example` and the docs use. It was moved to `5433`, so the Docker Compose smoke test found no database, fell back to SQLite and failed on the migrations. `POSTGRES_PORT` now picks another port when 5432 is taken.
- An empty `REDIS_URL` no longer stops the cache and the rate limits with an error. The in-process cache is used instead (#251).
- `render.yaml` sets the health check path `/api/health` of the frontend service, as `docs/deployment.md` says. Before, Render had no health check for `omnilog-web` (#292).

### Removed

- `API_URL` (`.env.prod`, the compose file) and `NEXT_PUBLIC_API_URL` (`frontend/Dockerfile`, `render.yaml`, `frontend/.env.example`). No code read them since the Axios client `src/lib/api.ts` was removed, but the build of the frontend image required them (#430).
- The unused frontend packages `axios`, `react-hook-form` and `recharts`, and the unused image `frontend/public/kagan.jpg` (#295).

### Security

- SonarCloud findings on `main` are fixed: no regular expression that can backtrack in the Wikidata genre names, `npm ci --ignore-scripts` and the local `tsc` in CI and the frontend image, `--only-binary :all:` for the CI tools, HTTPS only for the Gitleaks download, `[[` in the bash scripts, and generated reports out of the analysis. The findings that are safe are listed with their reason in `docs/tests/sonarqube.md` (#423).
- The frontend sends `Strict-Transport-Security: max-age=31536000` in production, so on Render the login form is not served over plain HTTP after the first visit. Caddy uses the same year instead of one day and drops the header of the frontend, so the browser gets one (#425).
- The choice to send HSTS without `includeSubDomains` (Render uses the shared `onrender.com` name) and without `preload` is written in `next.config.ts`, the Caddyfile and `docs/deployment.md`, section 9. A test keeps the HSTS value of the frontend and of Caddy the same and checks that Caddy drops the header of the frontend, so the browser gets one (#449).
- A user can change the password (`PUT /auth/password`), log out on all devices (`POST /auth/logout-all`) and delete the account (`DELETE /auth/me`) on the new account page. A new password and "log out everywhere" end every token of the user through `users.token_version` (claim `ver`, migration 0016) (#426).
- The writes of one user to the library, the chapters and the lists share one rate limit, `RATE_LIMIT_WRITES` (default `120/minute`). Before, one account could send 800 writes in 5 seconds, each with a diary row (#431).
- The failed logins of one account are limited from any address (`RATE_LIMIT_LOGIN_ACCOUNT`, default `20/hour`). Over the limit, the login of that account answers 429 with `Retry-After` until the window ends, also for the right password. The key is a hash of the username or email, and unknown accounts are counted the same way (#391).
- `GET /catalog/{id}` has a per-user limit, `RATE_LIMIT_DETAILS` (default `60/minute`), because opening a title that was not loaded yet calls IGDB or TMDB and OpenAI. A test checks that the embedding of a title is saved once and that later opens do not call OpenAI (#390).
- "Log out" ends the token at the backend with the new `POST /auth/logout`, so a copied token stops working at once instead of 90 minutes later. Every token has a `jti` claim, and the ended ones are kept in the new table `revoked_tokens` (migration 0014) until they would expire. Other tokens of the same user keep working. Tokens without `jti` are refused, so every user logs in once again after the update (#378).
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
