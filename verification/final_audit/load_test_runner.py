"""Async concurrent load test for the prior audit's Task 3 deliverable.

Reads BASE_URL from env (defaults to localhost). Logs in as testsim once,
captures the session cookie, then for each concurrency tier (10/25/50)
hammers the listed endpoints in parallel via httpx.AsyncClient.

Output: ``verification/final_audit/load_test.json`` with per-tier per-endpoint
{p50, p95, p99, min, max, count, errors_5xx, timeouts, status_codes}.

Run:
    BASE_URL=https://prosim-100-XXXXX.herokuapp.com \
      docker compose exec -T web python verification/final_audit/load_test_runner.py
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Tuple

import httpx


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001").rstrip("/")
USERNAME = os.environ.get("BENCH_USER", "testsim")
PASSWORD = os.environ.get("BENCH_PASS", "TestSim!2026")
TIMEOUT = 30.0

ENDPOINTS = [
    ("/landuse/", "GET"),
    ("/renewable/", "GET"),
    ("/verbrauch/", "GET"),
    ("/ws/", "GET"),
    ("/annual-electricity/", "GET"),
    ("/bilanz/", "GET"),
    ("/cockpit/", "GET"),
    ("/historie/", "GET"),
]
TIERS = [10, 25, 50]
REQUESTS_PER_WORKER = 3


async def login(client):
    r = await client.get(f"{BASE_URL}/login/")
    r.raise_for_status()
    import re
    m = re.search(
        r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)['\"]",
        r.text,
    )
    if not m:
        raise RuntimeError("CSRF token not found")
    csrftoken = m.group(1)
    r = await client.post(
        f"{BASE_URL}/login/",
        data={
            "csrfmiddlewaretoken": csrftoken,
            "username": USERNAME,
            "password": PASSWORD,
        },
        headers={"Referer": f"{BASE_URL}/login/"},
    )
    if r.status_code not in (200, 302):
        raise RuntimeError(
            f"login failed: status={r.status_code}, body={r.text[:200]}"
        )


async def hit(client, path, method) -> Tuple[float, int, str]:
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        if method == "GET":
            r = await client.get(url, timeout=TIMEOUT, follow_redirects=False)
        else:
            r = await client.request(method, url, timeout=TIMEOUT)
        return (time.perf_counter() - start, r.status_code, "")
    except httpx.TimeoutException:
        return (TIMEOUT, 0, "timeout")
    except httpx.HTTPError as e:
        return (time.perf_counter() - start, 0, f"http_error:{type(e).__name__}")
    except Exception as e:  # noqa: BLE001
        return (time.perf_counter() - start, 0, f"other:{type(e).__name__}")


async def worker(worker_id, results, requests_per_worker):
    async with httpx.AsyncClient(verify=False, follow_redirects=False) as client:
        try:
            await login(client)
        except Exception as e:  # noqa: BLE001
            results.append((worker_id, None, None, f"login_failed:{e}", None))
            return
        for endpoint, method in ENDPOINTS:
            for _ in range(requests_per_worker):
                elapsed, status, err = await hit(client, endpoint, method)
                results.append((worker_id, endpoint, elapsed, err, status))


async def run_tier(concurrency):
    results = []
    workers = [worker(i, results, REQUESTS_PER_WORKER) for i in range(concurrency)]
    tier_start = time.perf_counter()
    await asyncio.gather(*workers)
    tier_wall = time.perf_counter() - tier_start

    per_endpoint = {}
    login_failures = 0
    for worker_id, endpoint, elapsed, err, status in results:
        if endpoint is None:
            login_failures += 1
            continue
        b = per_endpoint.setdefault(
            endpoint,
            {
                "latencies": [],
                "errors": 0,
                "timeouts": 0,
                "status_5xx": 0,
                "status_2xx": 0,
                "status_3xx": 0,
                "status_4xx": 0,
                "status_other": 0,
            },
        )
        b["latencies"].append(elapsed)
        if err == "timeout":
            b["timeouts"] += 1
        elif err:
            b["errors"] += 1
        if status:
            if 200 <= status < 300:
                b["status_2xx"] += 1
            elif 300 <= status < 400:
                b["status_3xx"] += 1
            elif 400 <= status < 500:
                b["status_4xx"] += 1
            elif 500 <= status < 600:
                b["status_5xx"] += 1
            else:
                b["status_other"] += 1

    summary = {
        "concurrency": concurrency,
        "wall_seconds": round(tier_wall, 2),
        "login_failures": login_failures,
        "per_endpoint": {},
    }
    for ep, b in per_endpoint.items():
        latencies = b.pop("latencies")
        latencies.sort()
        n = len(latencies)
        if n == 0:
            continue
        summary["per_endpoint"][ep] = {
            "count": n,
            "p50_s": round(latencies[n // 2], 3),
            "p95_s": round(latencies[min(n - 1, int(n * 0.95))], 3),
            "p99_s": round(latencies[min(n - 1, int(n * 0.99))], 3),
            "min_s": round(latencies[0], 3),
            "max_s": round(latencies[-1], 3),
            **b,
        }
    return summary


async def main():
    print(f"Load test against {BASE_URL!r} as {USERNAME!r}")
    print(f"Tiers: {TIERS}, requests/worker: {REQUESTS_PER_WORKER}")
    overall = {"base_url": BASE_URL, "username": USERNAME, "tiers": []}
    for tier in TIERS:
        print(f"\n=== Tier {tier} concurrent users ===")
        result = await run_tier(tier)
        overall["tiers"].append(result)
        print(
            f"  wall: {result['wall_seconds']}s, "
            f"login_failures: {result['login_failures']}"
        )
        for ep, s in sorted(result["per_endpoint"].items()):
            print(
                f"  {ep:<28}  n={s['count']:>3}  "
                f"p50={s['p50_s']:>6.2f}s  p95={s['p95_s']:>6.2f}s  "
                f"p99={s['p99_s']:>6.2f}s  5xx={s['status_5xx']}  "
                f"to={s['timeouts']}"
            )
    out_path = "verification/final_audit/load_test.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(overall, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
