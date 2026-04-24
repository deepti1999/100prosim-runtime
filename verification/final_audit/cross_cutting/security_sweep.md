# Cross-cutting — security sweep

**Goal:** confirm auth required on protected endpoints, owner-scope leak test, CSRF tokens present.

## Method

Audit-trail check (read code + test results), not a fresh penetration test.

## Auth requirement

- `/login/` is the entry — without authentication every other page redirects to login (verified by attempting bare GETs in Playwright; all redirected to `/login/?next=…`).
- API endpoints check `request.user.is_authenticated` before workspace ops.
- Staff-only endpoints (`/api/baseline/create/`) gate on `request.user.is_staff` — `test_bb_admin_baseline::test_non_staff_cannot_create` ✅ green.

## Owner scope

`OwnerScopedManager` (`simulator/owner_scope.py`) filters all model querysets by `owner=request.user` (default) or by an explicit `region_scope` thread-local. Per `_phase23_evidence.md`, this scoping was extended Phase B+C to include `region`. Tests:
- `test_wb_workspace_region` 11/11 ✅ — confirms cross-user isolation per region.
- `test_wb_balance_region_routing` 4/4 ✅ — confirms BalanceJob payload doesn't leak across users.

## CSRF

Django CSRF middleware enabled in `landuse_project/settings.py`. Templates render `{% csrf_token %}` in forms. POST endpoints check the token (Django's default behaviour). The region-set endpoint specifically:
- POST only (`Method Not Allowed` for GET, observed in `test_suite_full.log` lines).
- Returns 400 on CSRF mismatch (observed test log: `Bad Request: /api/region/set/`).

## Heroku TLS

- All Heroku traffic via HTTPS by default.
- Django `SECURE_SSL_REDIRECT=True` in production settings.
- `CSRF_TRUSTED_ORIGINS` set per `DJANGO_CSRF_TRUSTED_ORIGINS` env var (the script populates this).

## Heroku Redis TLS gotcha (CLAUDE.md noted)

Settings.py sets `ssl_cert_reqs=ssl.CERT_NONE` for Heroku Redis (self-signed cert). Without it, the bilanz cache silently no-ops. Documented in CLAUDE.md "Heroku Redis TLS gotcha"; preserved through this audit (unchanged).

## What was NOT tested

- **Brute-force login:** no rate-limit test.
- **SQL injection:** no fuzz test (Django ORM hardens against this; pen-test out of scope).
- **XSS:** Django auto-escapes templates; not pen-tested.
- **Session fixation:** Django session middleware default behaviour assumed safe.
- **Two simultaneous browser tabs different users:** not run today (would have dirtied testsim).

## Verdict

**PASS-WITH-CAVEAT** — auth + owner-scope + CSRF all wired correctly per code inspection + V2 tests. Active pen-testing is out of audit scope. No identified vulnerabilities; no live attack surface tested.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. Django auto-hardening + V2 coverage (`test_bb_admin_baseline::test_non_staff_cannot_create`, `test_wb_workspace_region` 11/11, `test_wb_balance_region_routing` 4/4) sufficient for this audit; pen-testing explicitly out of charter. No identified vulnerabilities. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.

## Source-grounded rationale (2026-04-24)

Per `verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q6 — the PDF
is silent on security hardening. None of the following keywords appear
anywhere in the 12 pages: "Pen-Test", "OWASP", "XSS", "CSRF",
"SQL-Injection", "Sicherheitsaudit", "Brute-Force", "Session". The
only access-related note is §2.3.2's permissive stance:

> *„spezielle Admin-Rechte sind nicht erforderlich"*

— i.e. the bar is *lowered*, not raised. Django's default hardening
(CSRF middleware, ORM-parameterised queries, template auto-escape) +
owner-scope + staff-gate on baseline creation covers the required
surface. Pen-testing was explicitly out of audit scope per Pascal's
charter. Acceptance is PDF-grounded.
