# Performance tests

Issue #298. This feeds the Software Testing Report (#296). All numbers come from the runs of 2026-11-25. The raw results are the JSON files in [`tests/performance/results/2026-11-25`](../../tests/performance/results/2026-11-25).

## 1. Two kinds of evidence

| Kind | What it measures | Where |
|---|---|---|
| In process (NFR-01) | 100 cached catalog searches and 100 `/stats` calls through the FastAPI test client, with PostgreSQL and Redis. It measures the code and the database, but not the server, the network or many users at once | `tests/requirements/test_nfr.py` (`test_nfr01_*`), in every CI run |
| Over HTTP (this document) | Many virtual users at the same time, through Caddy over HTTPS to one uvicorn process, as in production | `tests/performance/load_test.py` and `tests/performance/run_stack.sh` |

## 2. The tool

A small Python script with `httpx` and `asyncio` (option A of the issue). Both are already installed for the backend, so the stack does not grow. Locust and k6 were not needed.

Each virtual user registers once, logs in once, adds 3 titles to its library and makes a list. Then it repeats this weighted mix until the time is up:

| Call | Weight |
|---|---|
| `GET /library` | 20 |
| `GET /stats` | 15 |
| `GET /auth/me` | 15 |
| `PATCH /library/{id}` | 14 |
| `GET /diary` | 12 |
| `GET /lists` | 12 |
| `GET /health` | 10 |
| `POST /auth/login` | 2 |

The login is rare on purpose. It runs bcrypt, which is slow by design, and a real user logs in once per session. The setup calls (register, first login, titles, list) are reported but are not part of the totals. Users join 10 at a time.

The limits are a p95 under **500 ms** (the NFR-01 value, used here as a project reference) and an error rate under **1%**.

## 3. Setup

- Machine: Apple M3 Pro, 11 cores, macOS 27.2.1, Docker Desktop with 11 CPUs and 7.7 GB of memory. **This is not the production machine.** Render's free plan has far less CPU, so the second series limits the backend to 1 CPU.
- Stack: `docker-compose.prod.yml` (Caddy 2 with HTTPS, the backend image with one uvicorn process as in `backend/Dockerfile`, PostgreSQL 16 with pgvector, Redis 7 with a password, the frontend).
- For this test only: `RATE_LIMIT_ENABLED=false`, because the limits count every call of one address and most answers would be 429, and `ALLOW_MEDIA_CREATE=true`, because the setup adds titles with `POST /media`. Never use either in production.
- The load generator runs in a Python 3.15 container on the same Docker network and calls `https://api.localhost` through Caddy. It shares the machine with the stack.
- Each run lasts 30 seconds.

## 4. Results

### No CPU limit

| Users | Requests/s | p50 | p95 | p99 | Errors | Login p95 | Limits |
|---|---|---|---|---|---|---|---|
| 5 | 535.7 | 4.7 ms | 12.2 ms | 213.5 ms | 0% | 219 ms | passed |
| 10 | 494.5 | 14.9 ms | 31.1 ms | 223.6 ms | 0% | 244 ms | passed |
| 20 | 542.3 | 32.3 ms | 59.8 ms | 240.4 ms | 0% | 259 ms | passed |
| 40 | 507.9 | 69.3 ms | 176.5 ms | 289.8 ms | 0% | 357 ms | passed |
| 80 | **6.0** | 188.7 ms | **30 203 ms** | 30 253 ms | **42.9%** | 30 164 ms | **failed** |
| 160 | 282.6 | 396.0 ms | **1 643.9 ms** | 2 635.1 ms | 0% | 1 536 ms | **failed** (p95) |

Per endpoint at 20 users: every read had a p95 between 15 ms (`/health`) and 50 ms (`/library`, `/lists`), the update 69 ms and the login 259 ms. The details of every run are in the JSON files.

### Backend limited to 1 CPU

| Users | Requests/s | p50 | p95 | p99 | Errors | Login p95 | Limits |
|---|---|---|---|---|---|---|---|
| 5 | 98.6 | 8.4 ms | 92.2 ms | 1 387.5 ms | 0% | 1 693 ms | passed |
| 10 | 122.9 | 60.7 ms | 197.0 ms | 998.0 ms | 0% | 1 892 ms | passed |
| 20 | 118.3 | 102.1 ms | 486.0 ms | 1 397.7 ms | 0% | 2 601 ms | passed, close to the limit |
| 40 | 113.8 | 213.4 ms | **1 109.4 ms** | 1 873.8 ms | 0% | 2 382 ms | **failed** (p95) |
| 80 | **4.3** | 30 001 ms | **30 118 ms** | 30 131 ms | **52.3%** | 30 098 ms | **failed** |

### Cached catalog search

10 users repeated `GET /catalog/search?q=Life is Strange&type=GAME` for 30 seconds after one call filled the cache (the keyless public sources, no CPU limit): **483 requests/s, p50 19.8 ms, p95 29.1 ms, p99 37.3 ms, no errors.** The cache works under load. A run with real IGDB and TMDB keys was not made, because the keys are only in the GitHub secrets. A manual CI run (#297) showed that the real services answer.

## 5. Analysis

**Throughput.** One uvicorn process serves about **500 requests/s** on this machine and about **115 to 123 requests/s** with one CPU. More users do not raise it, they only make each call wait longer. The reference run in the issue (one core, a small container) gave 70 to 77 requests/s, so the M3 core is faster, as expected.

**The knee.** Without a CPU limit, the p95 stays under 500 ms up to **40 users** and fails between 40 and 80. With one CPU it passes at 20 users (486 ms, just under the limit) and fails at 40. The login is the slowest call at every level: about 220 ms alone, and 1.7 to 2.6 seconds under load with one CPU, as the issue expected.

**The failure at 80 users.** With 80 users the API did not get slow, it stopped: almost no answers for 30 seconds, then timeouts. This happened in all three tries on 2026-11-25, with and without the CPU limit. The backend log shows the reason:

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
```

The endpoints are normal (`def`) functions, so FastAPI runs them in a pool of 40 threads. The database pool of SQLAlchemy has only 15 connections (5 plus 10 overflow, the defaults in `backend/app/core/database.py`). With more than 15 calls at the same time, the other threads wait up to 30 seconds for a connection, and the waiting threads block the next calls too. At 160 users the same stack kept answering (with a slow p95). Why 80 users locked up and 160 did not is not fully explained. The pool timeout is clearly involved, because the error appears in the log.

**Errors.** No run below the knee had a single error.

## 6. Recommendations

1. **Make the database pool fit the thread pool.** Set `pool_size` and `max_overflow` in `create_engine` so that the pool has at least as many connections as there are threads (for example 20 plus 20), and a short `pool_timeout` (for example 5 seconds), so that an overload gives quick errors instead of a 30 second lock. Check the connection limit of the database plan first. This needs its own issue and a repeat of this test.
2. **More than one process.** Start uvicorn with 2 to 4 workers (`--workers`) on a plan with more than one core. One process uses one core at most.
3. **Render's free plan** has far less CPU than one M3 core. Expect the knee there well under 20 users. Measure it with a harmless, short test only after the team agrees, never with this script against the shared hosted system.

## 7. How to repeat

The whole series, on a machine with Docker (it builds the images, starts the stack as the Compose project `omnilog-perf`, runs the tests and removes the stack):

```bash
SECONDS_PER_RUN=30 SEARCH_TEXT="Life is Strange" tests/performance/run_stack.sh tests/performance/results/2026-11-25/no-cpu-limit 5 10 20 40 80 160
BACKEND_CPUS=1 SECONDS_PER_RUN=30 tests/performance/run_stack.sh tests/performance/results/2026-11-25/backend-1-cpu 5 10 20 40 80
```

On GitHub: the workflow **Performance** (`.github/workflows/performance.yml`), started by hand with the users, the seconds and an optional CPU limit. It writes a table to the job summary and keeps the JSON files as an artifact.

Against an API that is already running (with the two test settings of section 3):

```bash
python tests/performance/load_test.py --base-url http://localhost:8000 --users 10 --seconds 30 --json result.json
```

Options: `--users`, `--seconds`, `--p95-limit` (ms, default 500), `--error-limit` (default 0.01), `--titles`, `--setup-concurrency`, `--search TEXT`, `--insecure` (for the self-signed certificate of a local Caddy) and `--json FILE`. The exit code is 1 when a limit fails.
