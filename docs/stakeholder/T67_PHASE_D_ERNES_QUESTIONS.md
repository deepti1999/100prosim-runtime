# T67 / §2.3 Phase D — Open questions for ErnES

**Audience:** ErnES (H. Schmidt-Kanefendt + the ≥ 2 admins per PDF §2.1).
**Asked by:** Pascal Leinfelder / Deepti (project owners).
**Why this exists:** PDF §2.3.2 says *"keine speziellen Admin-Rechte erforderlich"* — Phases A–C reduced that to *"no code change required"* (a single shell command), but a real non-coder admin still needs SSH / Docker / CLI access. Phase D is the upload UI that closes the literal ask. Before we build it, we need to know how ErnES will actually use it. Answers below pin the scope so we ship a form that fits, not one that has to be reworked once Phase 7 onboarding starts.

**How to answer:** mark the option you want under each question, or write a sentence in the "Notes" line. If a question doesn't apply or you don't have a preference, write "no preference" — that's a useful answer too.

---

## A. Authentication & access

### A1. Who can use the upload form?

- [ ] Same login as users (`testsim`-style), but with an "admin" role flag on the account
- [ ] Separate admin login (e.g. `/admin/region-import/` behind Django's built-in admin)
- [ ] Single shared admin account (the ≥ 2 admins from §2.1 share credentials)
- [ ] Personal admin accounts (one per ErnES admin)

**Notes:** ___________________________________________________________

### A2. Authentication mechanism

- [ ] Username + password (simple, current pattern)
- [ ] SSO via your existing identity provider (which one?: ___________)
- [ ] Two-factor (TOTP / hardware key)
- [ ] No preference — pick the simplest

**Notes:** ___________________________________________________________

### A3. Audit identity

When an admin uploads a new region's data, the import history will show *who* did it. Is the username sufficient, or do you need a real-name field as well?

- [ ] Username only is fine
- [ ] Need real name + email for compliance / reproducibility
- [ ] No preference

### A4. UI language for the admin pages

The whole user-facing app is German (per PDF §2.5.1). For the admin upload pages:

- [ ] German throughout (matches the rest of the app)
- [ ] German + English toggle (in case future admins are non-German speakers)
- [ ] English only (developer-style)
- [ ] No preference

**Notes:** ___________________________________________________________

---

## B. File handling

### B1. Where does the file come from?

- [ ] Browser file picker — admin downloads `D.xlsx` from `ernes.de` to their laptop, then uploads through the web form
- [ ] Shared filesystem path (e.g. an S3 bucket, an SMB share) that ErnES already maintains. If yes, where: ___________
- [ ] Both — admin can choose

**Notes:** ___________________________________________________________

### B2. Which workbook(s)?

The current `import_excel_provenance` consumes `D.xlsx` (data model). The companion `_S.xlsx` (scenario master, drives baseline cell values) is not currently importable. Do you want the form to:

- [ ] Accept `D.xlsx` only (current scope; provenance + Quellen + region columns)
- [ ] Accept both `D.xlsx` and `_S.xlsx` (provenance + scenario baseline values together)
- [ ] Accept `D.xlsx` now, plan `_S.xlsx` import as a follow-up
- [ ] Other: ___________

**Notes:** ___________________________________________________________

### B3. File size + upload limits

`D.xlsx` for Germany is ~3 MB; per-Bundesland files at <https://www.ernes.de/seite/422657/softwaretools.html> are similar. Should we plan for:

- [ ] ≤ 10 MB per upload (covers all known files with headroom)
- [ ] ≤ 50 MB per upload (room for combined workbooks)
- [ ] No preference

### B4. Where do uploaded files live after import?

- [ ] Discard after parsing (only the imported data lives in the DB)
- [ ] Archive every uploaded file in `data/import/<region>/history/<date>_D.xlsx` for audit replay
- [ ] Archive in cloud storage (S3 / Hetzner Object Storage / etc.) — which: ___________
- [ ] Git-track each upload (data is version-controlled alongside code)

**Notes:** ___________________________________________________________

### B5. "Export current to Excel" — round-trip editing

Often the easiest way to update a region is "download what's currently in the DB → edit it in Excel → re-upload". Should the form include an "Export current data as XLSX" button per region?

- [ ] Yes — this is how I'd actually want to update a region
- [ ] No — admins start from the canonical `D.xlsx` on `ernes.de` every time
- [ ] Yes for some types (e.g. user-facing parameters) but not others — specify: ___________

**Notes:** ___________________________________________________________

### B6. Accepted file formats

- [ ] XLSX only (current scope; matches `ernes.de` distribution)
- [ ] Also accept `.xlsm` (macro-enabled, e.g. `WS.xlsm`)
- [ ] Also accept `.ods` (LibreOffice native — for non-Excel admins)
- [ ] Also accept CSV (for very small / single-sheet imports)

**Notes:** ___________________________________________________________

---

## C. Region constants outside the Excel

### C1. `installed_pmax_ely_gw` and `installed_pmax_rv_gw` (the 194 / 261 GW labels on Jahresstrom)

These two numbers drive the red annotations on the flow diagram (T54 D4a / D4b). They are NOT in `D.xlsx` — they live in the `Region` row in the DB. For a new Bundesland, the upload form has to capture them somewhere. Options:

- [ ] Two number fields on the upload form ("Pmax Elektrolyse [GW]:" + "Pmax Rückverstromung [GW]:")
- [ ] You'll add a sheet to `D.xlsx` (e.g. `I_Region`) carrying these per region; we read it during import
- [ ] You don't have these numbers per Bundesland; default to Germany's 194 / 261 and we show a banner "regional Pmax not yet calibrated"
- [ ] Other: ___________

**Notes:** ___________________________________________________________

### C2. Other region-specific scalars we should know about

The current model exposes `region.code`, `display_name`, `active`, `installed_pmax_ely_gw`, `installed_pmax_rv_gw`. Are there other constants ErnES would expect to set per region (e.g. peak load, population, area, climate factor)?

- [ ] Just the two pmax values are enough
- [ ] Yes, also: ___________________________________________________________

### C3. WS daily time-series (`WSData` — 365 rows × 4 columns per region)

The Jahresgang Strom calculation eats a per-day, per-region table: daily Verbrauch / Solar / Wind / Heizung-Abwärme as per-mille values (the WS365 timeseries). Germany ships these in `WS.xlsm` sheet `Zeitreihen Kalkulation`. For a new region:

- [ ] Per-Bundesland WS series will arrive in the same `BB.xlsx` (which sheet?: ___________)
- [ ] WS series will arrive in a separate file (e.g. `BB_WS.xlsm`) — uploaded together with `D.xlsx`
- [ ] No regional WS data exists; a new region clones DE's WS series until ErnES provides one
- [ ] Other: ___________

**Notes:** ___________________________________________________________

---

## D. Validation & failure mode

### D1. Schema mismatch handling

`import_excel_provenance` currently fails loud on schema mismatch (missing sheet, wrong column name) — the CLI prints a Python stacktrace. For non-coder admins:

- [ ] Friendly summary in German *("Sheet '4. Verbrauch' fehlt Spalte 'Quellbezug'. Datei nicht importiert.")*
- [ ] Friendly summary + downloadable error log for forwarding to dev support
- [ ] Detailed dev-style error (the admin will forward to a developer)

**Notes:** ___________________________________________________________

### D2. Dry-run / preview before commit

Should the form show *"this will update 247 rows, add 12 rows, mark 5 orphans"* as a preview, then require an explicit "Übernehmen" (apply) button?

- [ ] Yes, always require preview + confirm
- [ ] Optional toggle (default: preview ON, but admin can skip for repeat imports)
- [ ] No, apply directly — admins know what they're doing

**Notes:** ___________________________________________________________

### D3. Partial-failure policy

If 200 of 247 rows import cleanly but 47 hit unmappable codes:

- [ ] Abort the whole import — nothing gets saved, admin fixes the file and re-uploads
- [ ] Import the 200, mark the 47 in `data/import/<region>/orphan_classification.csv`, show a warning banner
- [ ] Show the orphans up-front in the preview (D2), let the admin decide before commit

**Notes:** ___________________________________________________________

### D4. Rollback after a bad import

If yesterday's import broke something, can the admin click "Rollback to previous import" in the UI?

- [ ] Yes, the UI should track the last N imports and let an admin restore one
- [ ] No, rollback is a developer task — the audit log is enough
- [ ] Manual SQL / DB restore is fine (your DBA handles it)

**Notes:** ___________________________________________________________

### D5. Preserve previous edits on re-import

Suppose an admin manually corrected one assumption text ("notes_assumption") for `LU_2.1` last week, then today re-uploads a fresh `D.xlsx` that has the OLD assumption text. Should the re-import:

- [ ] Always overwrite — the file is the source of truth; previous manual edits are lost
- [ ] Preserve manual edits — only fields that were never edited get overwritten
- [ ] Show the conflict in preview ("12 fields you previously edited will be overwritten — confirm?") and let the admin decide per import
- [ ] No preference

**Notes:** ___________________________________________________________

### D6. Diff against current DB in the preview

When showing "this will update 247 rows", should the preview also show, for the most-changed rows, the actual before / after values?

- [ ] Yes — like a git diff: "LU_2.1 user_percent: 5.0 → 6.5"
- [ ] Just the counts ("247 rows changed") is enough
- [ ] Counts + a downloadable XLSX showing the diff for offline review
- [ ] No preference

**Notes:** ___________________________________________________________

---

## E. Region lifecycle

### E1. Adding a new region (the headline use case)

This is what the upload form primarily does. Confirm the flow:

> Admin opens `/admin/regions/new/` → enters code (`BB`), display name (`Brandenburg`), the two pmax values from C1 → clicks "Datei wählen", picks `BB.xlsx` from disk → preview shows "12 LandUse rows, 47 Renewable rows, … will be created" → admin clicks "Übernehmen" → success page with link to the new region in the dropdown.

- [ ] Yes, that flow is right
- [ ] Modify it: ___________________________________________________________

### E2. Updating an existing region

Admin re-uploads `D.xlsx` for an already-imported region (e.g. "we have new 2026 numbers for Brandenburg"):

- [ ] Re-import overwrites in place — no version history kept
- [ ] Re-import creates a new "version" of Brandenburg; admins can switch between versions in the dropdown
- [ ] Re-import overwrites but the previous file is archived (per B4)

**Notes:** ___________________________________________________________

### E3. Deleting a region

- [ ] Admins should be able to delete a region from the UI (with a "are you sure" confirm)
- [ ] No, region deletion is a developer-only operation
- [ ] Delete is allowed only if no scenario / workspace references it

**Notes:** ___________________________________________________________

### E4. Renaming a region's `display_name`

(e.g. "Brandenburg" → "Brandenburg (Stand 2026)" without re-importing data)

- [ ] Admins should have a rename field
- [ ] Out of scope for Phase D — re-import is enough

**Notes:** ___________________________________________________________

### E5. Existing user workspaces when a region's data changes

When admin re-imports `BB.xlsx`, currently-active user workspaces on Brandenburg need to handle the data change. Each user has a per-`(owner, region)` workspace with their own modifications layered on top of the canonical region data. Choices:

- [ ] **Reset all BB workspaces** — users on Brandenburg lose their in-progress modifications and start fresh from the new baseline. Show a banner: *"Brandenburg-Daten wurden aktualisiert. Ihre Modifikationen wurden zurückgesetzt."*
- [ ] **Preserve user modifications** — modifications are kept; only the base values change. Users see a banner: *"Brandenburg-Basisdaten wurden aktualisiert. Ihre Anpassungen bleiben erhalten."* — but cascading recalculations may produce surprising values.
- [ ] **Block re-import while users are active** — show an error to the admin: "5 users are currently in Brandenburg workspaces. Wait or notify them first."
- [ ] **Soft cutover** — new logins start with new data; existing sessions keep old data until they re-load.
- [ ] No preference

**Notes:** ___________________________________________________________

### E6. Region versioning

Should each import create a numbered version of the region (e.g. `BB v3`, `BB v4`), or always overwrite the single current version?

- [ ] Always single current version — simpler
- [ ] Numbered versions, admin can switch between them in dropdown ("Brandenburg v3 (2026-04-22)" vs "v4 (2026-04-25)")
- [ ] Numbered versions kept for audit but only the latest is selectable
- [ ] No preference

**Notes:** ___________________________________________________________

---

## F. Operational concerns

### F1. Hosting platform — affects async-job design

The import takes a few seconds in the simple case but can grow if `_S.xlsx` is included (B2). On a single dyno (Heroku Basic) we'd run it inline; on a multi-worker setup (Heroku Standard / on-prem with multiple containers) we'd queue it.

- [ ] Heroku Basic (1 web + 1 worker, current dev setup) — inline is fine
- [ ] Heroku Standard / Performance — queue it via the existing `BalanceJob` worker pattern
- [ ] On-prem (your own machines) — which container orchestrator?: ___________
- [ ] AWS / Hetzner / other PaaS — which: ___________
- [ ] Decision pending — confirm by Phase 7 unblock

**Notes:** ___________________________________________________________

### F2. Backup strategy

- [ ] ErnES has its own DB backup strategy (which: ___________); we just need to log imports
- [ ] We need to add nightly DB snapshots as part of Phase D
- [ ] No backups required (test environment only)

### F3. Audit log retention

Per-import history (who, when, what file, how many rows changed). Retention period:

- [ ] 30 days
- [ ] 1 year
- [ ] Forever (until ErnES manually deletes)
- [ ] Compliance-driven — which regulation: ___________

### F4. Notifications

Should other admins be notified when one admin uploads a new file?

- [ ] No notifications — they'll see it in the audit log
- [ ] Email notification to all admins on every successful import
- [ ] Slack / Teams / other integration: ___________
- [ ] Only on errors

### F5. Concurrent uploads — two admins at once

If admin A uploads `BB.xlsx` while admin B uploads `NRW.xlsx` at the same time:

- [ ] Run them serially — second admin sees "Import in progress, please wait"
- [ ] Run them in parallel — they touch different regions so no conflict
- [ ] Only one import allowed system-wide at a time (simpler reasoning)
- [ ] No preference

If admin A and admin B BOTH upload `BB.xlsx`:

- [ ] First wins, second sees "Brandenburg was updated 30 seconds ago by admin A — refresh and reconsider"
- [ ] Last wins, no warning
- [ ] Block — error: "Concurrent edit on Brandenburg"
- [ ] No preference

### F6. Programmatic API

Some teams want to script imports (e.g. cron job: "every Monday, pull `D.xlsx` from `ernes.de` and re-import"). Should we expose a REST/HTTP endpoint with API-token auth alongside the GUI?

- [ ] Yes, add `POST /api/admin/regions/<code>/import/` with token-based auth
- [ ] Yes, but later (Phase E)
- [ ] No, GUI only

**Notes:** ___________________________________________________________

### F7. Sandbox / test environment before applying to production

Should there be a separate "test" mode where the upload runs against a copy of the DB so admins can preview the full app behaviour before committing?

- [ ] Yes — admins click "Test in Sandbox" first, then "Apply to Production"
- [ ] No — preview (D2) + dry-run (D3) are enough; no sandbox
- [ ] Sandbox only for first-time imports of a new region; in-place updates skip sandbox
- [ ] No preference

**Notes:** ___________________________________________________________

---

## G. Adjacent feature — per-cell admin edit

PDF §2.3.1 says *"Aktualisierungen … von ZeitzuZeit erforderlich, um das Tool einsatzbereit zu halten"* ("from time to time, parameter updates are required to keep the tool deployment-ready"). For *small* updates (e.g. fix one number on `LU_2.1`), re-uploading the whole Excel is heavy.

### G1. Should admins also be able to edit individual values directly in the web UI?

- [ ] Yes — add an admin mode to the existing pages where each cell is editable + audited
- [ ] No — re-upload is the only path; small fixes happen in Excel first
- [ ] Out of scope for Phase D — revisit later

### G2. If yes — does each edit need a justification text box (provenance)?

- [ ] Yes, mandatory text field "Why this change?" feeding the audit log + the popover Annahme
- [ ] Optional text field
- [ ] No justification required

---

## H. Documentation & training for admins

### H1. Format of the admin handover material

PDF §2.1 says *"Bildung von Hosting-Knowhow bei ErnES-AdministratorInnen (mindestens 2 Personen)"*. For the upload UI specifically:

- [ ] Written admin handbook in German (PDF or web page)
- [ ] Video walkthrough (5–10 min, German narration)
- [ ] In-app inline help (tooltips + an "?" overlay tour)
- [ ] Live training session (we run a 1-hour onboarding call)
- [ ] Combination — specify: ___________

**Notes:** ___________________________________________________________

### H2. Where the admin handbook lives

- [ ] Inside the web app at `/admin/help/` (always up-to-date with the deployed version)
- [ ] Separate document on `ernes.de` (decoupled from app deployments)
- [ ] Both — in-app brief + external long-form
- [ ] No preference

### H3. Sample data for training

For onboarding the ≥2 admins, do you want a fully synthetic "TEST" region they can practice imports on without affecting real DE / Bundesland data?

- [ ] Yes, ship a TEST region in the deployed app for training (currently exists — see commit `6dfc2ed`)
- [ ] No, training happens once on the real platform; admins are careful
- [ ] Yes, but in a separate staging environment (not in the production app)

**Notes:** ___________________________________________________________

---

## I. Compliance, privacy, retention

### I1. GDPR considerations

The data being uploaded is energy/parameter data — not personal data. Confirm:

- [ ] Confirmed — no GDPR / personal-data implications for the upload
- [ ] There IS personal data in the upload — specify: ___________
- [ ] We need a data-protection sign-off before deploying — who: ___________

### I2. Source attribution requirements

PDF §2.3.1 emphasises *"Quellbezüge und zugrundeliegende Annahmen"* (source references and underlying assumptions). The current import already populates `source_url` and `notes_assumption` from `D.xlsx!9.Quellen` and the per-cell comments. For Phase D, should the upload form:

- [ ] Reject files where `9.Quellen` is empty or missing (force ErnES to maintain provenance)
- [ ] Warn but allow (orphans without provenance show a "no source" badge in the UI)
- [ ] Don't enforce — trust the file

**Notes:** ___________________________________________________________

---

## J. Anything else?

Open question for ErnES — anything we haven't asked that you'd want the upload UI to do or NOT do?

```
[ free text ]
```

---

## What we'll do with the answers

Once ErnES returns this filled in, the work breaks down approximately:

| Section | Affects |
|---|---|
| A — Auth | Login flow + permission decorator on the upload view + UI language pack |
| B — Files | Form layout, validator, archival path, accepted formats, round-trip export |
| C — Region constants | Form fields + DB schema additions to `Region` + `WSData` ingest path |
| D — Validation | Error message design + preview view + diff display + provenance preservation policy |
| E — Lifecycle | Number of distinct admin views (create / update / delete / rename) + workspace-cutover behaviour + version model |
| F — Ops | Sync vs async job, backup tooling, audit log schema, integrations, concurrency model, programmatic API, sandbox mode |
| G — Per-cell edits | Out of scope unless requested — separate target |
| H — Docs | Format of admin handover (PDF / video / in-app / live session); where it lives; sample-data setup |
| I — Compliance | GDPR confirmation; source-attribution enforcement level |

We expect the form itself to be ~1–2 days once these are answered, plus 0.5 day for V4/V5 verification + handbook entry. Each "Yes" answer in G or in section F (sandbox, programmatic API, version history) adds another 1–3 days. The largest cost drivers are E5 (workspace cutover behaviour — touches `workspace_service.py` and signal flow) and E6 (region versioning — schema migration plus a versioned read path everywhere `region` is queried).

---

## Returning your answers

Email the filled-in document back to **Pascal Leinfelder** (`Pascal@leinfelder.me`) or **Deepti**. We'll fold the decisions into a Phase D scope doc, then schedule the build to land alongside Phase 7 onboarding (so you can start using it in real onboarding, not in isolation).
