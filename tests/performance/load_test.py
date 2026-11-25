"""HTTP load test for the OmniLog API (#298).

Not a pytest file (no `test_` prefix), so the normal test run does not collect it. It uses only
httpx and asyncio, which the backend already installs, so the Charter stack does not grow.

Each virtual user registers once, logs in once, adds a few titles to its library and makes a list.
Then it repeats a weighted mix of calls until the time is up: many reads, some updates and a rare
login (bcrypt is slow on purpose, so a real user logs in once, not in every loop).

    python tests/performance/load_test.py --base-url http://localhost:8000 --users 10 --seconds 30

Start the API with RATE_LIMIT_ENABLED=false for this test only, otherwise most answers are 429.
The setup adds titles with POST /media, so the API also needs ALLOW_MEDIA_CREATE=true. Use both
only on a test stack, never in production. With --search the script instead measures the cached
catalog search (the first call fills the cache, the others must be fast).

The exit code is 1 when the p95 of all calls or the error rate is over its limit.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import random
import secrets
import statistics
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

# A new password for each run, only for the throwaway users of the test stack
PASSWORD = f"Load-{secrets.token_hex(8)}"

# Weighted mix of one loop step. The weights are relative, they do not need to add up to 100.
MIX = [
    ("GET /library", 20),
    ("GET /diary", 12),
    ("GET /lists", 12),
    ("GET /stats", 15),
    ("GET /auth/me", 15),
    ("GET /health", 10),
    ("PATCH /library/{id}", 14),
    ("POST /auth/login", 2),
]
STATUSES = ["PLAN_TO_WATCH", "IN_PROGRESS", "COMPLETED", "DROPPED"]
# Picks the next call of the mix. Not for anything secret, but SystemRandom keeps the linter quiet.
rng = random.SystemRandom()


@dataclass
class Results:
    latencies: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_examples: dict[str, str] = field(default_factory=dict)

    def record(self, name: str, seconds: float, ok: bool, detail: str = "") -> None:
        self.latencies[name].append(seconds)
        if not ok:
            self.errors[name] += 1
            self.error_examples.setdefault(name, detail[:200])


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile, the same as in tests/requirements/test_nfr.py."""
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(pct / 100 * len(ordered) + 0.5)) - 1))
    return ordered[index]


async def call(client: httpx.AsyncClient, results: Results, name: str, method: str, url: str,
               expected: tuple[int, ...] = (200,), **kwargs) -> httpx.Response | None:
    start = time.perf_counter()
    try:
        response = await client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        results.record(name, time.perf_counter() - start, False, f"{type(exc).__name__}: {exc}")
        return None
    ok = response.status_code in expected
    results.record(name, time.perf_counter() - start, ok, f"{response.status_code} {response.text}")
    return response


async def setup_user(client: httpx.AsyncClient, results: Results, titles: int) -> dict | None:
    """Register, log in, add titles to the library and make a list. Returns the user state."""
    name = f"load{uuid.uuid4().hex[:12]}"
    body = {"username": name, "email": f"{name}@example.com", "password": PASSWORD}
    if await call(client, results, "setup POST /auth/register", "POST", "/auth/register", (201,), json=body) is None:
        return None
    response = await call(client, results, "setup POST /auth/login", "POST", "/auth/login",
                          json={"username": name, "password": PASSWORD})
    if response is None or response.status_code != 200:
        return None
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    entries = []
    for number in range(titles):
        media = await call(client, results, "setup POST /media", "POST", "/media", (201,), headers=headers,
                           json={"title": f"{name} title {number}", "media_type": rng.choice(["GAME", "SERIES", "MOVIE"])})
        if media is None or media.status_code != 201:
            continue
        entry = await call(client, results, "setup POST /library", "POST", "/library", (201,), headers=headers,
                           json={"media_item_id": media.json()["id"], "status": "IN_PROGRESS"})
        if entry is not None and entry.status_code == 201:
            entries.append(entry.json()["id"])
    await call(client, results, "setup POST /lists", "POST", "/lists", (201,), headers=headers,
               json={"name": f"{name} favourites"})
    return {"name": name, "headers": headers, "entries": entries}


async def user_loop(client: httpx.AsyncClient, results: Results, user: dict, stop_at: float) -> None:
    names = [name for name, _ in MIX]
    weights = [weight for _, weight in MIX]
    headers = user["headers"]
    while time.perf_counter() < stop_at:
        step = rng.choices(names, weights)[0]
        if step == "PATCH /library/{id}":
            if not user["entries"]:
                continue
            await call(client, results, step, "PATCH", f"/library/{rng.choice(user['entries'])}",
                       headers=headers, json={"status": rng.choice(STATUSES), "rating": rng.randint(1, 10)})
        elif step == "POST /auth/login":
            response = await call(client, results, step, "POST", "/auth/login",
                                  json={"username": user["name"], "password": PASSWORD})
            if response is not None and response.status_code == 200:
                headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        elif step == "GET /health":
            await call(client, results, step, "GET", "/health")
        else:
            await call(client, results, step, "GET", step.split(" ", 1)[1], headers=headers)


async def search_loop(client: httpx.AsyncClient, results: Results, headers: dict, query: str,
                      media_type: str, stop_at: float) -> None:
    while time.perf_counter() < stop_at:
        await call(client, results, "GET /catalog/search (cached)", "GET", "/catalog/search",
                   headers=headers, params={"q": query, "type": media_type})


def summarize(results: Results, seconds: float, measured: set[str]) -> dict:
    endpoints = {}
    for name in sorted(results.latencies):
        values = results.latencies[name]
        endpoints[name] = {
            "requests": len(values),
            "errors": results.errors.get(name, 0),
            "p50_ms": round(percentile(values, 50) * 1000, 1),
            "p95_ms": round(percentile(values, 95) * 1000, 1),
            "p99_ms": round(percentile(values, 99) * 1000, 1),
            "max_ms": round(max(values) * 1000, 1),
            "mean_ms": round(statistics.fmean(values) * 1000, 1),
            "measured": name in measured,
        }
    all_values = [v for name in measured for v in results.latencies.get(name, [])]
    errors = sum(results.errors.get(name, 0) for name in measured)
    total = len(all_values)
    return {
        "endpoints": endpoints,
        "total": {
            "requests": total,
            "errors": errors,
            "error_rate": round(errors / total, 4) if total else 1.0,
            "requests_per_second": round(total / seconds, 1) if seconds else 0.0,
            "p50_ms": round(percentile(all_values, 50) * 1000, 1) if all_values else None,
            "p95_ms": round(percentile(all_values, 95) * 1000, 1) if all_values else None,
            "p99_ms": round(percentile(all_values, 99) * 1000, 1) if all_values else None,
        },
        "error_examples": results.error_examples,
    }


def print_table(summary: dict) -> None:
    print(f"{'endpoint':32} {'req':>6} {'err':>5} {'p50':>8} {'p95':>8} {'p99':>8} {'max':>8}")
    for name, row in summary["endpoints"].items():
        mark = "" if row["measured"] else "  (setup, not in the total)"
        print(f"{name:32} {row['requests']:6} {row['errors']:5} {row['p50_ms']:8} {row['p95_ms']:8} "
              f"{row['p99_ms']:8} {row['max_ms']:8}{mark}")
    t = summary["total"]
    print(f"TOTAL {t['requests']} requests, {t['requests_per_second']}/s, error rate {t['error_rate'] * 100:.2f}%, "
          f"p50 {t['p50_ms']} ms, p95 {t['p95_ms']} ms, p99 {t['p99_ms']} ms")
    for name, example in summary["error_examples"].items():
        print(f"first error of {name}: {example}")


async def run(args: argparse.Namespace) -> dict:
    limits = httpx.Limits(max_connections=args.users + 5, max_keepalive_connections=args.users + 5)
    async with httpx.AsyncClient(base_url=args.base_url, timeout=args.timeout, verify=not args.insecure,
                                 limits=limits) as client:
        results = Results()
        health = await client.get("/health")
        health.raise_for_status()

        if args.search:
            user = await setup_user(client, results, titles=0)
            if user is None:
                raise SystemExit(f"setup failed: {dict(results.error_examples)}")
            first = await call(client, results, "first search (fills the cache)", "GET", "/catalog/search",
                               headers=user["headers"], params={"q": args.search, "type": args.search_type})
            if first is None or first.status_code != 200:
                raise SystemExit(f"the first search failed: {dict(results.error_examples)}")
            start = time.perf_counter()
            stop_at = start + args.seconds
            await asyncio.gather(*(search_loop(client, results, user["headers"], args.search, args.search_type, stop_at)
                                   for _ in range(args.users)))
            measured = {"GET /catalog/search (cached)"}
        else:
            # Users join a few at a time: registration and login are two bcrypt checks each, and
            # 80 users that all register in the same second time out on one process.
            gate = asyncio.Semaphore(args.setup_concurrency)

            async def join():
                async with gate:
                    return await setup_user(client, results, args.titles)

            users = await asyncio.gather(*(join() for _ in range(args.users)))
            ready = [user for user in users if user is not None]
            if len(ready) < args.users:
                raise SystemExit(f"setup failed for {args.users - len(ready)} users: {dict(results.error_examples)}")
            start = time.perf_counter()
            stop_at = start + args.seconds
            await asyncio.gather(*(user_loop(client, results, user, stop_at) for user in ready))
            measured = {name for name, _ in MIX}
        elapsed = time.perf_counter() - start

    summary = summarize(results, elapsed, measured)
    summary["settings"] = {
        "base_url": args.base_url,
        "users": args.users,
        "seconds": args.seconds,
        "titles_per_user": args.titles,
        "setup_concurrency": args.setup_concurrency,
        "search": args.search,
        "p95_limit_ms": args.p95_limit,
        "error_limit": args.error_limit,
        "mix": dict(MIX) if not args.search else None,
    }
    summary["run"] = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed, 1),
        "client_python": platform.python_version(),
        "client_cpus": os.cpu_count(),
        "label": args.label,
    }
    total = summary["total"]
    summary["passed"] = {
        "p95": total["p95_ms"] is not None and total["p95_ms"] < args.p95_limit,
        "error_rate": total["error_rate"] < args.error_limit,
    }
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base-url", default="http://localhost:8000", help="address of the API")
    parser.add_argument("--users", type=int, default=10, help="virtual users at the same time")
    parser.add_argument("--seconds", type=float, default=30, help="length of the measured part")
    parser.add_argument("--titles", type=int, default=3, help="library entries per user")
    parser.add_argument("--setup-concurrency", type=int, default=10, help="users that register at the same time")
    parser.add_argument("--p95-limit", type=float, default=500, help="limit for the p95 of all calls, in ms")
    parser.add_argument("--error-limit", type=float, default=0.01, help="limit for the error rate (0.01 = 1%%)")
    parser.add_argument("--timeout", type=float, default=30, help="timeout of one call, in seconds")
    parser.add_argument("--search", metavar="TEXT", help="measure the cached catalog search for TEXT instead")
    parser.add_argument("--search-type", default="GAME", choices=["GAME", "SERIES", "MOVIE"])
    parser.add_argument("--insecure", action="store_true", help="accept the self-signed certificate of a local proxy")
    parser.add_argument("--label", default="", help="free text stored in the JSON, for example the machine")
    parser.add_argument("--json", metavar="FILE", help="also write the results to this JSON file")
    args = parser.parse_args(argv)
    if args.users < 1 or args.seconds <= 0:
        parser.error("--users must be 1 or more and --seconds more than 0")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = asyncio.run(run(args))
    print_table(summary)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as file:
            json.dump(summary, file, indent=2)
            file.write("\n")
    passed = all(summary["passed"].values())
    print("PASSED" if passed else f"FAILED: {summary['passed']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
