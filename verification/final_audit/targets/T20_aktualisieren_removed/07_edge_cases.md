# T20 — Edge cases

1. **Stale summary cards:** `refreshWsSummaryCards()` runs at page open + immediately after a Balance job finishes (banner state-change hook), so manual refresh is no longer necessary.
2. **Slow Heroku worker:** banner stays "Status: queued" until the job completes; once succeeded, summary cards auto-refresh. Verified via `eb5a6ae` 4-D banner work.
3. **Browser back/forward:** revisit /ws/ → `DOMContentLoaded` fires → auto-refresh runs again. No stale-data window.
