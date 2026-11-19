# Static Analysis Results

**Branch:** `test_work` | **Run date:** 19.11.2026 | Raw outputs: [`raw/`](raw/)

These tools were run **instead of** SonarQube, which could not be run in the test environment (see [README](README.md)). They are not SonarQube results.

| Tool | Scope | Command | Result |
|---|---|---|---|
| Ruff, security rules `S` (flake8-bandit) | `backend/` | `ruff check backend` | **0 findings** (`raw/ruff-backend.txt`). Same check as the CI job "Security lint (Ruff)" |
| Bandit 1.9 | `backend/app` (4 254 lines) | `bandit -r backend/app` | **0 findings** at any severity (`raw/bandit-backend.json`) |
| `pip-audit` | `backend/requirements.txt` | `pip-audit -r backend/requirements.txt` | **No known vulnerabilities** (`raw/pip-audit.txt`) |
| `npm audit` | `frontend` (all packages) | `npm audit --json` | **0 vulnerabilities**: 0 critical, 0 high, 0 moderate, 0 low (`raw/npm-audit.json`) |
| ESLint (`eslint-config-next`) | `frontend` | `npm run lint` | **0 errors, 5 warnings**: `<img>` used instead of `next/image` (`raw/eslint-frontend.txt`) |
| TypeScript compiler | `frontend` | `npx tsc --noEmit` | **0 errors** (`raw/tsc-frontend.txt` is empty) |
| Radon, cyclomatic complexity | `backend/app` | `radon cc backend/app -a -s` | 278 functions, **average 3.05 (A)**. 6 functions of grade C (11 to 14), none worse (`raw/radon-complexity.txt`) |
| Radon, raw metrics | `backend/app` | `radon raw -s backend/app` | 10 % comment lines (`raw/radon-raw.txt`) |
| Pytest AST checks | `backend/` | `pytest tests/test_security_static.py` | Passed (JWT, CORS, debug mode, secrets in logs, SQL strings) |
| Database migrations | `backend/migrations` | `alembic upgrade head`, `alembic check` | Passed: 11 migrations, no drift between models and schema |

Limits of these results: Radon could not read three files that start with a byte-order mark (`main.py`, `core/database.py`, `core/security.py`), so their complexity is not in the average (Q-05). Bandit and Ruff only know Python. There is no static security analysis of the TypeScript code other than ESLint's rules; the CI job `semgrep-registry` covers more.

## Mapping to the SonarQube vocabulary

| SonarQube category | What was found without SonarQube |
|---|---|
| Vulnerabilities | None (Ruff `S`, Bandit, dependency audits) |
| Security hotspots | None reported by Bandit. Items to review by hand: `database.py` fallback (Q-04), no rate limit on login (Q-03) |
| Bugs | None found by tests. One latent bug in dead code (Q-01) |
| Code smells | Dead and duplicated code (Q-01), complexity (Q-06), deprecated API (Q-07), BOM (Q-05), `<img>` (Q-09) |
| Coverage | Backend 91.3 %, frontend 32.8 % (Q-08) |
| Duplications | `journal_service` and `list_service` (and their routers) repeat the same functions (Q-01) |
