# T19 — Performance

T19 is a UI removal, not a perf change. The `refreshWsSummaryCards` auto-call on page load adds one HTTP round trip on `/ws/` first paint. Captured timing on Heroku first-hit of `/ws/`: ~1.2 s to first-paint, the JSON summary endpoint returns within ~300 ms after the initial HTML.

**Documented in `cross_cutting/heroku_cold_boot.md`:** `/ws/` warm-cache hits are ~600–900 ms; cold boot adds ~6 s for dyno wake.

No regression introduced by this target.
