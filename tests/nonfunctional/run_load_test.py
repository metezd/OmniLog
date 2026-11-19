"""Load test for the OmniLog API (non-functional test: performance and reliability under load).

This is a stand-alone script. It is not collected by pytest (the file name has no `test_` prefix)
because it needs a running server. It talks to the API over real HTTP, so it measures the whole
stack: Uvicorn, FastAPI, SQLAlchemy, PostgreSQL and the cache.

    # 1. start the API (PostgreSQL and Redis must run, migrations must be applied)
    cd backend && uvicorn app.main:app --port 8000
    # 2. run the load test from the repository root
    python tests/nonfunctional/run_load_test.py --base-url http://127.0.0.1:8000 \\
        --out docs/tests/non-func-tests/results

Each scenario is run at several numbers of parallel virtual users. A virtual user is a thread
with its own connection that sends requests one after the other. For every run the script reports
requests per second, the median (p50), p95 and p99 response time, and the error rate. Only a
response with the expected status code counts as a success.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

P95_LIMIT_MS = 500  # NFR-01 limit, used here as the pass mark for every scenario except login


def percentile(sorted_values: list[float], fraction: float) -> float:
    """Nearest-rank percentile of an already sorted list."""
    if not sorted_values:
        return float("nan")
    index = max(0, min(len(sorted_values) - 1, int(round(fraction * len(sorted_values))) - 1))
    return sorted_values[index]


def prepare_user(base_url: str, library_size: int) -> dict:
    """Register a user and fill the library, so list endpoints return realistic payloads."""
    name = f"load_{uuid.uuid4().hex[:8]}"
    credentials = {"username": name, "email": f"{name}@example.com", "password": "StrongPass123!"}
    with httpx.Client(base_url=base_url, timeout=30) as client:
        client.post("/auth/register", json=credentials).raise_for_status()
        token = client.post(
            "/auth/login", json={"username": name, "password": credentials["password"]}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        for number in range(library_size):
            media = client.post(
                "/media",
                json={
                    "title": f"{name} title {number}",
                    "media_type": "GAME" if number % 3 else "SERIES",
                    "release_date": "2020-01-01",
                },
                headers=headers,
            )
            media.raise_for_status()
            client.post(
                "/library",
                json={
                    "media_item_id": media.json()["id"],
                    "status": "COMPLETED",
                    "rating": 1 + number % 10,
                },
                headers=headers,
            ).raise_for_status()
    return {"credentials": credentials, "headers": headers}


def run_scenario(base_url, method, path, headers, json_body, expected, users, per_user):
    """Run `users` parallel virtual users, each sending `per_user` requests."""
    durations: list[float] = []
    failures = 0

    def virtual_user() -> tuple[list[float], int]:
        local, bad = [], 0
        with httpx.Client(base_url=base_url, timeout=30) as client:
            for _ in range(per_user):
                start = time.perf_counter()
                try:
                    response = client.request(method, path, headers=headers, json=json_body)
                    ok = response.status_code == expected
                except httpx.HTTPError:
                    ok = False
                local.append((time.perf_counter() - start) * 1000)
                bad += 0 if ok else 1
        return local, bad

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=users) as pool:
        for local, bad in [future.result() for future in [pool.submit(virtual_user) for _ in range(users)]]:
            durations += local
            failures += bad
    elapsed = time.perf_counter() - started

    durations.sort()
    total = len(durations)
    return {
        "virtual_users": users,
        "requests": total,
        "errors": failures,
        "error_rate_percent": round(100 * failures / total, 2),
        "requests_per_second": round(total / elapsed, 1),
        "p50_ms": round(statistics.median(durations), 1),
        "p95_ms": round(percentile(durations, 0.95), 1),
        "p99_ms": round(percentile(durations, 0.99), 1),
        "max_ms": round(durations[-1], 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default="load-test-results", help="folder for the result files")
    parser.add_argument("--library-size", type=int, default=40)
    parser.add_argument("--per-user", type=int, default=40, help="requests of every virtual user")
    parser.add_argument("--users", type=int, nargs="+", default=[1, 10, 25, 50])
    args = parser.parse_args()

    user = prepare_user(args.base_url, args.library_size)
    login_body = {
        "username": user["credentials"]["username"],
        "password": user["credentials"]["password"],
    }
    scenarios = [
        ("health", "GET", "/health", None, None, 200),
        ("library list", "GET", "/library", user["headers"], None, 200),
        ("diary", "GET", "/diary", user["headers"], None, 200),
        ("stats", "GET", "/stats", user["headers"], None, 200),
        ("recommendations", "GET", "/recommendations?target=SERIES", user["headers"], None, 200),
        # Login is slow on purpose (bcrypt, cost 12), so it gets fewer requests and no 500 ms pass mark
        ("login (bcrypt)", "POST", "/auth/login", None, login_body, 200),
        ("no token (401)", "GET", "/library", None, None, 401),
    ]

    results = []
    for name, method, path, headers, body, expected in scenarios:
        per_user = max(5, args.per_user // 4) if name.startswith("login") else args.per_user
        # one warm-up request fills the caches, so the numbers describe the steady state
        run_scenario(args.base_url, method, path, headers, body, expected, 1, 2)
        for users in args.users:
            row = run_scenario(args.base_url, method, path, headers, body, expected, users, per_user)
            row.update(scenario=name, method=method, path=path)
            row["meets_500ms_p95"] = row["p95_ms"] < P95_LIMIT_MS
            results.append(row)
            print(
                f"{name:<18} users={users:<3} rps={row['requests_per_second']:<8} "
                f"p50={row['p50_ms']:<7} p95={row['p95_ms']:<7} p99={row['p99_ms']:<7} "
                f"errors={row['errors']}",
                flush=True,
            )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "load-test-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults written to {out / 'load-test-results.json'}")
    return 1 if any(row["errors"] for row in results) else 0


if __name__ == "__main__":
    sys.exit(main())
