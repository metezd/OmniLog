# Static analysis

Part of #234 (Software Test Document). This feeds the Software Testing Report (#296). The tools were first run on 2026-11-19 on `test_work`. They were run again on **2026-11-26** on `test_work` at `c1fbcc9` (`main` at `e23f225` plus #234), so the numbers below are current. Raw outputs: [`static-analysis/raw/`](static-analysis/raw/).

SonarQube is the main static analysis of the project. Its results, with screenshots, are in [sonarqube](sonarqube.md) (#349). The tools here are a second, independent check of the same code. The findings of both, with what was done about each, are in the [mitigation plan](mitigation-plan.md).

## 1. Results

| Tool | Scope | Command | 2026-11-19 | 2026-11-26 |
|---|---|---|---|---|
| Ruff 0.17.5, the rules of `ruff.toml` (security rules `S`) | `backend/` | `ruff check backend` | 0 findings | **0 findings** (`raw/ruff-backend.txt`). The same check as the CI job "Security lint (Ruff)" |
| Bandit 1.9.4 | `backend/app` (5 143 lines) | `bandit -r backend/app -f json` | 0 findings | **0 findings** at any severity (`raw/bandit-backend.json`) |
| `pip-audit` | `backend/requirements.txt` | `pip-audit --require-hashes --disable-pip -r backend/requirements.txt` | no known vulnerabilities | **No known vulnerabilities** (`raw/pip-audit.txt`) |
| `npm audit` | `frontend` (all packages) | `npm audit --json` | 0 vulnerabilities | **0 vulnerabilities**: 0 critical, 0 high, 0 moderate, 0 low (`raw/npm-audit.json`) |
| ESLint (`eslint-config-next` and the security rules) | `frontend` | `npx eslint .` | 0 errors, 5 warnings (`<img>`) | **0 errors, 0 warnings** (`raw/eslint-frontend.txt` is empty) |
| TypeScript compiler | `frontend` | `npx tsc --noEmit` | 0 errors | **0 errors** (`raw/tsc-frontend.txt` is empty) |
| Radon, cyclomatic complexity | `backend/app` | `radon cc backend/app -a -s` | 278 blocks, average 3.05 (A), 6 of grade C | **326 blocks, average 3.14 (A)**. 8 functions of grade C (11 to 14), none worse (`raw/radon-complexity.txt`) |
| Radon, raw metrics | `backend/app` | `radon raw -s backend/app` | 10% comment lines | 4 609 source lines, **11% comment and docstring lines** (`raw/radon-raw.txt`) |
| Static security tests | `backend/` | `pytest tests/test_security_static.py` | passed | **64 passed** (12 test functions: JWT, CORS, debug mode, secrets in logs, SQL strings) |
| Database migrations | `backend/migrations` | `alembic upgrade head`, `alembic check` | passed | **Passed**: 13 migrations, no difference between the models and the schema |

Radon reads every file now. On 2026-11-19 it could not read `main.py`, `core/database.py` and `core/security.py`, because they started with a byte-order mark (finding Q-05). No file starts with one today.

The ESLint warnings of 2026-11-19 were `<img>` elements of the friends page, which #333 removed. The one `<img>` left, in `PosterImage.tsx`, is allowed on purpose: posters go through the proxy `/api/poster`, which takes only the TMDB and IGDB image hosts (#326, #342).

## 2. Functions of grade C

| Function | Complexity | Has tests |
|---|---:|---|
| `sync.py: main` | 14 | yes (`test_epic3_manual_sync.py`) |
| `integrations/openai_client.py: embed_texts` | 14 | yes (`test_openai_client.py`) |
| `seed/__main__.py: main` | 13 | yes (`test_epic4_seed_game_chapters.py`) |
| `integrations/openai_client.py: classify_spoiler` | 13 | yes (`test_openai_client.py`) |
| `api/deps.py: client_address` | 12 | yes (`test_client_address_and_redis_url.py`, `test_f1_render_rate_limit.py`) |
| `integrations/tmdb.py: fetch_series` | 12 | yes (`test_epic3_title_details_edge_cases.py`) |
| `services/recommendations_service.py: get_recommendations` | 11 | yes (`test_epic5_ai.py`, `test_epic5_review_and_recommendation_edge_cases.py`) |
| `integrations/igdb.py: _get_access_token` | 11 | partly: it runs in every faked search, but lines 80 to 89 (error answers of the Twitch sign-in) do not. The search edge cases that tested the sign-in were lost in `310010a` (Q-11) |

SonarQube's limit for cognitive complexity (15) is not crossed by any of them: its scan has 0 code smells ([sonarqube](sonarqube.md)). They are finding Q-06.

## 3. What the tools cannot see

Bandit and Ruff know only Python. The TypeScript code is checked by ESLint's security rules, by Semgrep in CI and by SonarQube. No tool here checks the behavior of the code; that is the job of the tests ([traceability](traceability.md)) and of the [penetration test](penetration/README.md).

## 4. How to repeat

From the repository root, with the backend packages and the test packages installed:

```bash
pip install -r .github/requirements-ruff.txt bandit radon pip-audit
ruff check backend
bandit -r backend/app -f json -o bandit-backend.json
pip-audit --require-hashes --disable-pip -r backend/requirements.txt
radon cc backend/app -a -s
radon raw -s backend/app
python -m pytest tests/test_security_static.py
cd backend && alembic upgrade head && alembic check && cd ..
```

Frontend, from `frontend/` after `npm ci` (delete `frontend/coverage` first, or ESLint also reads the generated report):

```bash
npm audit --json
npx eslint .
npx tsc --noEmit
```
