# T6 — Heroku evidence

The bench script is portable: pass `BASE_URL=https://prosim-100-<host>.herokuapp.com` and it will append a Heroku-targeted log line.

In this audit run, when Heroku is up, the script is exercised against the live URL purely to confirm the calling pattern + log format. Because the harness is a stub, the resulting `elapsed_seconds` will be `null` against Heroku as well.

## What V5 is *not* doing here

Because the harness does not measure (TODO: Phase 7-B), V5 cannot produce a real Heroku response-time number. The actual cold-boot timings against Heroku are captured in `cross_cutting/heroku_cold_boot.md` for separate documentation.

## V5 outcome

- Script callable against the live URL: ✅
- Emits JSON line with correct metadata: ✅
- Captures real elapsed_seconds: ❌ (stub)

This is captured in the verdict as PASS-WITH-CAVEAT — the harness's *shape* is shipped, the *measurement* is not.
