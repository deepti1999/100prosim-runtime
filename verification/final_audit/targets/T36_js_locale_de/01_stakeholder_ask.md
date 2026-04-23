# T36 — JS-rendered numbers in German locale

**PDF §2.5.2 (implied):** JS-rendered numeric displays (Chart.js, dynamic banner text) must also use German format — otherwise inconsistent with server-rendered.

**Acceptance:** `toLocaleString('de-DE')` (or equivalent) used in all JS that formats numeric output.
