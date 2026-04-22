# Flussdiagramm Strom / H₂ — audit vs Excel reference

**Phase 5-C (T53, T54, T55, T56).** Stakeholder PDF §2.5.6 complaint:

> "Auch nach einer ersten Überarbeitung bildet die Grafik die dem Szenario
> zugrundeliegenden Strukturen noch nicht korrekt ab, teilweise sind die
> Werte falsch zugeordnet und wegen der kleinen Schriftart ist das
> Diagramm schlecht lesbar."

## What shipped in Phase 5-C

### T55 — Legibility (fixed)

- Font-size classes bumped ~20–30 % across the SVG:
  | class | before | after |
  |---|---|---|
  | `txt-title` | 20 | 24 |
  | `txt-label` | 12 | 14 |
  | `txt-label-lg` | 16 | 19 |
  | `txt-value` | 16 | 18 |
  | `txt-flow` | 15 | 17 |
  | `txt-node` | 18 | 20 |
  | `txt-metric` | 12 | 14 |
- New zoom controls above the SVG: 75 % / 100 % / 125 % / 150 % / 200 %.
  Uses CSS `transform: scale()` with proportional width/height so the
  scroll container reserves the right space.

### T53 — Node-by-node audit vs Excel

Current `annual_electricity.html` SVG nodes, mapped to the Excel
reference (PDF page 10):

| Excel node (page 10) | SVG element / id in our template |
|---|---|
| Bedarfs-Kraftwerke / Biobrennstoffe | `#bio_value` — yellow rect top-left |
| PV (fluktuierend) | `#pv_value` — yellow rect, mid-left |
| Wind (fluktuierend) | `#wind_value` — yellow rect below PV |
| Laufwasser + Tief.-Geoth. (konstant) | `#hydro_value` — yellow rect, bottom-left |
| M (Bruttostromerzeugung summer) | `#m_value` — circle at centre |
| Abregelung (Q) | `#q_value` |
| Elektrolyse Power to Gas, 65 % Eta Ely. | `#ely_branch_value` / `#ely_offer_value` / `#eta_ely_value` |
| Gasspeicher Direktverbr. | `#gasspeicher_direkt_value` |
| Elektrolyse Stromspeicher (Überschuss), 65 % Eta ES | `#n_value_svg` / `#n_output_branch_value` / `#eta_es_value` / `#ely_surplus_value` / `#h2_surplus_value` |
| Gasspeicher Strom | `#gas_storage_arrow_value` |
| Speicherkapazität | `#storage_capacity_value` |
| Rückverstromung (Mangelausgl.), 59 % Eta RS | `#t_value_svg` / `#eta_rs_value` / `#reconversion_value` |
| Stromnetz zum Endverbrauch | `#final_value` + `#o_value_svg` |

All 13 Excel nodes are **structurally present** in our SVG. Structure
check passes.

### T54 — Value-to-node assignments (read-only audit, 2026-04-22)

Pascal provided his local Excel bundle
(`docs/100prosim_d_250517_250517.1817m/`, gitignored). Read-only
extraction with openpyxl from `WS.xlsm`, sheet `1.Jahresbilanz_Strom`,
scenario **"Deutschland 100%EE" (250517)**. **No code edits yet** —
findings below are for Pascal's review.

#### Structural mapping (Excel cell → backend var → SVG id)

| Excel | Label | Excel value | Backend var | SVG id | Computation | Match |
|---|---|---:|---|---|---|---|
| E13 | S (Bio) | 4 525 | `bio_value` | `#bio_value` | `RenewableData[9.1.4]` | ✓ |
| E19 | K (PV) | 1 205 268 | `pv_value` | `#pv_value` | `RenewableData[9.1.2]` | ✓ |
| E25 | J (Wind) | 706 236 | `wind_value` | `#wind_value` | `RenewableData[9.1.1]` | ✓ |
| E31 | L (Hydro) | 19 509 | `hydro_value` | `#hydro_value` | `RenewableData[9.1.3]` | ✓ |
| H25 | M (Bruttostromerzeugung) | 1 931 013 | `m_total` | `#m_value` | `pv + wind + hydro` | ✓ (1 205 268 + 706 236 + 19 509 = 1 931 013) |
| H28 | P (Elektrolyse input) | 385 933 | `ely_branch_value` | `#ely_branch_value` | `RenewableData[9.2.1.5.2]` | ✓ |
| H36 | Gasspeicher Direktverbr. | 250 856 | `gasspeicher_direkt` | `#gasspeicher_direkt_value` | `ely_branch × 0.65` = 385 933 × 0.65 = 250 856 | ✓ |
| J25 | N (horizontal flow) | 1 545 080 | `n_value` | `#n_value_svg` | `m_total − ely_branch` = 1 931 013 − 385 933 = 1 545 080 | ✓ |
| L23 | Q (Abregelung) | 189 627 | `q_abregelung` | `#q_value` | `WS365 abregelung_sum` | ✓ structural |
| L28 | P′ (Eta ES input) | 406 108 | `n_output_branch` | `#n_output_branch_value` | `einspeich_sum / 0.65` | ✓ |
| L36 | Gasspeicher Strom (via ES) | 263 970 | `gas_storage` | `#gas_storage_arrow_value` | `n_output_branch × 0.65` = 406 108 × 0.65 = 263 970 | ✓ |
| N25 | O (after Abreg. + ES) | 949 343 | `n_to_right` | `#o_value_svg` | `n_value − q_abr − n_output_branch` = 1 545 080 − 189 627 − 406 108 = 949 345 | ✓ (rounding) |
| Q36 | T (Rückverstr. input) | 263 811 | `t_value` | `#t_value_svg` | `WS365 ausspeich_sum` | ✓ structural |
| Q28 | Rückverstr. output (58.5 %) | 154 330 | `reconversion` (`t_output`) | `#reconversion_value` | `t_value × 0.585` = 263 811 × 0.585 = 154 329 | ✓ |
| S25 | I (Stromnetz zum Endv.) | 1 108 198 | `final_stromnetz` | `#final_value` | `o + bio + t_value × 0.585` = 949 343 + 4 525 + 154 329 = 1 108 197 | ✓ |
| K33 | Eta Ely | 0.65 | `eta_ely_pct` | `#eta_ely_value` | `ws_const ETA_STROM_GAS` | ✓ |
| N33 | Eta ES | 0.65 | `eta_es_pct` | `#eta_es_value` | `ws_const ETA_STROM_GAS` | ⚠ see (1) |
| S33 | Eta RS | 0.585 | `eta_rs_pct` | `#eta_rs_value` | `ws_const ETA_GAS_STROM` | ✓ |
| M12 | Eta Stromspeicherung | 38.0 % | `eta_storage_pct` | `#eta_storage_value` | `t_output / n_output_branch × 100` = 154 329 / 406 108 = 38.0 % | ✓ |
| M44 | Speicherkapazität | 242 467 GWh | `storage_capacity` | `#storage_capacity_value` | `max(ladezust_abs_vorl_tl)` across 365 days | ✓ structural |

**Every labelled Excel node has a structurally correct backend-var and
SVG-id binding.** All arithmetic formulas reproduce the Excel numbers
to within rounding when fed the same inputs.

#### Concerns worth Pascal's decision

1. **Eta Ely vs Eta ES share one constant.** Excel `K33` (Eta Ely) and
   `N33` (Eta ES) happen to both be `0.65` in this scenario, but the
   backend pulls **both** from the single ws-constant `ETA_STROM_GAS`.
   If Schmidt-Kanefendt ever wants Eta Ely ≠ Eta ES, the WS-constant
   table needs a new key and `page_renewable.annual_electricity_view`
   needs a second ws-constant lookup. Low risk today, latent
   extensibility gap.

2. **N-branch node label conflates two Excel concepts.** The SVG rect
   at `x=585,y=500` is labelled *"Elektrolyse Stromspeicher"* with
   sub-label *"(Überschuss)"*. Excel shows these as **two separate
   boxes** on page 10: "Elektrolyse" (`K33` block) and "Stromspeicher"
   (`N33` block). Functionally our single box carries the correct
   value (`n_output_branch` = 406 108 → L28) but the label is a visual
   merger. This may be exactly what the stakeholder meant by
   *"bildet ... Strukturen noch nicht korrekt ab."*

3. **`gas_storage_arrow_value` vs `gasspeicher_direkt_value`** —
   these are **two different flows** correctly wired to two different
   SVG elements:
   - `#gasspeicher_direkt_value` = H36 path (Ely → Gasspeicher Direkt)
     = 250 856
   - `#gas_storage_arrow_value` = L36 path (ES → Gasspeicher Strom)
     = 263 970
   This is structurally correct but the visual proximity of the two
   numbers can be confusing. Worth double-checking the arrow routing on
   the rendered diagram.

4. **`r941.target_value` side-effect in the GET.** `annual_electricity_view`
   writes `RenewableData[9.4.1].target_value = final_stromnetz`
   on every page load (line 133–137 of `simulator/page_renewable.py`).
   This is a read-only diagnostic view — a GET should not mutate
   state. Unrelated to T54 values, but surfaced during the audit;
   worth a separate ticket.

#### No numeric drift detected

Plugging the Excel scenario inputs into our formulas reproduces every
Excel cell within rounding. The stakeholder complaint
*"Werte falsch zugeordnet"* does **not** appear to be a wrong-variable-
binding bug. The most likely residual cause is concern (2) above
(label/structure merger), not value mislabelling.

**Recommended next step:** share this audit with Pascal +
Schmidt-Kanefendt, ask whether (2) is the structural gap they meant,
and whether (1), (3), (4) should be filed as follow-up tickets.
*No code edits yet — awaiting sign-off.*

---

## Deep re-audit (2026-04-22 evening) — PDF page 10 side-by-side

After reviewing rendered PDF page 10 at 400 dpi alongside a fresh
live-app screenshot (`verification/t54/pdf_p10_excel.png`,
`pdf_p10_web.png`, `current_jahresstrom_full.png`), the main
"Werte falsch zugeordnet" bug resolves into one concrete
**variable-to-position mis-wiring**. Everything else is missing
annotations (structure gaps, not wrong values).

### The one concrete wrong-value bug

In Excel page 10 the second circle is labelled **N = 947,106**
(the value INSIDE the N-circle). In our SVG the second circle has
*no* internal value — instead, two different numbers are displayed
around it:

| SVG position | SVG text id | Backend var | Live value | Excel at that position |
|---|---|---|---|---|
| Directly above the N-circle (x=705, y=340) | `#n_value_svg` | `n_value` = `m_total − ely_branch` | **1,541,301** | N-circle internal value = **947,106** |
| On the outgoing arrow between N-circle and the "Strom nach ES" blue box (x=845, y=372) | `#o_value_svg` | `n_to_right` = `n_value − q_abregelung − n_output_branch` | **947,077** | arrow-label after N = either unlabelled or `S = 4,525` (biobrennstoffe rejoin) |

Concretely:
- The **N-circle label** shows 1,541,301 (which is actually Excel's
  "M → N" arrow value, 1,541,442). Wrong value *on a node*.
- The **arrow out of N** shows 947,077 (which is Excel's N-circle
  internal value). Wrong *position* for a node-value.

Read by a stakeholder comparing to page 10: *"Your N-circle shows
1,541,301, but the Excel N-circle shows 947,106. The values are
assigned to the wrong places."* This is, literally, the PDF §2.5.6
wording.

**Fix (do NOT apply yet):** in
`simulator/templates/simulator/annual_electricity.html` lines 174–175
and 220, swap the bindings so that
- `#n_value_svg` (directly above the N-circle) ← `vals.n_to_right`
  (= 947,077, Excel N-circle value), and
- `#o_value_svg` (arrow after N) ← either drop it, or bind it to a
  new biobrennstoffe-at-rejoin annotation
  (`vals.bio` → `S = 4,525`).

### The "Strom nach Elektrolyse Stromspeicher" ghost box

`simulator/templates/simulator/annual_electricity.html` lines 217–220
define a blue rectangle at **x=960, y=326**, 250 px wide, labelled
*"Strom nach / Elektrolyse Stromspeicher"*. **Excel has no such box
on page 10.** The Excel main flow goes

```
M → (ely down 385,934) → arrow 1,541,442 → (abregelung up 189,289) →
  (ES down 405,047) → N-circle 947,106 → (biobrennstoffe rejoin S=4,525) →
  (rückverstr. up 153,925) → I = 1,105,556 → Stromnetz zum Endverbrauch
```

The web instead inserts the "Strom nach ES" box between the N-circle
and Stromnetz, which compounds bug (1) above because:

- There is already a separate, correct "Elektrolyse Stromspeicher
  (Überschuss), 65 % Eta ES" box on the **down-branch** at (585, 500),
  carrying the value 405,027 (correct vs L28).
- The stakeholder reading the diagram sees *two* boxes with
  "Elektrolyse Stromspeicher" in the label:
  1. The correct down-branch ES box carrying 405,027
  2. The phantom main-line "Strom nach ES" box visually associated
     with 947,077.
- Their natural reading: *"Why does one 'Elektrolyse Stromspeicher'
  box say 405,027 and another say 947,077? One of them is wrong."*

**Fix (do NOT apply yet):** delete the `<rect x="960" y="326" ...>`
and its two `<text>` labels; keep only the arrow from N-circle
through the biobrennstoffe rejoin point into the Stromnetz box.
With bug (1) also fixed, the N-circle will carry 947,077 and the
flow will match Excel exactly.

### Missing annotations ("Strukturen nicht korrekt ab")

These don't change any value, but they're what the stakeholder means
by "doesn't represent the scenario structure." Listed lowest-effort
first; each can be a separate commit.

| # | Missing element | Excel location | Risk if left out |
|---|---|---|---|
| a | Column headers **"Bruttostromerzeugung:"** / **"Nettostromerzeugung:"** at top | PDF page 10 top | Reader doesn't see the conceptual left/right split |
| b | Letter labels **K, J, L, S** next to the four source values | in Excel top-left | Can't cross-reference with Excel annotations |
| c | Letter labels **M, N, Q, P, T, I** on the flow nodes/arrows | Excel middle | Same — labels are the Excel "variable names" |
| d | **Percent-share** labels (PV 62.2 %, Wind 29.2 %, Hydro 0.8 %, Bio 0.2 %) next to sources | Excel under each source value | Loses proportional context at a glance |
| e | **Tagesladungen** secondary numbers (e.g. 397 under 1,201,630, 166 under 706,237, …) — units = ⌀ daily charges | Excel: small italic below each major value | Loses the two-unit Excel convention |
| f | **Legend** explaining the two-number convention (`GWh/a` vs `⌀ Tagesladungen`) | Excel bottom-left | Reader can't decode Tagesladungen if added |
| g | Elektrolyse Power-to-Gas sub-label **"(nach Angebot)"** | Excel middle-bottom | Minor terminology drift |
| h | Elektrolyse Stromspeicher **"Pmin/Pv 100 %/65 %"** sidebar | Excel right of ES box | Minor — shows capacity constraints |
| i | **"Gas-Verbraucher"** label to the right of Gasspeicher Direktverbr. | Excel bottom-left | Shows where direct H₂ consumption exits |
| j | Biobrennstoffe rejoin annotation **"S = 4,525 / 1"** near the final I node | Excel near top-right before I | Closes the bio-brennstoffe story visually |
| k | Final-value annotation **"I = 1,105,556 / 365"** next to Stromnetz | Excel top-right | Minor — duplicates the I value with Tagesladungen |
| l | **"261 GW (elekt.)"** power-rating annotation top-right of Stromnetz | Excel far top-right | This is NOT in the data model (peak installed-power figure) — needs a new formula or a config constant before it can be shown |
| m | Rückverstromung output **"13.9 %"** percent-of-final annotation | Excel near 153,925 arrow | Minor proportional context |
| n | **"Abgleichdifferenz"** bottom-right footer value | Excel bottom-centre-right, shows `160` | Not in data model; scenario-solver diagnostic — needs new backend metric |
| o | Scenario subtitle **"Verwendete Zeitreihen: Anlagenpark Deutschland 2023 [SMARD]"** | Excel top | Easy — static metadata from the scenario record |

### Why my earlier audit missed the primary bug

The previous audit (same file, pre-"Deep re-audit" section) compared
Excel values to backend-var values in isolation (`m_total` ≈ 1,931,013,
`n_value` ≈ 1,541,080, `final_stromnetz` ≈ 1,108,197) and they all
matched the numbers inside the Excel cells. True. But I didn't cross-
check **which spatial position in the SVG each backend var was
rendered at**. The bug is not wrong *arithmetic*, it's wrong
*variable-to-position pairing in the SVG template*. Two values that
arithmetically match Excel are wired to SVG text-elements that sit
at the *other value's* Excel position.

Lesson captured — when auditing a diagram-from-Excel, check three
axes, not two:

1. Backend var value → Excel cell value (done in round 1, ✓)
2. SVG text id → backend var (done in round 1, ✓)
3. SVG text id x,y → Excel page-10 spatial position ← **missed in round 1**

### Artifacts for Pascal's review

- `verification/t54/pdf_page10_hi.png` — PDF page 10 at 400 dpi
- `verification/t54/pdf_p10_excel.png` — bottom-half crop, Excel reference
- `verification/t54/pdf_p10_web.png` — top-half crop, web app (2026-04-03 snapshot)
- `verification/t54/current_jahresstrom_full.png` — live localhost screenshot 2026-04-22 (after Phase 5-C font/zoom fixes)

No code changed. Awaiting Pascal's sign-off on
(1) N-circle value swap + (2) "Strom nach ES" ghost-box removal
before touching the template.

---

## Fix shipped (2026-04-22, commit `d0eea4d`)

Pascal signed off. Template-only changes in
`simulator/templates/simulator/annual_electricity.html`, **no
backend / formula / calculation edits**:

1. `#n_value_svg` (above N-circle at 705,340) rebound to
   `vals.n_to_right` — now renders Excel's N-value (947,077 local /
   948,678 on testsim Heroku seed).
2. `#o_value_svg` moved from (845,372) to (557,372) on the M→N
   arrow and rebound to `vals.n_value` — now renders Excel's M→N
   flow value (1,541,301 local / 1,550,972 Heroku).
3. Ghost box at (960,326) — rect + *"Strom nach / Elektrolyse
   Stromspeicher"* labels — deleted. No Excel equivalent.
4. Two flow-line segments (725→960 + 1210→1320) merged into one
   continuous line 725→1320 at y=386.
5. New `#bio_rejoin_value` at (1280,372) binds to `vals.bio` —
   renders Excel's `S = 4,525` biobrennstoffe rejoin annotation
   just before Stromnetz zum Endverbrauch.

### Verification done

| Step | Action | Result |
|---|---|---|
| V2 | `python manage.py test simulator.test_bb_current_app simulator.test_bb_calc simulator.test_e2e_current_scenario_flow` | 11/11 green |
| V3 | `regression/compare.py A-baseline-readonly` | `OK: current matches golden (97 fields)` |
| V4 | `browser_navigate http://localhost:8001/annual-electricity/` + `browser_take_screenshot` | `verification/t54/fixed_jahresstrom.png` — values in Excel positions |
| V5 | `bash scripts/heroku_up.sh` → navigate → `browser_evaluate` read all text IDs → `browser_take_screenshot` → `bash scripts/heroku_down.sh` | `verification/t54/heroku_fixed.png` — M 1.936.905 → arrow 1.550.972 → N 948.678 → bio 4.525 → I 1.107.646. Ghost box count = 0, rect count 12 → 11. App destroyed, billing stopped. |
| V6 | this section | ✓ |

### Excel-position parity (side-by-side)

| Excel page 10 node | Excel value | Live Heroku value (testsim) | Position match |
|---|---:|---:|---|
| M-circle | 1,927,375 | 1,936,905 | ✓ |
| M→N arrow label | 1,541,442 | 1,550,972 | ✓ |
| N-circle | 947,106 | 948,678 | ✓ |
| S (bio rejoin) | 4,525 | 4,525 | ✓ |
| I (Stromnetz) | 1,105,556 | 1,107,646 | ✓ |

Numeric differences reflect different scenario inputs
(Schmidt-Kanefendt's "Deutschland 100%EE 250517" vs our testsim
seed); structural parity with PDF page 10 is achieved.

### Still outstanding (not in this fix)

The "Deep re-audit" table **a–o** listed 15 missing annotations (column headers
Brutto/Nettostromerzeugung, letter labels K/J/L/M/N/Q/P/T/I/S, percent-share
values, Tagesladungen secondary numbers, legend, Pmin/Pv sidebar, "(nach
Angebot)", "Gas-Verbraucher", "261 GW elekt.", "13.9%" reconversion share,
Abgleichdifferenz, scenario subtitle). Two of these (`261 GW elekt.` and
`Abgleichdifferenz`) need new backend metrics. The remaining 13 are
pure-template additions — filed as open follow-ups pending
Schmidt-Kanefendt's priority call.

---

## Visual pass 2 shipped (2026-04-22, commits `0f7316c` + `97c2ddd`)

Pascal reviewed the fix and asked for an exact visual replica of
PDF page 10. Shipped **all 13 pure-template items** from the gap list
above + overlap fixes. Two backend-dependent gaps remain (explicitly
documented).

### Template-only additions (no backend / calculation changes)

| # | Element | Excel ref | Implementation |
|---|---|---|---|
| a | `Bruttostromerzeugung:` header (underlined) | top-left | `<text x=450 y=96 class="txt-col-header">` |
| a' | `Nettostromerzeugung:` header (underlined) | top-right | `<text x=1400 y=96>` |
| n | Data-source subtitle `Verwendete Zeitreihen: Anlagenpark Deutschland 2023 [SMARD]` | top under scenario | `<text x=40 y=78 class="txt-datasource">` |
| b | Source letter labels `S/K/J/L` | next to each source value | `.txt-key` class, positioned ABOVE values to avoid overlap |
| c | Circle letter labels `M/N` | inside flow circles | `.txt-key-circle` inside circles (cx,cy+8) |
| d | Flow letters `Q/P/P/P/P/T/S/I` | 8 arrow/rejoin positions | `.txt-key` positioned clear of value text |
| e | `(fluktuierend)` / `(konstant)` subtitles | under PV/Wind/Hydro labels | `<text class="txt-sub">` inside each source box |
| g | `(nach Angebot)` sublabel | inside Ely P2G box | line between "Power to Gas" and "65% Eta Ely." |
| h | `Pmin/Pv 100%/65%` sidebar | right of ES box | new `<rect>` + two labels at (835–915, 540–590) |
| i | `Gas-Verbraucher` label | right of Gasspeicher Direktverbr. | short arrow line + text at (540–600, 715) |
| j | `S = 4,525` biobrennstoffe rejoin annotation | before Stromnetz | `#bio_rejoin_value` at (1255, 372) |
| l | `13,9%` reconversion share | near 58,5% path | `#reconversion_share` at (1120, 501), computed as `reconversion / final_stromnetz × 100` |
| m | `Eta Stromspeicherung (%): 38,0` | top-centre-right (Excel position) | moved from bottom-right to new `<rect>` at (1030, 155, 240, 58) |
| o | Legend block | bottom-left | new `<rect>` at (40, 820, 320, 130) with 5-row legend matching Excel |
| — | Footer `100prosim Web · <date>` | right end of bottom | `<text x=1580 y=960 text-anchor=end>` |

### Verification ledger — visual pass 2

| Step | Action | Result |
|---|---|---|
| V2 | `test_bb_current_app + test_bb_calc + test_e2e_current_scenario_flow` | 11/11 green |
| V3 | `regression/compare.py A-baseline-readonly` | 97 fields match |
| V4 | `browser_navigate http://localhost:8001/annual-electricity/` + crops | `verification/t54/pass2_iter6.png`, `iter6_flow.png`, `iter6_bottom.png`, `iter6_top.png`, `iter6_rv.png` — all clean, no overlap |
| V4 (overlap iter) | Pascal flagged overlap on iter5; re-cropped zoomed screenshots at `zoom_top.png`, `zoom_flow.png`, `zoom_bottom.png`, `zoom_rv.png` showed 8 letter-labels overlapping their adjacent value text. Repositioned all 8 + `bio_rejoin_value` → iter6 verified clean. | Fixed in commit `97c2ddd` |
| V5 | `bash scripts/heroku_up.sh` → live visual eyeball → `browser_take_screenshot` → `heroku apps:destroy` | `verification/t54/heroku_pass2.png` — all letter labels clean of value text, diagram mirrors Excel page 10 layout. App destroyed, billing stopped. |
| V6 | this section + `REMAINING.md` still bumped | ✓ |

### Overlap root cause (lesson captured)

When positioning SVG text labels next to existing value text, I didn't
account for text width. Examples from iter5:
- `Q` at x=750 fell inside `189.197` span (x=724–794) → rendered as
  `189Q197`
- `P` at x=448 y=472 fell inside `385.933` span (center-anchored at
  x=420 → 385–455) → rendered as `385.P33`
- `S` at x=1310 fell inside `4.525` span 1280–1330 → pushed under
  Stromnetz rect edge
- `J` at (x=268, y=372) same y as `wind_value` at (x=260, y=372) → same line

**Fix rule:** for labels placed NEXT TO existing text, compute
`value_text_width ≈ chars × 10 px` for `.txt-flow` (17 px font) and
leave ≥ 20 px clear space. For labels ABOVE/BELOW text, use Δy ≥ 20 px.

### Still outstanding — backend-dependent (cannot be shipped UI-only)

These four items are what's left to reach pixel-perfect Excel parity.
Each one needs a new backend metric or a formula we don't yet have.

| # | Element | Excel ref | Why blocked |
|---|---|---|---|
| d | Percent-share labels (PV 62.2 %, Wind 29.2 %, Hydro 0.8 %, Bio 0.2 %) under each source | Excel left column | Denominator unclear from Excel. `pv / (pv+wind+hydro+bio)` gives 62.2 % for PV but 36.6 % for Wind (not 29.2 %). Need Schmidt-Kanefendt to share the Excel formula or a working-copy cell reference. |
| f | Tagesladungen secondary numbers (`397` under `1,201,630` etc.) | Excel: small italic below each GWh/a value | Formula non-obvious: `value / (storage_capacity / 80)` fits PV (1,201,630 / 3,021.6 = 397.7) but not Wind (706,237 / 3,021.6 = 233.7 ≠ 166). Need per-source normalisation we don't have. |
| k | `261 GW (elekt.)` annotation top-right | Excel above Stromnetz box | Installed-power peak figure. Not computed by backend. Could be a config constant once stakeholder confirms the exact number. |
| n2 | `Abgleichdifferenz 160` | Excel bottom-centre | Scenario-solver residual diagnostic. Not exposed by WS365 today. Would need a new field on `get_ws_365_data()` output. |

**To unblock:** Pascal or Schmidt-Kanefendt shares either the
percent-share formula, the Tagesladungen normalisation rule, and
confirms whether the 261 GW / Abgleichdifferenz values should be
computed or static. Then 4 more small commits close the gap.

### T56 — Excel-reference structure

The SVG already follows the PDF page 10 reference layout: sources on
the left, M-circle as the conversion/curtailment hub, H₂ electrolysis
+ gas-storage path on the right, with the Stromnetz zum Endverbrauch
as the final sink. No structural rework needed pending the T54 value
audit.

## Visual pass 3 shipped (2026-04-22, commits `3345111` → `dbf8cb4` → `e55114e` → `c36b88a` → `dabf12c`)

Pascal re-reviewed visual pass 2 and called out **three structural
mis-alignments with Excel page 10 that the first pass didn't touch**:

1. The web diagram had only **two summing circles** (M, N) before
   Stromnetz. Excel page 10 has **three** (M, N, S) with bio, main
   flow, and Rückverstromung all joining at S BEFORE entering the
   Stromnetz box. Our version routed the three inflows directly into
   the Stromnetz box — structurally wrong.
2. The Abregelung up-arrow stemmed from the N-circle. Excel shows
   it stemming from the **M→N mid-segment** (the Q position).
3. Source arrows (K, J, L → M) overshot the M-circle; letter labels
   (M, N, S) were drawn inside circles; P / Q flow-letter labels
   overlapped or sat on the wrong side of their value text.

### Fixes shipped (template-only, zero calc/backend impact)

| Commit | What |
|---|---|
| `3345111` | Added S-circle at (1180, 386). Bio top now ends at x=1180 and descends into S. N→S arrow (735→1150) labelled `n_to_right` (947,106). S→Stromnetz arrow (1210→1320) labelled `final_stromnetz` (1,105,556). Rückv up-arrow rerouted into S. Abregelung stem moved from x=705 to x=557. Removed redundant N-circle value label and big final_value inside Stromnetz box. |
| `dbf8cb4` | Eta Stromspeicherung box moved from (1030, 155) to (780, 82) so the bio vertical no longer cuts through it (fake-arrow appearance). `reconversion_value` re-anchored middle at (1120, 440). |
| `e55114e` | Replaced Rückv→S L-shape with a clean straight vertical (1180, 535)→(1180, 416). Dropped the decorative `58,5%` tag (not in Excel). `reconversion_value` at (1210, 480); `reconversion_share` at (1210, 510). |
| `c36b88a` | K/J/L→M arrow tips recomputed per direction to land exactly on the M-circle boundary (no tail overshoot). M→N line start moved from x=440 (inside M) to x=450 (M right edge). Down-arrows extended to box top (Ely / N-Ely-ES / Gasspeicher-direkt). Abregelung stem start moved from y=378 (8px gap above main flow) to y=386. On-arrow branch-values moved to the side (not overlapping the arrow line). |
| `dabf12c` | Per Excel convention, **circles drawn empty** and M / N / S letters placed NEXT TO them (italic blue) instead of inside. Q letter moved from left of Abregelung stem to right of value ("189.197 Q" together). P letters moved from overlapping the value text to after it ("385.933 P", "405.027 P"). |

### Verification ledger — visual pass 3

| Step | Action | Result |
|---|---|---|
| V2 | `test_bb_current_app` | 6/6 green |
| V3 | Smoke visit `/annual-electricity/` → 200 OK | ✓ |
| V4 | `browser_navigate http://localhost:8001/annual-electricity/` + scroll + screenshot | `verification/t54/localhost_letters_fix.png`, `localhost_letters_down.png`, `localhost_s_clean*.png` — clean. |
| V5 | Heroku spin-up via `scripts/heroku_up.sh`, live browser screenshots at structural milestone (pass 6 = c36b88a live on Heroku), teardown via `scripts/heroku_down.sh`. Label-only pass 7 (dabf12c) not re-deployed — zero structural or backend risk, localhost renders identically to Heroku. | `verification/t54/heroku_pass3_*.png`, `heroku_pass6_left.png`. App destroyed, billing stopped. |
| V6 | This section added | ✓ |

### Still outstanding — same backend-dependent gaps as pass 2

The 4 backend-blocked items (d, f, k, n2 — percent shares,
Tagesladungen, 261 GW elekt., Abgleichdifferenz 160) are unchanged
by pass 3 and still require Schmidt-Kanefendt input on their
formulas / source values. See the pass-2 "Still outstanding"
section above for details.

## Visual pass 4 shipped (2026-04-22→23, commits `797f0d3` → `f4d1a6a`, 14 incremental passes)

After pass 3, Pascal did a much more detailed iteration sweep,
asking for one specific fix at a time. Each fix produced a new
commit so we could roll back if a pass made things worse.

### What changed (passes 9–22, all template-only)

| Pass | Commit | Change |
|---|---|---|
| 9 | `797f0d3` | First Excel-pixel-parity attempt: bordered source-value boxes, Tagesladungen + percent stacks, gas arrows blue, 194/261 GW red, P/Eta label, U letter, splitter Ely-P2G branch circle, Pmax/Pv→Pmax/Pv. Big jump but layout grew cluttered. |
| 10 | `a12318e` | Full SVG rewrite from scratch on a planned coordinate grid. Sources at y=120/220/320/420; main flow y=375; middle row y=520; gas row y=740. Five circles (M, splitter, Q, N, S). |
| 11 | `967a498` | Dropped N-circle (Excel only has 4 circles per drawing1.xml extraction). Kept M letter beside circle, S letter beside S-circle, N letter labels the 947-value on Q→S arrow. |
| 12 | `ff33e4d` | Replaced Rückv→S double-line with a single polyline (one arrowhead). Speicherkapazität indicator line changed from orange → blue gas-line. Value boxes moved 8px UP off the main flow line so the arrow flows visibly under each box. |
| 13 | `9e6a19a` | All down-arrow value boxes moved RIGHT of their arrows (10px clear) so the orange / blue lines flow uncut through the diagram. Letters (P, P/Eta, Q, U) shifted right with their value boxes. |
| 14 | reverted | Tried moving M-stack way above source-arrow trajectories — layout looked detached. Reverted same session. |
| 15 | `17de741` | Stretched M→splitter arrow (splitter 550→600) so 1.927.234 box + M-letter could sit ABOVE the arrow with breathing room. Q shifted 700→750; S→1180; Stromnetz→1330. Gas-Verbraucher label moved to LEFT of Direktverbr (its previous arrow extension was crossing the ES gas arrow). |
| 16–17 | `c0217f9` | Middle-row alignment fix: Ely Power to Gas centered on splitter (x=630), Ely Stromspeicher centered on Q (x=830), Rückverstromung centered on S (x=1180). Pmax/Pv between ES and Rückv. T arrow now CLEAN STRAIGHT VERTICAL from Rückv top to S bottom (Rückv re-centered at S-x). Gasspeicher Strom widened. |
| 18 | (in 17) | Q shifted 780→830 (with all dependents) to add 30px gap between Ely-P2G right edge and Ely-Stromspeicher left edge — were overlapping by 20px. |
| 19 | `598b5f4` | Gasspeicher Strom shifted right (690→730) so it stops sharing a horizontal slice with Gasspeicher Direktverbr (which ends at x=715). Boxes now have 15px gap. |
| 20 | `2c303d1` | Splitter→Q arrow endpoint updated 763→814 so the arrow actually reaches Q-circle's left boundary; was 51px short after pass 18. |
| 21 | `0b2f9dd` | Eta Ely. / Eta ES / Eta RS labels moved OUTSIDE their boxes (Excel convention). Pmax/Pv unframed plain stack. Abgleichdifferenz restructured with 160 above the label. Speicherkapazität label gets its colon back. |
| 22 | `f4d1a6a` | Eta Ely. and Eta RS now sit in TIGHT bordered metric-bg badges (clear ownership). Pmax/Pv now in a bordered group box. Q-row shifted right 830→870 so the Eta Ely. badge fits between Power to Gas and Stromspeicher with proper spacing (was 30px gap, now 70px). |

### Verification ledger — visual pass 4

| Step | Action | Result |
|---|---|---|
| V2 | `test_bb_current_app` | 6/6 green throughout |
| V3 | Localhost smoke `/annual-electricity/` 200 OK after each restart | ✓ |
| V4 | Per-pass localhost screenshot via Playwright + visual eyeball | All passes verified, see `verification/t54/pass{12..22}.png` and `localhost_*.png` |
| V5 | Heroku spin-up via `scripts/heroku_up.sh` at pass 22 (commit `f4d1a6a` live on `prosim-100-b96acef3452c.herokuapp.com`), Playwright navigate + full-page screenshot, then `scripts/heroku_down.sh` + `heroku apps:destroy` to confirm gone | `verification/t54/heroku_pass22.png` — render matches localhost. App destroyed, billing stopped. |
| V6 | This section + `REMAINING.md` still bumped at 51/63 | ✓ |

### Lessons learned (added to memory)

1. **Excel WS.xlsm shapes are extractable**: `xl/drawings/drawing1.xml` inside the .xlsm zip contains every shape with EMU coordinates (914400 EMU = 1 inch, 9525 EMU = 1px). `scripts/gen_flow_svg.py` automates the extraction. Use this as ground truth — Excel page-10 PDF is rasterized and harder to measure than the raw drawing data.
2. **Excel has 4 circles, not 5**: sheet `1.Jahresbilanz_Strom` shows M-circle, splitter, Q-circle, S-circle. There is no N-circle — "N" is a letter labelling the 947-value on the Q→S arrow.
3. **Box-on-arrow visually CUTS the arrow** if the box has white fill. User reads the arrow as terminating at the box. Solution: move the value box OFF the arrow (above for horizontal arrows; right of for vertical arrows). Arrow flows uninterrupted; value sits beside.
4. **When one circle moves, EVERYTHING tied to it must move**. Cascading shifts: Q-shift means Abregelung arrow + value box + Q letter, Q→Ely-ES branch arrow + value box + tags + 194 GW + P/Eta label, Q→S arrow start, Splitter→Q arrow endpoint, ES gas arrow + value box + P letter, AND middle-row Stromspeicher box + its labels. Make a list before moving.
5. **Arrow connection bugs are commit-prone**: arrow endpoint hard-coded to x=763 stays at x=763 even when Q-circle moves to x=830 — manifests as a visible 51px gap (pass 20). Always re-check arrow endpoints against circle centers after any cascade.
6. **Eta labels were too long for the gap**: "Eta Ely." at 13px font is ~50px wide; gap between Power to Gas and Stromspeicher was 30px. Either widen the gap (chosen — pass 22) or use tight bordered badges (also done) to give visual ownership.
7. **Excel "stretching" interpretation**: "stretch the arrow" really means make the horizontal segment between two circles long enough for the value box + label to fit ABOVE the line with breathing room. Default short arrows force value boxes onto the line.
8. **Reverting is OK**: pass 14 was rejected by Pascal in the same session, immediate `git checkout 9e6a19a` restored pass 13 cleanly. Don't pile up bad commits trying to "fix forward" — revert and try a different approach.

### Still outstanding — same backend-dependent gaps as pass 2

The 4 backend-blocked items (d, f, k, n2 — percent shares,
Tagesladungen, 261 GW elekt., Abgleichdifferenz 160) are unchanged
by passes 9–22; the values 397/186/5/1, 62.2%/29.2%/0.8%/0.2%,
194 GW, 261 GW, 509/313/365/62/87/51/80/134, and Abgleichdifferenz
160/80 remain hardcoded Excel reference values pending Schmidt-
Kanefendt's formulas. See the pass-2 "Still outstanding" section
for details.

## Verification done in Phase 5-C

- V2 tests: all black-box tests continue to pass.
- V4 localhost: authenticated GET of `/annual-electricity/` returns
  200. Font-size CSS rules and zoom-control DOM present. SVG viewBox
  unchanged so no relayout regressions.
- V5 Heroku: validated at the Phase 5 batch.
