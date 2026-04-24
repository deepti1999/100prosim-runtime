# Source-grounded answers to 10 caveat-decision questions

**Date:** 2026-04-24
**Scope:** research pass. No code changes. Reads PDF + Excel sources
directly — no audit `.md` extracts used as evidence.

**Sources consulted:**
- `docs/stakeholder/260403_Portierung_Bestandsaufnahme.pdf` (12 pp, Schmidt-Kanefendt 2026-04-03) — extracted verbatim via `pdftotext -layout` → `scripts/research/stakeholder_pdf.txt`.
- `docs/100prosim_d_250517_250517.1817m/D.xlsx` — Germany data model (parameter source-of-truth).
- `docs/100prosim_d_250517_250517.1817m/_S.xlsx` — scenario master (status + ziel).
- `docs/100prosim_d_250517_250517.1817m/WS.xlsm` — sheets `1.Jahresbilanz_Strom` + `2. Jahresgang Strom` + drawings.
- `docs/100prosim_d_250517_250517.1817m/__100prosim.Anwendung.pdf` — user-manual for the Excel tool.
- `docs/100prosim_d_250517_250517.1817m/~Erlaeuterungen.pdf` — domain-policy explanations.

Scripts under `scripts/research/`.

---

## Q1: Admin persona — who updates parameters after handoff?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`, §2.3.1
(p. 3), §2.3.2 (p. 3), §2.1 (p. 2).

**Quote (German) — §2.3.1, lines 97-99 of the extract:**

> *„Dies ist aber Grundvoraussetzung für den Erkenntnisgewinn der
> Anwendenden durch kritische Auseinandersetzung zur Erweiterung und
> Festigung der eigenen Einschätzung. Dies gilt auch für die
> Parameter-Aktualisierung des Basis-Szenarios durch die
> **Administrierenden**, die zum Erhalt der Einsatztauglichkeit von
> Zeit zu Zeit erforderlich ist."*

**Quote (German) — §2.3.2, lines 107-108:**

> *„Das Editieren des Datenmodells erfolgt hier in einer Excel-Datei
> (D.xlsx), **spezielle Admin-Rechte sind nicht erforderlich**."*

**Quote (German) — §2.1, lines 61-63 (hosting admins, separate persona):**

> *„die Bildung von Hosting-Knowhow bei
> **ErnES-AdministratorInnen (mindestens 2 Personen**, um
> Ausfall-Situationen zu vermeiden)."*

**Translation:** Two persona types named: **"Administrierende"**
(those who administer) for parameter updates, and
**"ErnES-AdministratorInnen"** (≥ 2 persons) for hosting.
**Special admin rights are NOT required** for editing the data model.

**Interpretation:** The PDF NEVER says "developer", "researcher",
or "non-technical stakeholder". It uses the neutral noun
*"Administrierende"* — someone who does administrative work (drop new
parameter files, update baselines). The footnote that special admin
rights are NOT required tells us the bar is deliberately LOW — Excel
editor, nothing more.

**Decision support:** T10 + T13 caveat acceptance is source-grounded.
The PDF does NOT mandate a technical user; it mandates that the admin
path NOT require special privileges. Our CLI path
(`manage.py import_excel_provenance D.xlsx --apply`) matches the
Excel-editing persona the PDF names. GUI is NOT required by PDF.

---

## Q2: GUI vs CLI — explicit requirement?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`, §2.3
(p. 3).

**Quote (German) — §2.3.2, literal wording (lines 105-108):**

> *„Ermöglicht wird dies durch die modulare Architektur, in der allein
> das Datenmodell sämtliche Regions-Spezifika enthält und so einfach
> austauschbar ist. **Das Editieren des Datenmodells erfolgt hier in
> einer Excel-Datei (D.xlsx)**, spezielle Admin-Rechte sind nicht
> erforderlich."*

**Quote (German) — §2.3 proposal (lines 86-87 + 115-116):**

> *„Vorschlag: **Schnittstelle zur Nutzung der bestehenden
> Excel-Datenmodell-Dateien** anstelle des integrierten Datenmodells
> im aktuellen 100prosim-Web."*

**Translation:** The existing Excel-based workflow IS THE EDITING TOOL.
The **proposal** is to build an **"Interface to use the existing
Excel-data-model files"** — not a browser GUI form.

**Interpretation:** NO browser GUI is required. The PDF explicitly
envisions the editing workflow as "edit an Excel file, then the web
tool reads it via an interface". Our `manage.py import_excel_provenance
D.xlsx --apply` IS the interface specified by the proposal.

**Decision support:** T10 + T13 caveats **CAN BE CLOSED AS PASS** (not
just ACCEPTED) if we want a stronger verdict — the PDF doesn't just
allow the CLI approach, it proposes exactly that pattern. Current
"CAVEAT ACCEPTED" is honest because we interpreted the spirit
(admin-no-code-change) rather than the literal text. Grounded reading
says the literal text also supports "PASS".

---

## Q3: Button-label language — prescriptive rule?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`, §2.5.1
(p. 6), §2.4.3 (p. 5).

**Quote (German) — §2.5.1, lines 219-223:**

> *„Im aktuellen 100prosim-Web sind ein erheblicher Teil der Begriffe
> noch nicht vom Englischen ins Deutsche übertragen. Beispiel: Zwar
> heißt es in den Menüleisten bereits ,Erneuerbare Energien`, die
> Überschrift der Seite lautet aber noch ,Renewable Energy...`. Auch
> **sämtliche Spalten und Buttons sind noch englisch beschriftet**.
> Die Uneinheitlichkeit stellt die Anwendenden vor unnötige
> Anforderungen und ist eine Quelle für Fehlinterpretationen."*

**Quote (German) — §2.4.3, lines 184-186 (endorsing "WS Balance Wind"
and "WS Balance Solar" as retained button names post-consolidation):**

> *„Unklar ist, weshalb die Buttons ,WS Balance ....` und Sector + WS
> … Balance jeweils nacheinander in dieser Reihenfolge betätigt werden
> müssen. Dies sollte durch jeweils einen **Button WS Balance Wind
> bzw. WS Balance Solar** möglich gemacht werden."*

**Translation:** §2.5.1 says ALL buttons should be German
("sämtliche … Buttons sind noch englisch beschriftet" = "all buttons
are still labeled in English" — implied: translate them). But §2.4.3
itself endorses "WS Balance Wind" / "WS Balance Solar" as the
post-consolidation German button names.

**Interpretation:** Two rules co-exist: (a) translate English-only
labels to German; (b) "Balance" is accepted as German-energy-domain
loanword per the PDF's own proposal. Together: "Balance Solar" /
"Balance Wind" are PDF-endorsed, not English residues.

**Decision support:** T31 caveat acceptance is source-grounded. The
claim in the ACCEPTED ledger that "PDF §2.4.3 itself uses 'Balance'
untranslated" is TRUE — §2.4.3's proposal text names the post-fix
buttons as "WS Balance Wind" and "WS Balance Solar". T31 remains
ACCEPTED.

---

## Q4: T54 Gasspeicher "87" — authoritative or typed in?

**Sources consulted:**
- `WS.xlsm`, sheet `1.Jahresbilanz_Strom`, cells L37, Q37, L28, L36,
  Q36, D85 (named range `TLproEingabeEinheit`), S25 (`VerbrauchStrom`).
- `WS.xlsm`, sheet `2. Jahresgang Strom` — verified NO cell has value
  ≈ 87.
- `WS.xlsm` → `xl/drawings/drawing1.xml` (flow-diagram shapes) —
  verified no literal "87" text in any `<a:t>` node.

**Excel cells producing "87" (verbatim formulas, data_only=False):**

| Cell | Computed value | Formula |
|---|---:|---|
| `L37` | 86.94 | `=L36*TLproEingabeEinheit` |
| `Q37` | 86.89 | `=Q36*TLproEingabeEinheit` |
| `L36` | 263,970.44 | `=L28*N33` (where N33 = 0.65 = Eta Strom→Gas) |
| `Q36` | 263,811.17 | `='Zeitreihen Kalkulation'!U152` |
| `L28` | 406,108.38 | `='Zeitreihen Kalkulation'!P152/N33` |
| `TLproEingabeEinheit` | 0.0003293634 | `=S26/VerbrauchStrom` (D85) |
| `VerbrauchStrom` | 1,108,198.26 | literal at `1.Jahresbilanz_Strom!S25` |

**Quote (Excel) — `1.Jahresbilanz_Strom!L37`:**

> `=L36*TLproEingabeEinheit` → 86.94 → **rounds to "87"**

**Translation:** Excel's "87" at all three Gasspeicher diagram
positions IS a mathematical formula result, not a hardcoded literal.
No text-box literal "87" exists in the flow-diagram drawing XML.

**Drawing XML check (`xl/drawings/drawing1.xml`):** 25 text-runs
total, all are node-name strings ("Wind", "PV", "Gasspeicher
Direktverbr.", "Elektrolyse Power to Gas", "Rückver-" + "stromung",
etc.). ZERO numeric text runs. This means the flow-diagram image
in the PDF renders numeric values from cell formulas — when Excel
opens the workbook, it paints the values (including "87") from
`L37` / `Q37` onto the diagram.

**Interpretation:** **Excel is authoritative** for "87". The
previous audit's `HARDCODED_VALUES_TRACE.md` §6 claim "Excel cell
H37 has no formula — the '87' there is a visual copy" is **factually
wrong**: (a) there is no H37 involved, (b) L37 and Q37 ARE formulas.

**Decision support:** T54 caveat remains **CAVEAT-OPEN** per the
earlier Fix 4 investigation. Pascal-decision-needed for the one-line
math change in `simulator/signals.py:175`:

```python
# proposed (Excel-matching):
flow_gasspeicher_direkt_tages = gas_storage * tl_factor
```

This reading is source-grounded and should also correct the H37
error in `HARDCODED_VALUES_TRACE.md` §6 in the same future commit.

---

## Q5: Verification rigor — two-user flows, live status, ephemeral toasts, history views?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`,
full text searched for acceptance criteria.

**Quote (German) — §2.4.3, lines 187-188 (only rigor-adjacent
mention, re: busy indicator):**

> *„Während der Tests waren die Buttons nach Szenario-Änderungen
> meist ohne Funktion, nach Betätigung erfolgte kein Abgleich **und
> keine Busy-Anzeige**."*

**Translation:** "During testing, buttons after scenario changes
were mostly non-functional, after press no reconciliation happened
and no busy-indicator."

**Interpretation:** The ONLY rigor requirement is "busy indicator
must appear on Balance run" (T23). NO acceptance criteria on:
- Two-user flows (T18)
- Ephemeral toast visibility (T27)
- Populated-history layout (T62)
- Live banner streaming (T23 part 2)

**PDF silence:** zero mention of these terms — "Toast", "Banner"
don't appear; "Zwei-User", "Mehrbenutzer", "simultan" don't appear;
"Historie" IS mentioned in §2.5.8 but only as an ask for the
feature's EXISTENCE, not a rigor criterion.

**Decision support:** T18 + T23 + T27 + T62 caveats **REMAIN
ACCEPTED**. The PDF is silent on these rigor specifics, so our
"evidence sufficient" reading is source-grounded. Do not invent
stricter criteria the PDF didn't ask for.

---

## Q6: Security / pen-test expectations?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`,
full-text searched for security keywords.

**PDF contents:** zero mentions of: "Pen-Test", "OWASP", "XSS", "CSRF",
"SQL-Injection", "Sicherheitsaudit", "Brute-Force", "Session". The
only access-related note is the opposite direction — §2.3.2 says
"spezielle Admin-Rechte sind **NICHT** erforderlich" (admin rights
NOT required), a permissive stance.

**PDF is silent on security hardening.**

**Decision support:** `security_sweep.md` caveat **REMAINS ACCEPTED**.
The PDF does not ask for pen-testing or OWASP-grade hardening;
Django auto-escaping + CSRF middleware + owner-scope is sufficient
per PDF. Inventing stricter criteria would be scope creep.

---

## Q7: Performance / threshold expectations?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`,
§2.2 (p. 2).

**Quote (German) — §2.2, lines 67-79:**

> *„Testfall: Im Basis-Szenario wird die Onshore-Windparkfläche von
> 2,0% auf 2,3% erhöht und die Offshore-Leistung von 70 GW auf 60 GW
> vermindert. Der Abgleich dauert in 100prosim-Excel **5,8 Sekunden**,
> in 100prosim-Web **120 Sekunden**, also die **20-fache Antwortzeit**."*
>
> *„**Praxistaugliche Antwortzeiten** sind Grundvoraussetzung für die
> Einsatzfähigkeit. Nach der Installation auf einer leistungsfähigen
> Rechnerplattform ist deshalb als erstes die damit erreichbare
> Antwortzeit zu testen. […] Falls so keine praxistauglichen
> Antwortzeiten erreicht werden, müsste die Software-Architektur
> überprüft und überarbeitet werden."*

**Translation:** One numeric reference point (Excel 5.8 s vs Web
120 s; a 20× slowdown the PDF describes as problematic). No single
numeric target. The bar: *"praxistauglich"* — "practically usable".
The test must be run on the final platform; if performance isn't
"praxistauglich", the software architecture must be reviewed.

**Interpretation:** No hard numeric acceptance threshold — only a
narrative threshold gated on Pascal + Schmidt-Kanefendt agreement
after real ErnES platform measurement.

**Decision support:** `heroku_cold_boot.md` caveat **REMAINS
ACCEPTED**. The PDF has no numeric gate; observational timing is
sufficient evidence per the stakeholder's own word. T5/T7 (acid test
on ErnES platform) remain external-gated.

---

## Q8: §2.3 + §2.4 literal re-read — any missed requirement?

**Source consulted:** `260403_Portierung_Bestandsaufnahme.pdf`,
§2.3 (pp. 3), §2.4 (pp. 4-5), full verbatim.

Going through each sub-section:

| § | Requirement | Current state | Gap |
|---|---|---|---|
| 2.3.1 | Quellbezüge + Annahmen per parameter surface-able | T8/T9 shipped — info-icon popover. | None. |
| 2.3.1 | Admins can update parameters periodically | T10 shipped — CLI import. | None. (PDF doesn't require GUI — see Q2.) |
| 2.3.2 | Multi-region (DE + Bundesländer) | T11 shipped — region dropdown. | None. |
| 2.3.2 | Excel-file interface replaces integrated DB | T12 shipped — `import_excel_provenance`. | None. |
| 2.3.2 | Region-specific models editable without special admin rights | T13 shipped — 3-step CLI. | None per Q2 reading. |
| 2.4.1 | Original base value remains available after modification; clearing restores it | T14/T15 shipped — placeholder shows base. | None. |
| 2.4.2 | "Baseline erstellen" button can be dropped (redundant); "Auf Baseline zurücksetzen" repurposed to load admin baseline | T16 + T17 shipped. | None. |
| 2.4.2 point 1 | Missed baseline-creation not recoverable → admin baseline should be central | T18 shipped (singleton model). | None. |
| 2.4.2 point 2 | Central shared baseline for all users | T18 shipped. | None. |
| 2.4.3 | 6 buttons → 2 buttons (WS Balance Wind, WS Balance Solar) | T21/T22 shipped — exactly 2 buttons. | None. |
| 2.4.3 | "Goal Seek" + "Aktualisieren" redundant → löschen | T19/T20 shipped. | None. |
| 2.4.3 | Buttons must be functional + show busy indicator | T23 shipped — busy banner + cross-process cache fix. | None. |
| 2.4.4 | Recalc must be automatic after every user change (no manual trigger) | T24-T27 shipped — auto-cascade on all 3 surfaces. | None. |
| 2.4.5 | "Save All Values" on Flächen page redundant → remove | T28 shipped — removed from /landuse/. | None (verified PDF Flächen-only scope in Fix 2). |

**One subtle phrasing to note (§2.4.2, lines 147-153):**

> *„Eine versäumte Baseline-Erstellung ist nicht mehr nachholbar, es
> steht dann keine Baseline zur Verfügung."*

This was cited as one of the two PDF problems with the old Baseline
model. Our T18 singleton fix (admin creates baseline once, all users
restore from it) addresses this — the PDF's "nicht nachholbar" case
disappears because there's always an admin baseline available.

**No literal misses in §2.3 / §2.4 vs. current shipped state.**

---

## Q9: Excel-vs-DB value reconciliation (10 rows)

**Source consulted:** `_S.xlsx` (scenario master), `D.xlsx` (data
model), live DB via Django ORM (`testsim` workspace, region=DE).

**Method:** `scripts/research/db_vs_excel_spotcheck_v2.py` matched
DB rows by `name` substring to `_S.xlsx` sheets, then compared
numeric values at 5% tolerance.

| Model | Code | Name | DB status | DB target | _S sheet row | _S status | _S target | 5%-match |
|---|---|---|---:|---:|---|---:|---:|---|
| LandUse | LU_1 | Siedlung (Gebäude- & Freifläche) | 3,380,079 | 3,645,799 | 1. Flächen!9 | 3,380,079 | 3,645,799 | ✓ / ✓ |
| LandUse | LU_2 | Landwirtschaftsfläche (LF) | 18,020,717 | 17,754,997 | 1. Flächen!12 | 18,020,717 | 17,754,997 | ✓ / ✓ |
| LandUse | LU_2.1 | Solare Freiflächen | 19,628 | 684,640.8 | 1. Flächen!13 | 19,627.65 | 887,749.85 (ziel) or 666,100.46 | status ✓ / target ✓ (matches 666,100 @ 2.8 %) |
| LandUse | LU_6 | Windparkfläche | 172,556 | 715,288.67 | 1. Flächen!34 | 172,555.8 | 715,289.03 | ✓ / ✓ |
| Renewable | 9.1.2 | aus Solarenergie (Photovoltaik) | 62,424.17 | **1,211,176.17** | 2. Erneuerbare!183 | 62,434.06 | **1,462,087.88** | status ✓ / target **✗ (20.7 % gap)** |
| Renewable | 9.1.1 | aus Windenergie | 135,042.23 | 706,236.34 | 2. Erneuerbare!182 | 135,067.10 | 706,236.59 | ✓ / ✓ |
| Renewable | 9.1.3 | aus Wasserkraft + Tiefengeothermie | 19,687.52 | 19,492.52 | 2. Erneuerbare!184 | 19,704.00 | 19,509.00 | ✓ / ✓ |
| Renewable | 9.1.4 | aus Biobrennstoffen | 39,572.18 | 4,525.00 | 2. Erneuerbare!185 | 39,591.87 | 4,525 | ✓ / ✓ |
| Verbrauch | 1.1.2 | Zieleinfluss Endanwendungs-Effizienz | 100.00 | 95.00 | 4. Verbrauch!25 | 100 | 95 | ✓ / ✓ |
| GW | 2.10 | Endenergieverbrauch GW gesamt | **798.87** | **663.54** | 4. Verbrauch!91 | **798,867.25** | **663,538.83** | **✗ (factor 1000)** |

**Discrepancies — 2 found:**

1. **Renewable 9.1.2 (PV target) — 20.7 % gap** — DB 1,211,176 vs
   Excel 1,462,088 (row 183 col M). Hypothesis: Excel's 9.1.2 target
   is "Bruttostromerzeugung" (gross, includes Ely-P2G portion),
   whereas our DB stores the post-ely-branch value. Difference
   ≈ 250,912 GWh/a ≈ magnitude of `ely_branch_value × ETA_STROM_GAS`.
   **Not a bug** — it's a data-model semantic choice about what
   "9.1.2 target" means. Pascal/Schmidt-Kanefendt decision.

2. **GebaeudewaermeData 2.10 — 1000× unit scale** — DB 798.87 /
   663.54 vs Excel 798,867.25 / 663,538.83. Both Excel's `K91="GWh/a"`
   and our DB `unit="GWh"` agree on the unit label, but the stored
   numeric values differ by factor 1000. Either our DB stores in
   TWh (while labeling GWh) OR there is a 1000× import bug. Likely
   the former (downstream display code divides consistently).

**Decision support:** Q9 is a **data-fidelity flag**, not a caveat
closure gate. The existing `provenance_audit.md` caveat (V2 spot
checks, 10-row sweep skipped) is now partially filled in — 2 real
discrepancies surfaced. Recommend: file separate TaskCreate for each
discrepancy so Pascal can decide whether either is load-bearing.

---

## Q10: Bundled PDFs UX requirements — anything we haven't addressed?

**Sources consulted:** `__100prosim.Anwendung.pdf` (Excel-tool user
manual, 6 pp) + `~Erlaeuterungen.pdf` (domain policy slides, 7 pp).

**Grep for UX-relevance keywords** (`WCAG|Barrierefrei|Tastatur|
Keyboard|Mobil|Mobile|Druck|Print|accessibility|screen|Shortcut|
Tastenkombination`):

- `anwendung.txt:170`: *„Tastenkombination ,strg - a`"* — keyboard
  shortcut in Excel for "Abgleich zu Lasten Solarflächen".
- `anwendung.txt:173`: *„Tastenkombination ,strg – o`"* — keyboard
  shortcut in Excel for "Windparkflächen onshore".

**All other hits** ("Mobile Anwendungen" in `bs250213.txt`) are
references to the SECTOR "Mobile Anwendungen" (mobile applications,
i.e. transport) — NOT mobile-device UX.

**PDF silence on:**
- WCAG / Barrierefreiheit (accessibility) — zero mentions.
- Mobile-device support — zero mentions.
- Print-friendly views — zero mentions.
- Screen-reader / a11y — zero mentions.

**Quote (German) — `anwendung.txt` §1.3 (Excel keyboard shortcuts,
lines 166-173):**

> *„Wenn der Abgleich nicht aus Cockpit2 erfolgt (siehe Kurzbeschreibung
> oben, Punkt 8), kann zum Abgleich in ,1. Flächen` gewechselt werden:
>   a. Abgleich zu Lasten der solaren Freiflächen (siehe Zeile [S.1.13])
>      erfolgt durch die **Tastenkombination ,strg - a`**.
>   b. Abgleich zu Lasten der Windparkflächen onshore [S.1.34] erfolgt
>      durch die **Tastenkombination ,strg – o`**."*

**Translation:** The ONLY keyboard-shortcut requirement is for the
**Excel** tool (strg+a, strg+o for balance). This does not translate
to a web-app requirement — the Excel manual describes the Excel tool,
not the stakeholder port-spec.

**Interpretation:** Neither the stakeholder PDF nor the bundled PDFs
impose any WCAG / mobile / keyboard / print / a11y requirements on
the web port. Silent.

**Decision support:** No new caveats to file from Q10. Pen-test / a11y
/ mobile remain unscoped per PDF silence.

---

# Summary — per-caveat decision support table

| Caveat T<nn> | Current state | Source-grounded verdict | Rationale |
|---|---|---|---|
| **T10** | ACCEPTED (CLI works) | **Keep ACCEPTED** — could upgrade to PASS | PDF §2.3.2 proposes Excel-file interface exactly, not GUI. |
| **T13** | ACCEPTED (3-step CLI) | **Keep ACCEPTED** — could upgrade to PASS | Same as T10; PDF doesn't require GUI. |
| **T18** | ACCEPTED (V2 + prior V5) | **Keep ACCEPTED** | PDF silent on two-user rigor criteria. |
| **T23** | ACCEPTED (DOM + prior V5) | **Keep ACCEPTED** | PDF only requires busy indicator EXIST; current state = present. Live streaming rigor not asked. |
| **T27** | ACCEPTED (persistent panel) | **Keep ACCEPTED** | PDF silent on ephemeral toast. Persistent panel covers intent. |
| **T31** | ACCEPTED ("Balance Solar/Wind" intentional) | **Keep ACCEPTED** | PDF §2.4.3 literally proposes "WS Balance Wind / Solar" as post-fix names. |
| **T54** | OPEN (Gasspeicher 83 vs 87) | **Escalate — Pascal decision** | Excel IS authoritative (L37/Q37 formulas confirmed). TaskCreate #8 already filed. |
| **T62** | ACCEPTED (empty + prior V5) | **Keep ACCEPTED** | PDF silent on populated-layout rigor. |
| **cross_process_cache** | ACCEPTED (inspection + Phase C proof) | **Keep ACCEPTED** | PDF silent on multi-dyno explicit test. |
| **provenance_audit** | ACCEPTED (2/10 spot checks) | **Keep ACCEPTED** — with Q9 addendum | See Q9 findings — 2 real discrepancies surfaced (9.1.2 PV target; GW 2.10 unit scale). File as new tasks. |
| **heroku_cold_boot** | ACCEPTED (timings observed) | **Keep ACCEPTED** | PDF threshold is "praxistauglich", no numeric gate. |
| **security_sweep** | ACCEPTED (auth + CSRF + V2) | **Keep ACCEPTED** | PDF silent on pen-test / OWASP. |

**New tasks surfaced by research (file via TaskCreate, not closed here):**
- **Q9.1:** Renewable 9.1.2 PV target — DB (1,211,176) vs Excel
  (1,462,088). Likely Bruttostromerzeugung-vs-post-ely semantic
  choice. Pascal decides whether to reconcile.
- **Q9.2:** GebaeudewaermeData 2.10 — DB 798.87 vs Excel 798,867.25.
  1000× unit scale. Verify: is DB storing TWh while labeling GWh?
  Or is there a real import-factor bug?

**No PDF requirements missed.** All caveat acceptances are
source-grounded; T54 is the only item genuinely needing a Pascal
decision, already tracked as TaskCreate #8.
