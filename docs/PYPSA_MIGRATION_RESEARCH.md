# Migration research: 100ProSim → PyPSA (and the wider Python energy-modelling landscape)

**Status:** extended research brief, revision 2 (2026-04-20). **No code has been changed.**

**Purpose:** give Pascal a decision-grade picture of what migrating 100ProSim to PyPSA — or to any of the other active Python energy-system frameworks — would actually cost, what would be gained, what would be lost, and what alternatives exist short of a full migration. Scope intentionally broad; skim section 1 for the verdict, the rest is backup.

---

## Table of contents

1. [TL;DR](#1-tldr)
2. [PyPSA: architecture in detail](#2-pypsa-architecture-in-detail)
3. [PyPSA-DE: the Germany-specific model you'd be competing with](#3-pypsa-de-the-germany-specific-model-youd-be-competing-with)
4. [The atlite + ERA5 weather workflow](#4-the-atlite--era5-weather-workflow)
5. [Solver performance — HiGHS vs Gurobi, honestly](#5-solver-performance--highs-vs-gurobi-honestly)
6. [The wider Python energy-modelling landscape](#6-the-wider-python-energy-modelling-landscape)
7. [oemof in depth (and OSeEM-DE — the closest analogue to 100ProSim)](#7-oemof-in-depth-and-oseem-de--the-closest-analogue-to-100prosim)
8. [Calliope 0.7 — the xarray rewrite](#8-calliope-07--the-xarray-rewrite)
9. [FINE / ETHOS — Jülich's multi-region NPV toolbox](#9-fine--ethos--jülichs-multi-region-npv-toolbox)
10. [openmod and the MODEX framework-comparison project](#10-openmod-and-the-modex-framework-comparison-project)
11. [100ProSim today — the architecture you'd be migrating away from](#11-100prosim-today--the-architecture-youd-be-migrating-away-from)
12. [Paradigm gap: what-if vs optimization, unpacked](#12-paradigm-gap-what-if-vs-optimization-unpacked)
13. [Migration strategies — five paths, increasing cost](#13-migration-strategies--five-paths-increasing-cost)
14. [Concrete data-model mapping 100ProSim → PyPSA](#14-concrete-data-model-mapping-100prosim--pypsa)
15. [Web-UI options on top of PyPSA (pypsa-server, pypsa-explorer, model.energy, tauritron)](#15-web-ui-options-on-top-of-pypsa-pypsa-server-pypsa-explorer-modelenergy-tauritron)
16. [Testing strategy after a migration](#16-testing-strategy-after-a-migration)
17. [Effort estimate with a detailed WBS](#17-effort-estimate-with-a-detailed-wbs)
18. [Risks, limitations, criticisms](#18-risks-limitations-criticisms)
19. [Thesis-defense considerations](#19-thesis-defense-considerations)
20. [Recommendation](#20-recommendation)
21. [Appendix A: reading list](#21-appendix-a-reading-list)
22. [Appendix B: canonical PyPSA example Germany 100% RE](#22-appendix-b-canonical-pypsa-example-germany-100-re)
23. [Future work — integrate, don't migrate + speed + extensibility](#23-future-work--integrate-dont-migrate--speed--extensibility)
24. [Sources](#24-sources)

---

## 1. TL;DR

- **PyPSA is mature and is the de-facto community standard** for continental-to-national scale power-plus-sector-coupled energy optimization. [PyPSA-DE](https://github.com/PyPSA/pypsa-de) already covers the "100 % renewable Germany by 2045" question at up to 40 regions with hourly resolution, peer-reviewed, cited in Germany's Ariadne project. If "optimal cost pathway to German 2045 net-zero" is the research question, PyPSA-DE is the answer and reinventing it is negative-value work.
- **100ProSim does something different.** It's a *what-if calculator*: the user sets targets and the app shows the balance. PyPSA is a *cost-minimization optimizer*. They are not substitutable.
- **Full migration is a rewrite.** Realistic calendar time 6–12 months for a part-time developer learning PyPSA. The Django app becomes a thin UI around `pypsa.Network`; the calculation engine and 2300+ formula rows disappear.
- **Cheaper paths exist that preserve thesis value**:
  1. Keep 100ProSim as-is and add a **PyPSA export / validation bridge** (2–4 weeks). ★ recommended
  2. Replace only `calculation_engine/` internals with a fixed-capacity PyPSA Network (3–5 months).
  3. Use PyPSA-DE / oemof OSeEM-DE as **external benchmarks** in the thesis without touching code (days).
- **Honest alternatives to PyPSA** that might fit 100ProSim better at the storage layer: **oemof.solph** (modular, LP/MILP, component-library heavy, good German community), **Calliope 0.7** (YAML-configured, xarray-native, recently rewritten for speed), **FINE** (Jülich, NPV-minimizing, multi-region/commodity). None of them is a what-if calculator either.
- **Don't migrate because PyPSA is shinier.** The thesis's novelty — as I understand it from the code and seed data — is the user-facing what-if interaction, the land-use coupling, and the specific WS365 yearly storage model. That's not what any optimization framework does natively. Migrating turns the thesis into "I rebuilt 100ProSim as an already-existing optimizer," which is a weaker contribution.
- **Before investing a week in any migration path**: validate with your advisor whether the thesis contribution is the *tool*, the *methodology*, or the *results*. Migration only makes sense if the answer is "methodology" and the methodology demands optimization.

---

## 2. PyPSA: architecture in detail

Core references: [PyPSA documentation](https://docs.pypsa.org/latest/), [PyPSA GitHub](https://github.com/PyPSA/PyPSA), [PyPSA paper (Brown, Hörsch, Schlachtberger, 2018)](https://openresearchsoftware.metajnl.com/articles/10.5334/jors.188).

### 2.1 Origin and governance

- Created 2015 by Tom Brown, Jonas Hörsch, David Schlachtberger at the Frankfurt Institute for Advanced Studies (FIAS).
- Maintenance now led by the **Department of Digital Transformation in Energy Systems at TU Berlin** (Prof. Tom Brown), with roughly 200 contributors on GitHub.
- MIT-licensed. Active development, roughly weekly-to-monthly release cadence.
- The PyPSA community is an [openmod-affiliated](https://openmod-initiative.org/) grassroots group; same community as oemof, Calliope, and adjacent frameworks.

### 2.2 The `Network` object

Everything orbits a single `Network` instance (often aliased `n`). You add **components** to it, set time series, and call `network.optimize()`.

Core components with their semantics:

| Component | Represents | Key attributes | Analogue in 100ProSim |
|---|---|---|---|
| `Bus` | A node where carrier flows meet (substation, gas hub, heat sector node) | `carrier`, `v_nom`, coords | no direct analogue; 100ProSim is "one giant bus" |
| `Generator` | Anything producing a carrier at a bus (PV panel, wind turbine, lignite plant) | `p_nom`, `marginal_cost`, `p_max_pu` (t-series) | `RenewableData` *status*/*target* |
| `Load` | Demand at a bus | `p_set` (t-series) | `VerbrauchData` rows |
| `StorageUnit` | Short-term storage with both power and energy ratings (batteries, pumped hydro) | `p_nom`, `max_hours`, `efficiency_store/dispatch` | no direct analogue |
| `Store` | Pure energy storage (gas caverns, H₂) | `e_nom`, `e_cyclic` | WS365 is conceptually a `Store` with `e_cyclic=True` |
| `Link` | Controllable, optionally multi-port flow (HVDC, electrolyser, heat pump) | `efficiency`, `bus0`, `bus1`, ..., `p_nom` | closest: sector conversion factors in `Formula` rows |
| `Line` | AC transmission line with Kirchhoff physics | `x`, `r`, `s_nom` | none |
| `Transformer` | AC/AC or AC/DC coupling | `s_nom`, `x`, `r` | none |
| `Carrier` | An energy carrier (AC, DC, heat, H₂, CH₄, CO₂, biomass, oil) | `co2_emissions`, `color` | implicit in the 4-sector split |
| `SubNetwork` | Derived: connected AC sub-graph | (derived) | n/a |

Recent (upcoming) additions:
- **Process component**: multi-port Link with explicit rate per bus; lets you change the reference unit for cost (e.g., cost per t H₂ vs per MWh gas). Useful for chemistries and CCS.
- **Delayed Link outputs**: attributes `delay` and `cyclic_delay` model reactions, chemistries with latency, seasonal offsets.

Source: [PyPSA release notes (latest)](https://docs.pypsa.org/latest/release-notes/).

### 2.3 Snapshots (time)

The temporal index is `network.snapshots`. Typically hourly for a single year (8760 rows), or 3-hourly for long horizons. You can aggregate via time-series clustering (`tsam`), use representative days/weeks, or specify arbitrary weightings via `n.snapshot_weightings`. Weightings let 100 representative snapshots act as proxies for 8760 hours by scaling their contribution to the objective.

Multi-year / pathway studies use `n.investment_periods` — a separate axis (the `network.periods`), with its own weightings. PyPSA-DE uses **5-year steps from 2020 to 2050** with **hourly resolution within each step**.

### 2.4 Optimization

- `network.optimize()` minimises total system cost:
  `Σ (investment_annuity × p_nom_extendable) + Σ (marginal_cost × dispatch × snapshot_weighting)`.
- Default objective linear, but extensible. You can inject custom objectives, constraints, and variables via `extra_functionality` hooks or directly through linopy's API.
- Since PyPSA 0.22 (late 2022), [linopy](https://linopy.readthedocs.io/) is the default backend — xarray-labeled N-D optimization interface, far faster than Pyomo for problems with long time dimensions. Pyomo is still supported for backward compatibility but no longer recommended.
- `linopy.Variable` / `linopy.LinearExpression` closely mirror `xarray.DataArray` and integrate with `pandas.DataFrame`.

**What the optimizer returns**: `n.generators_t.p`, `n.storage_units_t.state_of_charge`, `n.lines_t.p0`, etc. — all time-indexed xarray-like frames. Post-processing via `n.statistics.energy_balance()`, `n.statistics.capacity_expansion()`, etc.

### 2.5 Limitations PyPSA explicitly acknowledges

- For computational reasons, hourly resolution is typically the finest sampled; sub-hourly is possible but rarely used.
- For Europe-wide sector-coupled models, **practical resolution is 25-hourly** (!) due to memory. Single-country sector-coupled models reach **3-hourly**.
- Models build infrastructure that may not be socially acceptable or supply-chain feasible — PyPSA doesn't model acceptance or permitting latency.
- Land-use constraints come from external GIS layers (Natura 2000, CORINE Land Cover, etc.), encoded as `p_nom_max` ceilings. The mapping is done in PyPSA-Eur/PyPSA-DE data workflows, not in core PyPSA.

Source: [PyPSA-GB limitations discussion](https://www.sciencedirect.com/science/article/pii/S2211467X24000828), general PyPSA documentation.

---

## 3. PyPSA-DE: the Germany-specific model you'd be competing with

Primary source: [PyPSA-DE GitHub](https://github.com/PyPSA/pypsa-de), preprint: [PyPSA-DE: Open-source German energy system model reveals savings from integrated planning (arXiv 2510.09414)](https://arxiv.org/abs/2510.09414).

### 3.1 What it covers

PyPSA-DE is a **sector-coupled open-source energy system model based on PyPSA**, adapted from PyPSA-Eur, specifically tuned for Germany and its neighbours. It:

- Solves a linear optimization problem in **5-year steps from 2020 to 2050** (pathway planning).
- Models **up to 40 regions** inside Germany, plus neighbour countries.
- Uses **hourly resolution** across full weather years.
- Covers electricity generation (hydro, PV, on/offshore wind, biomass, coal, lignite, nuclear phase-out, gas, CHP), storage (batteries, pumped hydro, H₂ salt caverns), heat (heat pumps, district heating, resistive heating, solar thermal), transport (BEVs, H₂-FCEV, synfuels), industry, and non-energy feedstocks.
- Implements Germany-specific policy levers: **coal phase-out law, nuclear phase-out (done), net-zero 2045, EU ETS, national CO₂ budget**.
- Publishes scenario results with integrated transmission planning.

### 3.2 Headline findings (2025 paper)

- Integrated (coordinated) transmission planning produces ~1/3 less grid expansion than the National Grid Development Plan (Netzentwicklungsplan), saves €92–€191 billion (in €₂₀₂₀), and lowers average grid tariffs by €7.5/MWh.
- Hydrogen infrastructure costs are minimized when planned jointly with electricity transmission.

### 3.3 Institutional embedding

- Developed within the [Kopernikus-Projekt Ariadne](https://ariadneprojekt.de/en/model-documentation-pypsa/) (BMWK-funded), Germany's flagship open-data climate-pathway research initiative.
- Plays a **reference role in the Ariadne Scenario Report**, the official German climate scenario comparison.
- Results feed into policy advice at the Federal Ministry for Economic Affairs and Climate Action.

### 3.4 Why this matters for 100ProSim

If the thesis argument is **"I analyze pathways to 100 % renewables in Germany by 2045"**, PyPSA-DE already does this with a research-grade model. Reinventing it as 100ProSim is hard to defend as a contribution.

If the thesis argument is **"I built an interactive what-if exploration tool so non-experts can reason about the pathway"**, 100ProSim offers something PyPSA-DE does not: immediacy, zero-solver interaction, German-language domain UI, and a specific land-use coupling that goes deeper than PyPSA-DE's generic `p_nom_max` ceilings.

A thesis that leans on the second framing is defensible. One that leans on the first would need to explain what 100ProSim offers that PyPSA-DE does not.

---

## 4. The atlite + ERA5 weather workflow

Source: [atlite GitHub](https://github.com/PyPSA/atlite), [atlite docs](https://atlite.readthedocs.io/en/master/).

### 4.1 What atlite does

`atlite` is a **lightweight xarray-based Python package for converting weather data into renewable-energy time series**. It's the standard input for PyPSA-Eur / PyPSA-DE / PyPSA-USA / PyPSA-Earth and is maintained by the PyPSA community.

- Downloads weather data from **ERA5 reanalysis** (ECMWF, 0.25° × 0.25° grid, hourly, 1950-present) via the Climate Data Store API.
- Optionally supplements with **SARAH-3** (satellite-based solar surface radiation, CM-SAF).
- Converts raw variables (wind speed at 100m, DNI, DHI, temperature, runoff) into:
  - Wind generation profiles for arbitrary turbine models (Vestas V112 3MW at 80m hub is the default).
  - PV generation via CSP + PV conversion models (includes temperature effects, inverter losses).
  - Heat pump COP as function of ambient temperature.
  - Hydro inflow.
- Output: hourly `p_max_pu` time series per grid cell (or aggregated per bus), directly pluggable into PyPSA.

### 4.2 What this costs you to adopt

- **Data volume**: a single Germany-cutout for one weather year is ~2–10 GB.
- **ECMWF CDS API account** is needed (free). First-time download can take hours.
- **One-time preparation effort** of ~1 week to learn the stack.
- For 100ProSim, which currently works with annual aggregates, atlite/ERA5 is necessary only if you want hourly resolution — which PyPSA does by default.

Cutouts for 2010, 2013, 2019, and 2023 are already prepared and published on [Zenodo](https://zenodo.org/records/12791128) for direct use.

### 4.3 Alternatives

- **[renewables.ninja](https://www.renewables.ninja/)** — pre-computed profiles, API access, less flexible but zero setup.
- **MERRA-2** — older NASA reanalysis, coarser grid, used by some legacy models.
- **National weather services** — DWD provides German hourly radiation/wind data but lacks full continental coverage.

---

## 5. Solver performance — HiGHS vs Gurobi, honestly

Source: [Open Energy Modelling Initiative HiGHS thread](https://forum.openmod.org/t/open-source-highs-solver-performance-boost-for-energy-system-models/2922), [HiGHS on Wikipedia](https://en.wikipedia.org/wiki/HiGHS_optimization_solver), [Mittelmann's benchmarks](https://plato.asu.edu/bench.html).

### 5.1 Real numbers

For **LP problems of moderate size** (single-country, low-resolution), all solvers perform comparably. For **large sector-coupled continental LPs**:

- **Gurobi** solves PyPSA-Eur 5-node × 8760-hour in about **1 minute**.
- **HiGHS** needs **2+ hours** for the same problem.
- On [Mittelmann's LP benchmarks](https://plato.asu.edu/bench.html), HiGHS interior-point is **20× slower** than COPT (best commercial).
- For **MILP** (mixed-integer, unit-commitment), the commercial gap widens to 50–100×.
- For the specific interior-point solver algorithm on LPs of practical size, HiGHS can be **60–100× slower** than Gurobi.

### 5.2 What this means for 100ProSim-style problems

100ProSim's scale would be modest by PyPSA standards:
- Single node (Germany aggregate) or ~6 nodes (coarse Länder aggregation).
- Snapshots: the current 365-daily cycle, possibly 8760-hourly if hourly resolution is adopted.
- Variables: estimated 10⁴–10⁵ after vectorization.

At this scale, **HiGHS finishes in seconds to minutes**. Gurobi is not required. The HiGHS gap only bites on continental sector-coupled runs.

### 5.3 Commercial licenses

- **Gurobi**: free academic license (named-user, expires yearly, includes cluster support for students). Unlimited personal use; install with `pip install gurobipy` and `grbgetkey`.
- **CPLEX**: similar free academic license via IBM Academic Initiative.
- **Mosek**: free academic license.
- **HiGHS / GLPK / CBC / SCIP**: all free and open.

Thesis work can use academic Gurobi license for performance. Post-thesis (if 100ProSim ships) you'd need HiGHS or to purchase Gurobi commercially.

### 5.4 Recommendation for the thesis

If you adopt PyPSA at all, **use HiGHS as the default** (it's the PyPSA default since Feb 2022 via `highspy`) and document the academic-Gurobi fallback in the thesis for reproducibility. Don't make Gurobi a hard requirement.

---

## 6. The wider Python energy-modelling landscape

| Framework | Maintainer | Paradigm | Solver backend | Scale | Distinguishing feature |
|---|---|---|---|---|---|
| **PyPSA** | TU Berlin / FIAS | LP/MILP optimization with AC/DC power-flow physics | linopy (primary), Pyomo | Continental, sector-coupled | Only framework with first-class Kirchhoff physics |
| **Calliope 0.7** | ETH/Imperial | LP/MILP, YAML-configured | linopy in 0.7 (Pyomo in 0.6) | Flexible, single-site → continent | YAML-native scenario definition, xarray-first |
| **oemof.solph** | Uni Flensburg + partners | LP/MILP, bus/component graph | Pyomo | Regional to national | Large German-community plugin library |
| **oemof.tabular** | Uni Flensburg | Tabular data + solph | Pyomo | Regional | CSV-driven (OSeEM-DE uses it) |
| **FINE / ETHOS.FINE** | FZ Jülich (IEK-3) | LP/MILP NPV minimization | Pyomo, linopy | Multi-region, multi-commodity | Built-in spatial aggregation tooling |
| **urbs** | TU Munich | LP | Pyomo | Urban-to-regional | Teaching-oriented, simpler than oemof |
| **OSeMOSYS** | OpTIMUS community | LP, capacity expansion | GLPK, Pyomo, GAMS ports | National | Used by IAEA/UN-DESA, pathway planning |
| **SpineOpt.jl** | EU Spine | MILP, unit commitment | JuMP (Julia) | Multi-carrier | Database-backed, stochastic, day-ahead |
| **Backbone** | VTT | MILP, stochastic | GAMS | Power + storage | Stochastic investment/UC, strong on energy markets |
| **Balmorel** | DTU / Ea Energy | LP/MILP | GAMS | Nordic/Baltic | Open model with long history, district heat |
| **Dispa-SET** | JRC | Unit-commitment MILP | Pyomo | European power | Policy support at EU level |
| **REMix** | DLR | LP/MILP | Pyomo/linopy | European | Used in DLR research |
| **Genesys-2** | RWTH Aachen | LP | Pyomo | German 100% RE | Ancestor of a 100% RE Germany research lineage |
| **PyPSA-Eur / DE / USA / Earth** | PyPSA community | PyPSA + regional data | linopy | Country-specific | Drop-in national models |
| **Open Energy Platform (OEP)** | OpenMod / ZIB | Data platform | n/a | Meta | Database + API for sharing scenarios |

**All of these are optimization frameworks.** None is a what-if calculator like 100ProSim. The closest simulation-style tools are:

- [**PowerSimulations.jl**](https://github.com/NREL-Sienna/PowerSimulations.jl) (NREL Sienna, Julia) — dispatch simulation, no optimization required.
- [**openAFOLU / OSeMOSYS** in "dispatch-only" mode] — possible but unusual.
- **PyPSA with `p_nom_extendable=False`** — forces the optimizer to only dispatch given fixed capacities; effectively a simulator.

---

## 7. oemof in depth (and OSeEM-DE — the closest analogue to 100ProSim)

### 7.1 oemof the ecosystem

- [oemof](https://oemof.org/) (Open Energy Modelling Framework) is a Python library ecosystem for modelling energy systems, originally centred on [oemof.solph](https://oemof-solph.readthedocs.io/).
- Developed by a German academic consortium led by University of Flensburg, in active development since 2015.
- LP/MILP backend is **Pyomo**; solvers are same options as PyPSA (HiGHS/Gurobi/CPLEX/CBC/GLPK).
- **Philosophy**: bus-and-component graph, strictly declarative. Each component is a node; each flow is an edge. A `Sink` at a bus is a load; a `Source` at a bus is a generator; a `Transformer` converts one flow to another.
- **Plugin ecosystem**: `oemof-thermal`, `DHNx` (district heating networks), `oemof-tabular` (CSV-driven configuration), `oemof-B3` (Berlin-Brandenburg case).
- **Sector coupling**: first-class via `Transformer` and multi-flow buses; often used for district heating and CHP.

Source: [oemof.solph paper](https://www.sciencedirect.com/science/article/pii/S2665963820300191).

### 7.2 OSeEM-DE — the model closest to what 100ProSim seeks to do

Source: [OSeEM-DE GitHub](https://github.com/znes/OSeEM-DE), paper: [Open model-based analysis of a 100% renewable and sector-coupled energy system — the case of Germany in 2050 (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0306261921001549).

Highlights:

- Built on **oemof-tabular** (CSV-driven oemof.solph).
- **2 regions** (Northern Germany NDE vs Southern Germany SDE), connected by transmission links.
- Components: onshore/offshore wind, PV, run-of-river hydro, biomass CHP, air-source heat pumps, ground-source heat pumps, batteries, heat storage.
- Objective: **100 % renewable electricity + space heating for Germany in 2050**, cost-optimal mix.
- Headline result: **100 % renewable sector-coupled Germany is feasible** with the modelled technology mix.
- Published with full data and code; reproducible.

**Why this matters**: if you frame 100ProSim as a 100 % RE Germany study, OSeEM-DE is a published baseline. You can cite it, compare, and differentiate. It's also much smaller than PyPSA-DE, easier to read, and closer to 100ProSim's aggregation level.

### 7.3 oemof vs PyPSA in practice

For 100ProSim-scale problems (aggregated Germany, annual-to-daily resolution, 4 sectors), **oemof.tabular is arguably a better fit than PyPSA**:
- Flatter learning curve (CSV-driven, less conceptual overhead).
- No Kirchhoff physics (you don't need it at your scale).
- Direct CSV in/out maps cleanly to the current 100ProSim database tables.
- Existing OSeEM-DE blueprint to copy from.

PyPSA wins when:
- You want transmission network detail.
- You need 1+ continental model integration (Europe-wide balance).
- You want the larger user/contributor community.

---

## 8. Calliope 0.7 — the xarray rewrite

Source: [Calliope GitHub](https://github.com/calliope-project/calliope), [Calliope docs](https://calliope.readthedocs.io/), [Calliope PyPI](https://pypi.org/project/calliope/).

### 8.1 What changed in 0.7

- Pre-release announced March 2025; currently on iteration toward 0.7 stable.
- **Switched optimization backend from Pyomo to linopy** (same direction PyPSA went in 0.22).
- Internal data model moved to xarray-first; results come back as xarray Datasets directly.
- Large performance gain on problems with long time dimensions.
- Migration path from 0.6 documented; YAML configs largely compatible.

### 8.2 What Calliope is for

- **Multi-scale** — same YAML spec can describe a single building, a neighbourhood, a region, or a continent. You choose the spatial resolution.
- **YAML-first** — the scenario definition is a set of YAML files, not Python code. Good for reproducibility; bad for programmatic scenario generation.
- **Modular** — techs, nodes, and links are user-defined. Very little is hardcoded. Compare to PyPSA where you're committing to a fixed component taxonomy.
- **Teaching-friendly** — used at ETH Zürich and Imperial College.

### 8.3 When it fits 100ProSim

If you want an optimization paradigm but also want scenario definitions you can version-control in plain text, Calliope is a good middle path. You'd generate the YAML from 100ProSim's database on export.

---

## 9. FINE / ETHOS — Jülich's multi-region NPV toolbox

Sources: [FINE GitHub](https://github.com/FZJ-IEK3-VSA/FINE), [ETHOS.FINE: A Framework for Integrated Energy System Assessment (arXiv 2311.05930)](https://arxiv.org/abs/2311.05930), [JOSS paper](https://joss.theoj.org/papers/10.21105/joss.06274.pdf).

- Developed at **Institute of Energy and Climate Research IEK-3 at Forschungszentrum Jülich**.
- Part of **ETHOS** (Energy Transformation paTHway Optimization Suite), a family of Jülich modelling tools.
- Current version 2.3.7.
- **Objective**: minimise **net present value** (NPV), not just annual cost. Includes full CAPEX/OPEX discounting over the horizon.
- Handles **multi-region, multi-commodity, multi-time-step, multi-investment-period** systems.
- Includes **spatial aggregation tooling** — cluster a fine-grained grid of regions into a workable number via k-medoids or similar.
- Backend: Pyomo historically, linopy adoption in progress.

### 9.1 When to consider FINE

- If your thesis has a strong **investment-over-time** angle (NPV, discounting, pathway CAPEX), FINE is specifically designed for it.
- If you're attached to the Jülich research ecosystem (IEK-3 has deep German-system expertise), FINE integrates best with their other tools.
- Less community than PyPSA or oemof; expect steeper learning curve and fewer Stack Overflow answers.

---

## 10. openmod and the MODEX framework-comparison project

Source: [openmod initiative](https://openmod-initiative.org/), [MODEX on openmod forum](https://forum.openmod.org/t/modex-framework-comparison-study-for-germany/3243).

- **openmod** is a grassroots community of energy modellers (~1000+ members, university + research institute) that promotes open-source code and open data.
- Runs [forum.openmod.org](https://forum.openmod.org/), annual workshops, a wiki, and mailing lists.
- Hosts [framework comparisons](https://forum.openmod.org/t/decision-support-for-selection-of-frameworks/4220) and decision-support discussions.

### 10.1 MODEX / open_MODEX

MODEX is a BMWi-funded project comparing German energy system models. The **open_MODEX** sub-project compares five **open-source** frameworks on a common benchmark:

- **urbs** (TUM)
- **oemof** (Uni Flensburg)
- **GENESYS-2** (RWTH Aachen)
- **OSeMOSYS** (Python-GUI edition)
- **Balmorel** (DTU)

Their findings generally converge on similar cost-optimal mixes but differ in computational performance, solver compatibility, and ease of extending to new technologies. (Full reports on the openmod forum and in published papers.)

PyPSA and FINE are not in the MODEX comparison — they showed up later or have continental-scale focus rather than the Germany-benchmark scope MODEX targets.

### 10.2 What this tells us

- There is a **peer-reviewed framework-comparison literature** Pascal can draw on. The thesis doesn't need to do the comparison from scratch.
- Cross-framework agreement on cost-optimal results is actually quite strong; differences are mostly in ergonomics and scope, not in answers.
- For a thesis that wants to position 100ProSim amongst the field, citing MODEX as prior art for "why a new framework is interesting" is the right move.

---

## 11. 100ProSim today — the architecture you'd be migrating away from

Based on direct inspection of the repo.

- **App type**: Django 4.2 web application, Postgres-backed (SQLite fallback).
- **Domain**: Germany, pathway to 100% renewable by 2045.
- **Paradigm**: deterministic formula evaluation. User sets inputs (landuse percentages, renewable targets, consumption levels); derived rows recompute via `calculation_engine/` plus the DB-stored `Formula` table (760 rows) and `FormulaVariable` table (1558 rows).
- **Sectors**: KLIK (Kraft/Licht/IKT/Kälte), Gebäudewärme, Prozesswärme, Mobile Anwendungen.
- **Temporal resolution**: annual aggregates everywhere except the WS365 storage cycle, which is daily for one year (365 samples).
- **Spatial resolution**: single-node Germany (no sub-national detail).
- **Storage model**: WS365 — annual daily-resolution balance with drift constraint `state(day 1) == state(day 365)`.
- **"Balance" action**: solves a single-variable inverse — adjust LU_2.1 (or LU_6 for wind) until storage drift is zero. This is a 1D root-find, handled by a dedicated `BalanceJob` worker, not a general optimizer.
- **Scenarios**: user-owned, named, comparable. Create / rename / delete / restore-baseline / save-snapshot semantics. No investment-optimization framing anywhere.
- **Outputs**: balance sheet per sector (`Bilanz`), annual electricity Sankey-style SVG diagram (`Jahresstrom`), Cockpit KPIs, storage cycle plot.
- **UI language**: German throughout. Non-negotiable if the thesis is German-examined.
- **Test coverage**: backend thesis suites + Claude-driven regression harness + Playwright/Selenium UI tests. Well-covered current behaviour.
- **Formula engine**: user-editable formulas stored as text (`Formula.formula_text`) evaluated at runtime via `formula_evaluator.py`. This gives 100ProSim a runtime-configurable calculation model that no optimization framework offers natively.

**What 100ProSim does not do** (that PyPSA would add if migrated):
- Electrical power-flow physics.
- Hourly time resolution.
- Cost-optimal sizing of generators, storage, transmission.
- Investment decisions under cost objectives.
- Geographic detail (buses, lines).
- Sector coupling beyond the four fixed sectors.

**What 100ProSim does that PyPSA would not preserve**:
- Runtime-editable formulas and variables from the DB.
- Direct manipulation of targets with instant recalculation.
- The German-language domain UI.
- The scenario lifecycle (save/rename/compare).
- Land-use ↔ solar-area coupling as a first-class UI concept.
- The 365-day storage drift as a dedicated "Balance" action.

---

## 12. Paradigm gap: what-if vs optimization, unpacked

The single biggest reason migration is expensive.

**100ProSim's core loop:**

```
user edits LU_2.1 → app recomputes target_ha → renewable rows update →
  bilanz recomputes → storage drift recomputes → Balance button enabled.
  User clicks Balance → worker adjusts LU_2.1 to zero drift → UI refreshes.
```

Each step is **deterministic, transparent, and millisecond-fast**. The user is in control.

**PyPSA's core loop:**

```
user sets costs, constraints, availability → network.optimize() → solver runs (seconds to hours) →
  cost-optimal dispatch and sizing → user inspects results.
```

Each step is **black-box**. The user gives preferences (costs, bounds); the solver decides.

To rebuild 100ProSim's UX on PyPSA you would:

1. **Freeze capacities** (`p_nom_extendable=False`) so the user's target values survive optimization.
2. **Add per-input constraints** locking targets (e.g., `Generator.p_nom == user_target_value`).
3. **Run optimization** for dispatch only. Expect 5-60s latency depending on resolution.
4. **Poll-and-refresh UI** to show the result. The current "instant recalc on every keystroke" dies.

That's not necessarily wrong — Calliope and model.energy do exactly this and feel usable — but **the direct manipulation feel of 100ProSim is gone**, and replaced with "submit scenario → wait → read result". Different product.

To keep direct manipulation: **don't migrate the front-end path**. Only use PyPSA to validate, benchmark, or compute results a formula-based calculator can't (e.g., hourly dispatch). Keep the what-if engine Python-native.

---

## 13. Migration strategies — five paths, increasing cost

### Path A — Full rewrite on PyPSA (6–12 months, very high risk)

Replace both `calculation_engine/` and most of `simulator/` with a PyPSA-backed model. The Django app becomes a thin UI plus scenario persistence around a `pypsa.Network`.

Throw away: `calculation_engine/`, formula service, formula evaluator, formula tables, ws365_*, ws_engine. Keep: Django auth, scenario save, German UI shell, regression harness (definitions, not goldens).

**Biggest risk**: the thesis's methodological contribution evaporates; you've rebuilt 100ProSim as a poor man's PyPSA-DE.

### Path B — PyPSA under the calculation-engine hood (3–5 months, medium risk)

Keep the UI and scenario model; replace `calculation_engine/*_engine.py` with code that builds a fixed-capacity PyPSA Network and runs dispatch-only optimization. User inputs still drive the model (as `p_set` / `p_nom` bounds); PyPSA handles energy balance and dispatch internally.

**Advantage**: replace the ad-hoc WS365 drift balance with PyPSA's `Store(e_cyclic=True)`. You get proper energy-balance physics for free while keeping the thesis paradigm (user-set targets, app checks feasibility).

**Disadvantage**: non-trivial Network-builder, ~2000 LoC. Seed reproduction requires tuning.

### Path C — PyPSA validation bridge (2–4 weeks, low risk) ★ RECOMMENDED

Don't migrate. Add a one-way "Export to PyPSA" feature. Writes the current scenario as a PyPSA `.nc` (NetCDF) file the user can load in a Jupyter notebook. The thesis compares 100ProSim's what-if outputs to PyPSA's cost-optimal outputs as a **validation step**, not a replacement.

Concretely:
- `simulator/pypsa_export.py`, ~300–500 LoC, translates LandUse + Renewable + Verbrauch rows into PyPSA components and writes NetCDF.
- Django view returns the NetCDF for download.
- A Jupyter notebook in-repo loads the export, runs `network.optimize()`, and produces comparison plots.

### Path D — External benchmark, no code (days, zero risk)

Pick 2–3 reference scenarios, run their equivalents in PyPSA-DE or OSeEM-DE (both have published Snakemake workflows), compare by hand in the thesis. Cite the PyPSA-DE / OSeEM-DE papers. Write a thesis section defending 100ProSim's what-if paradigm against the optimization paradigm on methodological grounds.

### Path E — oemof.tabular alternative (4–6 weeks, medium risk)

If migration is necessary but PyPSA feels too heavy, port the calculation engine to **oemof.tabular** instead. OSeEM-DE is a published blueprint. Closer to 100ProSim's current CSV/table-driven style. Smaller learning curve. Less community than PyPSA but sufficient for thesis.

---

## 14. Concrete data-model mapping 100ProSim → PyPSA

| 100ProSim | PyPSA | Notes |
|---|---|---|
| `LandUse` row (LU_2.1, LU_6, ...) | **Custom constraint on `Generator.p_nom`**. PyPSA has no land-use concept. | Encode `p_nom_max = area_ha × power_density_MW_per_ha`. Add a second constraint summing solar areas ≤ total available LU_2.1 ha. |
| `RenewableData.status` / `.target` | `Generator.p_nom_min` / `.p_nom_max` or `.p_nom` | Map GWh/a → MW via capacity factor (atlite-derived). |
| `RenewableData` code `9.3.1` (Stromaufnahme Überschussphasen) | `n.storage_units_t.p_store.sum()` (result, not input) | This is an output of the optimization; PyPSA doesn't accept it as an input. |
| `RenewableData` code `9.3.4` (Abregelung) | `n.generators_t.p_max_pu - n.generators_t.p / p_nom` (curtailment, result) | Same: computed, not set. |
| `RenewableData` code `10.1` (Endenergie ee) | `n.statistics.energy_balance(aggregate_time='sum').loc[(slice(None), 'ac')]` etc. | Aggregation of generator output. |
| `VerbrauchData` rows per sector | `Load` per sector bus, `p_set` time series | For annual aggregates, single snapshot with `snapshot_weightings=8760`. |
| `GebäudewärmeData` | `Load` on heat bus + `Link` from electricity bus to heat bus (heat pump) with time-varying `efficiency` for COP | Heat pumps are the canonical sector-coupling example in PyPSA. |
| `Formula` rows (760) | Replaced by PyPSA model structure | Most formulas collapse into first-class components. The runtime-editable aspect is lost. |
| `FormulaVariable` rows (1558) | Component attribute values | Same collapse. |
| **WS365 storage cycle** | **`Store(e_cyclic=True)`** | This is exactly what PyPSA does natively. The entire WS365 subsystem is replaced by one `Store` declaration. ⭐ |
| `BalanceJob` queue | Irrelevant — `network.optimize()` replaces it | All async worker logic goes. |
| Scenario create/rename/delete | `n.export_to_netcdf(path)` / `n.import_from_netcdf(path)` + Django scenario table | PyPSA has no scenario-metadata layer. |
| Goal Seek (find LU_2.1 such that drift = 0) | Custom constraint + `p_nom_extendable=True` on solar | The optimizer naturally sizes LU_2.1 to satisfy the cyclic storage constraint. |
| `/annual-electricity/` Sankey | `pypsa-explorer` has a Sankey visualization, or custom Plotly from `n.statistics.energy_balance()` | Presentation layer; no hard mapping. |
| `/cockpit/` KPIs | `n.statistics.capex()`, `n.statistics.opex()`, `n.statistics.curtailment()` | Built-in. |
| `/bilanz/` tables | `n.statistics.energy_balance()` | Built-in. |

**Note on `Formula`**: 100ProSim stores computation as data (formulas in DB, editable at runtime). PyPSA stores computation as code (component semantics). Migrating loses the runtime-editability unless you keep a formula layer that runs *before* PyPSA (so the DB formulas parameterize PyPSA inputs, not PyPSA outputs).

---

## 15. Web-UI options on top of PyPSA (pypsa-server, pypsa-explorer, model.energy, tauritron)

If migration happens, these are the paths for keeping a web front-end.

### 15.1 [pypsa-server](https://github.com/PyPSA/pypsa-server)

- Web interface for running PyPSA scenarios via the Snakemake workflow.
- Stack: **Flask + gunicorn + nginx + Redis** (job queue).
- Deployed as **model.energy** in production.
- Async: user submits scenario, Redis queues it, worker runs optimization, Redis returns job status; results served as CSV / plots.

**Relevance to 100ProSim**: this is the canonical "PyPSA as a web app" blueprint. If you did Path A, you'd essentially be recreating pypsa-server with a German-language Django shell in front.

### 15.2 [pypsa-explorer](https://libraries.io/pypi/pypsa-explorer)

- Interactive dashboard for **visualizing** PyPSA networks (not running new scenarios).
- Stack: **Dash + Plotly**.
- Features: energy balance plots, capacity expansion, CAPEX/OPEX breakdowns, geographic network topology, multi-network comparison.

**Relevance**: for Path C (validation bridge), pypsa-explorer is the perfect tool for the Jupyter-notebook comparison layer. Saves you writing custom plots.

### 15.3 [model.energy](https://model.energy/)

Production deployment of pypsa-server running PyPSA-Eur-Sec. Free, public. User sets CO₂ target, year, region; solver runs; results come back in 1-5 minutes. Demonstrates what a PyPSA-backed interactive tool looks like in practice.

### 15.4 [tauritron](https://github.com/pypsa-meets-earth/tauritron)

Open-source web interface for PyPSA-Earth (worldwide scenarios). Newer project, less mature than pypsa-server, but an example of how the community is building Django-adjacent PyPSA front-ends.

### 15.5 Django integration?

None of the above uses Django. If you want Django specifically, you'd wrap PyPSA's Python API in Django views yourself — not hard, but no off-the-shelf "django-pypsa" package exists as of April 2026.

---

## 16. Testing strategy after a migration

If you migrate (Paths A, B, or E), test strategy must shift:

| Current test | Still valid after migration? | Replacement |
|---|---|---|
| `test_bb_calc.py` (formula black-box) | No — formulas are gone | Tests on PyPSA component construction |
| `test_wb_ws365_formula_engine.py` | No — WS365 replaced by Store | Tests on Store behaviour |
| `test_ws365_formulas.py` (formula parity) | No — parity check against what? | Deleted |
| `test_bb_val.py` (input validation) | Yes | Unchanged |
| `test_bb_bal.py` (balance endpoints) | Partial — `BalanceJob` may go | Replace with optimization job tests |
| `test_bb_e2e.py` (end-to-end persistence) | Yes | Unchanged |
| `test_e2e_ui_baseline.py` (Playwright baseline) | Yes — still valid | Probe new values |
| `regression/scenarios/A-baseline-readonly.yml` | Yes — reframe goldens | New baseline values |
| `regression/scenarios/C-ws-balance.yml` | Major redefinition — "balance" now = "optimize" | Keep the scenario, rewrite the semantics |

**New tests needed after migration:**
- **Infeasibility detection**: the optimizer may return infeasible under user input combinations. Test the UI handles this gracefully.
- **Solver determinism**: pin solver version + random seed (HiGHS has no seed, Gurobi does). Capture `n.statistics` output as golden.
- **Performance regression**: worst-case solve time per scenario, alert on 2× slowdown.
- **Network-builder property tests**: for any seed scenario, `network.optimize()` must converge; `n.statistics.energy_balance().sum() == 0` within tolerance.

Rough estimate: a migration rewrite doubles the test line count for the first 6 months, then stabilizes.

---

## 17. Effort estimate with a detailed WBS

### Path A — full rewrite (16–24 full-time weeks)

| Phase | Weeks | What |
|---|---|---|
| Learn PyPSA + linopy | 3–5 | Read docs, run PyPSA-DE tutorials, replicate small examples |
| Design Network schema | 1–2 | Decide component granularity (one bus? per-sector? per-Länder?) |
| Write Network builder | 3–4 | Translate LandUse + Renewable + Verbrauch into PyPSA components |
| Write land-use custom constraints | 1–2 | `n.add_constraints()` for area ↔ capacity coupling |
| Build atlite workflow for hourly profiles | 1–2 | Download ERA5, compute wind/solar/heat-pump profiles |
| Cost data sourcing | 1 | PyPSA-Eur cost DB, ATB, PyPSA-DE references |
| Replace WS365 with `Store(e_cyclic=True)` | 1 | Straightforward once builder is in place |
| Reproduce current balance outputs within tolerance | 3–5 | Tune parameters until scenario A golden passes (or intentionally deviates) |
| Rewrite balance worker → optimizer runner | 1–2 | Django view queues optimize; Celery / RQ instead of custom BalanceJob |
| Adapt scenario save/restore | 1 | NetCDF round-trip in Django scenario table |
| Rewrite thesis test suite | 2–3 | Per section 16 |
| Rewrite UI components that depended on formula values | 1–2 | `Jahresstrom` Sankey probably needs Plotly redo |
| Integration + debugging | 2–4 | Solver infeasibility debugging is an undocumented art |
| Documentation rewrite | 1–2 | CLAUDE.md, thesis methodology chapter |

**Calendar time part-time**: 6–12 months.

### Path B — engine swap (8–14 full-time weeks)

Like Path A but skip: UI rewrite (keep), scenario save (keep), most thesis tests (keep, targeted only).

### Path C — validation bridge (1–2 full-time weeks)

| Phase | Weeks | What |
|---|---|---|
| Learn enough PyPSA | 0.5 | Run one PyPSA tutorial |
| Write `simulator/pypsa_export.py` | 0.5 | Database rows → `pypsa.Network` |
| Write Django view for NetCDF download | 0.1 | One view, one URL |
| Write comparison Jupyter notebook | 0.3 | Load export, optimize, plot |
| Thesis chapter write-up | 0.5 | Compare / contrast section |

**Calendar time part-time**: 2–4 weeks.

### Path D — external benchmark (0.5–1 week)

Just thesis writing; no code. Clone PyPSA-DE, run 2–3 scenarios, paste numbers.

### Path E — oemof.tabular (4–8 full-time weeks)

Between B and C. oemof.tabular is closer to 100ProSim's CSV style, smaller learning curve than PyPSA.

---

## 18. Risks, limitations, criticisms

### 18.1 Risks of any migration path

- **Thesis-scope creep.** Rewriting the calculator is not the thesis's stated contribution; reviewers may ask why you spent 6 months on it.
- **Lost runtime flexibility.** PyPSA's component structure is more rigid than 100ProSim's formula DB. Forumla-as-data is a product feature.
- **Solver dependency.** Even HiGHS introduces a binary dependency new failure mode (infeasibility, numerical issues at scale).
- **Reproducibility regression.** If you tune parameters to reproduce today's outputs, your reproduction is tautological. If you don't, outputs differ and you must re-justify.

### 18.2 PyPSA-specific limitations

- Time resolution capped at 25-hourly for Europe / 3-hourly for single countries due to memory. 100ProSim could probably do hourly Germany, but PyPSA-DE already settled on coarser for scale reasons.
- Models may recommend infrastructure that's socially or politically infeasible. Not a bug in PyPSA; a limitation of any optimizer without political-economy constraints.
- Supply-chain and labour-force constraints not modelled.
- AC power-flow physics are the headline feature, but at a single-bus aggregate scale (which is roughly what 100ProSim does) that complexity is paid for but never used.

### 18.3 Criticisms from the openmod community

- All optimization models are normative — they say "this is the cheapest pathway". They do not say "this is what Germany will do". Policymakers sometimes conflate the two.
- Sector-coupled assumptions drive results heavily. The classic critique: "garbage in, PyPSA-confidence out".
- Reproducibility is better than most fields but still not CI-tested — PyPSA-DE papers aren't re-runnable without manually downloading ~50 GB of input data.

### 18.4 What PyPSA is NOT good at (where 100ProSim might actually be better)

- **Teaching / exploration.** Non-expert users learn faster from direct-manipulation calculators than from optimization models.
- **Interactive deliberation.** "What if I insist on 50% PV?" is a 1-click answer in 100ProSim and a 30-60s solver run in PyPSA.
- **German-language domain framing.** PyPSA is English-only and generic. 100ProSim's vocabulary (*Verbrauch*, *Bilanz*, *Gebäudewärme*, *Jahresstrom*) is thesis-consistent.

---

## 19. Thesis-defense considerations

- If the thesis claims 100ProSim is a **contribution**, reviewers will ask: how is this different from PyPSA-DE / OSeEM-DE? You need a defensible answer.
- A good answer: *"100ProSim is a deliberative exploration tool for non-expert users, not an optimization oracle. It complements, not replaces, cost-optimization."* — defensible, honest, cites prior art.
- A bad answer: *"100ProSim is a 100%-RE Germany optimizer."* — reviewers will point to PyPSA-DE and OSeEM-DE. Don't frame it this way.
- The validation bridge (Path C) gives the best defense: "I benchmarked my tool against PyPSA-DE's published results; the what-if outputs I produce are consistent with the cost-optimal solutions in these metrics, differ in these others, and the differences are attributable to the paradigm gap I discuss in chapter N."

---

## 20. Recommendation

**Do Path C (validation bridge).** Concretely:

1. Complete current 100ProSim feature work and stabilize the regression harness (scenarios A, C, and the D you'll send later). Do not start on PyPSA until this is done.
2. Add `simulator/pypsa_export.py` with `scenario_to_pypsa_network(scenario_id) -> pypsa.Network`. Export current scenario state as a PyPSA Network.
3. Add `GET /api/scenario/<id>/export-pypsa/` Django view returning a NetCDF file.
4. Add `docs/pypsa_comparison.ipynb` — a Jupyter notebook that loads three reference 100ProSim scenarios, runs PyPSA `network.optimize()` on each, and produces side-by-side comparison figures suitable for the thesis.
5. Write a thesis chapter "Comparison with cost-optimal PyPSA-DE solution" showing where your targets agree with the optimizer and where they don't, with physical explanations for divergences.

**Effort: 2–4 weeks, calendar time 1–2 months part-time.**

**Do not pursue paths A or E** unless your advisor specifically demands an optimization-based methodology. In that case, pursue Path B (engine swap), not A. Keep the Django UI and scenario model; change only the calculation engine. This minimizes rework while delivering a defensible optimization-based thesis claim.

**Do not migrate to stay current with the field.** The field is optimization-first, but your tool's value is in being not-quite-that. Staying what-if is a position, not a weakness.

---

## 21. Appendix A: reading list

**Start here (if you do any PyPSA work):**
1. [PyPSA documentation](https://docs.pypsa.org/latest/) — the whole top-level intro.
2. [PyPSA Quickstart 3: Investments & Storage](https://docs.pypsa.org/stable/examples/example-3/) — the canonical small example.
3. [PyPSA: Introduction (Fabian Neumann's course)](https://fneum.github.io/data-science-for-esm/dsesm/workshop-pypsa/) — best external tutorial.

**If you go beyond Path C:**
4. [PyPSA-DE GitHub + Ariadne model documentation](https://ariadneprojekt.de/en/model-documentation-pypsa/)
5. [PyPSA-DE paper (arXiv 2510.09414)](https://arxiv.org/abs/2510.09414)
6. [PyPSA-Eur documentation](https://pypsa-eur.readthedocs.io/) and [PyPSA-Eur GitHub](https://github.com/PyPSA/pypsa-eur)
7. [atlite documentation](https://atlite.readthedocs.io/en/master/) — weather-to-profiles pipeline
8. [linopy documentation](https://linopy.readthedocs.io/)

**For comparison / context:**
9. [oemof.solph paper (Krien et al., 2020)](https://www.sciencedirect.com/science/article/pii/S2665963820300191)
10. [OSeEM-DE paper (100% RE Germany 2050)](https://www.sciencedirect.com/science/article/pii/S0306261921001549)
11. [ETHOS.FINE paper (arXiv 2311.05930)](https://arxiv.org/abs/2311.05930)
12. [Calliope documentation](https://calliope.readthedocs.io/)

**Community:**
13. [openmod Initiative forum](https://forum.openmod.org/) — ask before you start
14. [PyPSA GitHub Discussions](https://github.com/PyPSA/PyPSA/discussions) — PyPSA-specific questions

---

## 22. Appendix B: canonical PyPSA example Germany 100% RE

For orientation — what a minimum-viable 100% renewable Germany model looks like in PyPSA. Not for copy-paste; shown so Pascal can gauge the translation distance from 100ProSim's current formula engine.

```python
# NOT EXECUTABLE — ILLUSTRATIVE ONLY.
# Shows the shape of a minimal PyPSA model that does conceptually what the WS365
# subsystem does (yearly storage balance with renewable feedstock).

import pypsa
import pandas as pd

n = pypsa.Network()
# Hourly snapshots for one year.
n.set_snapshots(pd.date_range("2045-01-01", "2045-12-31 23:00", freq="h"))

# One bus (Germany aggregate).
n.add("Bus", "DE_electric", carrier="AC")

# Load: total annual electricity demand in GWh, distributed hourly.
hourly_profile = ...  # from atlite or renewables.ninja
n.add("Load", "DE_demand", bus="DE_electric",
      p_set=hourly_profile * TOTAL_ANNUAL_GWh / hourly_profile.sum())

# PV generator with area ceiling from LU_2.1.
n.add("Generator", "PV_utility", bus="DE_electric", carrier="solar",
      p_nom_extendable=True,
      p_nom_max=LU_2_1_ha * PV_POWER_DENSITY_MW_per_ha,
      capital_cost=ANNUAL_CAPEX_PV_eur_per_MW,
      marginal_cost=0,
      p_max_pu=atlite_solar_profile)

# Onshore wind similar, using LU_6.
n.add("Generator", "Wind_onshore", bus="DE_electric", carrier="wind",
      p_nom_extendable=True,
      p_nom_max=LU_6_ha * WIND_POWER_DENSITY_MW_per_ha,
      capital_cost=ANNUAL_CAPEX_WIND_eur_per_MW,
      marginal_cost=0,
      p_max_pu=atlite_wind_profile)

# The WS365 storage cycle as a PyPSA Store with cyclic constraint.
n.add("Bus", "DE_h2", carrier="H2")
n.add("Store", "DE_h2_cavern", bus="DE_h2", carrier="H2",
      e_nom_extendable=True, e_cyclic=True,
      capital_cost=ANNUAL_CAPEX_H2_STORE_eur_per_MWh)

# Electrolyser: electricity → H2.
n.add("Link", "electrolyser", bus0="DE_electric", bus1="DE_h2",
      p_nom_extendable=True, efficiency=0.65,
      capital_cost=ANNUAL_CAPEX_ELY_eur_per_MW)

# Fuel cell: H2 → electricity.
n.add("Link", "fuelcell", bus0="DE_h2", bus1="DE_electric",
      p_nom_extendable=True, efficiency=0.585,
      capital_cost=ANNUAL_CAPEX_FC_eur_per_MW)

# Solve.
n.optimize(solver_name="highs")

# Post-process.
print(n.statistics.energy_balance())
print(n.statistics.capacity_expansion())
```

Whole model: ~40 lines. In exchange for throwing out ~760 `Formula` rows and the WS365 engine. The trade is simplicity for runtime-editability and interactive feel.

---

## 23. Future work — integrate, don't migrate + speed + extensibility

**Direction decided (2026-04-21, Pascal):** no migration. Future work is **integration** of PyPSA (and other libraries) at specific slow or rigid cores — everything else stays.

### 23.1 PyPSA integration (optimization-backed cores only)

Replace only the slow numerical modules with PyPSA calls; keep the UI, formula DB, scenario lifecycle, and "instant what-if" feel.

Priority targets:

1. **WS365 storage cycle** (`ws365_core.py`, `ws365_orchestrator.py`) → a single-node PyPSA Network with `Store(e_cyclic=True)` solved by HiGHS. Replaces the hand-rolled 365-day iteration with an LP. Expected speedup: 5–20×.
2. **Goal Seek / WS Balance Solar & Wind** → expressed as `p_nom_extendable=True` on the PV/wind generator + cyclic-storage constraint. One LP replaces the repeated-recalc root-find. Expected speedup: 3–10×, also deterministic.
3. **Sector + WS Full Balance** → same pattern, more generators extendable. Natural extension of (2).

Guard rails for the integration:
- Keep the old Python path behind a flag (`SIMULATOR_USE_PYPSA_WS_BALANCE`).
- Run both paths in parallel for N days; log disagreements.
- Scenario C golden may need re-capture after flip (difference will be solver tolerance, not physics).
- Add `pypsa`, `linopy`, `highspy` to `requirements.txt` and rebuild the Docker image. ~200 MB added.

### 23.2 Other speed-up areas (independent of PyPSA)

Slow paths that have nothing to do with optimization, and where PyPSA would NOT help. Worth profiling and fixing before or alongside PyPSA work:

1. **Full recalc cascade** after input change — 760 formulas fire in dependency order via `formula_evaluator.py`. Candidate wins: cache the dependency DAG, vectorize groups of independent formulas, short-circuit formulas whose inputs didn't change.
2. **`Renewable` / `Verbrauch` bulk updates** — currently per-row save + per-row signal. Batch into a single transaction + one recalc at the end. Likely 10–50× on bulk edit flows.
3. **Annual-electricity SVG rendering** — the 365-day table re-serializes on every page load. Cache the payload keyed by `(scenario_id, last_calc_run_id)`; invalidate only on recalc.
4. **Balance-job API polling** — current JS polls every 500 ms; switch to server-sent events or websocket notification so the worker pushes completion. Reduces idle load on both sides.
5. **DB query hotspots** — there are almost certainly N+1s in the renewable/verbrauch list views. Add Django `select_related` / `prefetch_related` where iterating rows triggers per-row related lookups.
6. **`WSData` 365-row reads** — currently fetches all 365 rows on every annual-electricity page load. Aggregate + cache.
7. **Formula evaluation memoization** — within a single recalc, same sub-expression is likely evaluated many times. Add an LRU cache keyed on input hash.

Most of these are 1–3 day fixes each. Profile first (Django Debug Toolbar, `django-silk`, or just `cProfile` on `run_full_recalc_view`) — then fix the top-3 hot paths by wall-clock cost.

### 23.3 Extensibility — what's actually hardcoded

Pascal asked: *"currently it's hardcoded I believe I don't know."* Partial audit of what's data-driven vs hardcoded:

**Data-driven today (good, extensible without code changes):**
- **Formulas**: 760 `Formula` rows + 1558 `FormulaVariable` rows. New derived quantities can be added by DB insert + formula text, no code needed.
- **LandUse categories**: adding / renaming rows is a DB insert.
- **Renewable rows**: hierarchical codes, editable via admin or management commands.
- **Verbrauch rows**: same.
- **Scenarios**: fully data-driven via `ScenarioSnapshot`.

**Hardcoded today (inflexible, requires code changes to extend):**
- **The four sectors** (*KLIK*, *Gebäudewärme*, *Prozesswärme*, *Mobile Anwendungen*) — baked into views, templates, column headings, bilanz layout. Adding a fifth sector (e.g., agriculture, industrial feedstocks) requires touching ~15 files.
- **WS365 model shape** — 365-day cycle, single-node Germany — assumed throughout `ws365_*.py`. Changing to hourly or multi-region means re-architecting that module.
- **Sector-coupling links** — implicit in formula text, not first-class entities. Adding a heat-pump model means adding both a formula AND UI for heat-pump COP.
- **Time horizon** — "2045 net-zero" is implicit in seed numbers; no concept of scenario year / pathway.
- **Country** — "Germany" is implicit everywhere (LU_*, Landuse total 35,759,529 ha = Germany, etc.). Not easily re-targetable to another country.
- **Language** — UI is German only, no i18n layer.
- **Power densities** (MW/ha for solar, wind) — live as magic constants inside `ws365_core.py` and land-use forms.
- **Cost data** — no first-class concept. If you ever add economics, it will be a major refactor.

**To make the system genuinely extendable, the most valuable refactors (in order of leverage):**

1. **First-class `Sector` entity** — make sectors a DB table with `name`, `display_name_de`, `order`, `icon_class`; iterate everywhere over `Sector.objects.all()` instead of hardcoded KLIK/GW/PW/MA. Single biggest unlock for future sector additions.
2. **First-class `Carrier` entity** (electricity, heat, H₂, gas, biomass) — currently implicit. Modeling new carriers (ammonia, synfuels) requires code today.
3. **First-class `Link` / `Conversion` entity** (electrolyser, heat pump, CHP) — currently lives inside formula text. Making conversions their own table with `from_carrier`, `to_carrier`, `efficiency`, `time_varying_efficiency_profile_id` is the step toward sector coupling without code changes.
4. **Scenario year / `TimeHorizon`** — decouple "2045" from the data so future-year or past-year pathways are possible.
5. **Power densities + cost parameters in DB** — not in Python constants.
6. **i18n / `django.utils.translation`** — wrap all UI strings with `gettext` so English / French versions become a translations file, not a fork.
7. **Spatial layer** — long-term, if multi-region is ever wanted, introduce a `Region` table; all LandUse / Renewable / Verbrauch rows get a `region_id` FK, default = "DE" for backward compatibility.

These are independent of PyPSA. Doing (1)–(3) also *makes a later PyPSA integration easier*, because the PyPSA Network builder (section 14) maps much more cleanly to a Sector + Carrier + Link schema than to the current hardcoded four-sector layout.

### 23.4 Suggested sequencing (not committing to dates)

1. Finish current stakeholder work.
2. Profile and fix top-3 non-optimization speed hotspots (section 23.2). Cheap wins.
3. First-class `Sector` table refactor (section 23.3, item 1). Biggest extensibility unlock.
4. PyPSA integration for WS365 storage cycle (section 23.1, target 1). Biggest remaining speed win.
5. First-class `Carrier` + `Link` (section 23.3, items 2–3).
6. PyPSA integration for goal-seek and full balance (section 23.1, targets 2–3).
7. Cost parameters in DB, scenario year, i18n — as stakeholder needs surface.

Each step is independently shippable. None requires the next. Stop whenever the returns diminish.

---

## 24. Sources

**PyPSA core**
- [PyPSA documentation (latest)](https://docs.pypsa.org/latest/)
- [PyPSA release notes](https://docs.pypsa.org/latest/release-notes/)
- [PyPSA GitHub](https://github.com/PyPSA/PyPSA)
- [PyPSA on PyPI](https://pypi.org/project/pypsa/)
- [pypsa.org](https://pypsa.org/)
- [PyPSA: Python for Power System Analysis (Brown et al. 2018, JORS)](https://openresearchsoftware.metajnl.com/articles/10.5334/jors.188)

**PyPSA-Eur / PyPSA-DE / PyPSA-Earth / PyPSA-USA**
- [PyPSA-Eur documentation](https://pypsa-eur.readthedocs.io/)
- [PyPSA-Eur GitHub](https://github.com/PyPSA/pypsa-eur)
- [PyPSA-DE GitHub](https://github.com/PyPSA/pypsa-de)
- [PyPSA-DE: Open-source German energy system model (arXiv 2510.09414)](https://arxiv.org/abs/2510.09414)
- [Ariadne project PyPSA documentation](https://ariadneprojekt.de/en/model-documentation-pypsa/)
- [REMIND-PyPSA-Eur (arXiv 2510.04388)](https://arxiv.org/abs/2510.04388)
- [National-sectoral emission constraints in PyPSA models (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10326444/)
- [PyPSA-Earth paper (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0306261923004609)
- [PyPSA-USA paper (SSRN)](https://papers.ssrn.com/sol3/Delivery.cfm/5029120.pdf?abstractid=5029120)
- [PyPSA-GB paper (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2211467X24000828)
- [PyPSA-Spain preprint (arXiv)](https://arxiv.org/html/2412.06571v1)
- [PyPSA comparable-software reference](https://docs.pypsa.org/v0.29.0/references/comparable-software.html)

**atlite**
- [atlite GitHub](https://github.com/PyPSA/atlite)
- [atlite documentation](https://atlite.readthedocs.io/en/master/)
- [Weather data cutouts for PyPSA-Eur (Zenodo)](https://zenodo.org/records/12791128)

**Solvers**
- [HiGHS Wikipedia](https://en.wikipedia.org/wiki/HiGHS_optimization_solver)
- [HiGHS funding proposal (highs.dev)](https://highs.dev/assets/HiGHS_funding_proposal.pdf)
- [Open-source HiGHS solver thread (openmod forum)](https://forum.openmod.org/t/open-source-highs-solver-performance-boost-for-energy-system-models/2922)
- [Mittelmann benchmarks](https://plato.asu.edu/bench.html)
- [Use Benchmarks to Find the Best Solver (Gurobi)](https://www.gurobi.com/resources/use-benchmarks-to-find-the-best-solver-for-your-needs/)

**Web UIs on PyPSA**
- [pypsa-server GitHub](https://github.com/PyPSA/pypsa-server)
- [model.energy](https://model.energy/)
- [pypsa-explorer (PyPI)](https://libraries.io/pypi/pypsa-explorer)
- [tauritron (PyPSA-meets-Earth)](https://github.com/pypsa-meets-earth/tauritron)

**oemof**
- [oemof homepage](https://oemof.org/)
- [oemof.solph paper (Krien et al. 2020)](https://www.sciencedirect.com/science/article/pii/S2665963820300191)
- [OSeEM-DE GitHub](https://github.com/znes/OSeEM-DE)
- [OSeEM-SN GitHub](https://github.com/znes/OSeEM-SN)
- [Open model-based analysis of a 100% renewable Germany 2050 (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0306261921001549)

**Calliope**
- [Calliope homepage](https://www.callio.pe/)
- [Calliope GitHub](https://github.com/calliope-project/calliope)
- [Calliope documentation](https://calliope.readthedocs.io/)

**FINE**
- [FINE GitHub](https://github.com/FZJ-IEK3-VSA/FINE)
- [ETHOS.FINE documentation](https://vsa-fine.readthedocs.io/en/master/)
- [ETHOS.FINE paper (arXiv 2311.05930)](https://arxiv.org/abs/2311.05930)
- [ETHOS.FINE JOSS paper](https://joss.theoj.org/papers/10.21105/joss.06274.pdf)
- [Helmholtz Research Software Directory ETHOS.FINE](https://helmholtz.software/software/ethosfine-framework-for-integrated-energy-system-assessment)

**Landscape / comparisons**
- [Open energy system models (Wikipedia)](https://en.wikipedia.org/wiki/Open_energy_system_models)
- [openmod Initiative](https://openmod-initiative.org/)
- [openmod forum](https://forum.openmod.org/)
- [openmod wiki (Wikipedia page on openmod)](https://en.wikipedia.org/wiki/Open_Energy_Modelling_Initiative)
- [MODEX framework comparison for Germany (openmod forum)](https://forum.openmod.org/t/modex-framework-comparison-study-for-germany/3243)
- [Decision-support for framework selection (openmod forum)](https://forum.openmod.org/t/decision-support-for-selection-of-frameworks/4220)
- [Framework comparison/synergies/consolidation workshop (openmod forum)](https://forum.openmod.org/t/moving-beyond-factsheets-framework-comparison-synergies-consolidation/1390/3)
- [Open source district heating modeling tools comparison (Energies MDPI)](https://www.mdpi.com/1996-1073/15/21/8277)
- [Sector coupling in North Sea region (Energies MDPI)](https://www.mdpi.com/1996-1073/12/22/4298)
- [Calliope: a multi-scale energy systems modelling framework (ResearchGate)](https://www.researchgate.net/publication/327617194_Calliope_a_multi-scale_energy_systems_modelling_framework)
