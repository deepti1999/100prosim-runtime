# 100prosim-Web — Stocktaking / Current-State Assessment

**Author:** H. Schmidt-Kanefendt (ErnES)
**Date:** 2026-04-03
**Source PDF:** `260403_Portierung_Bestandsaufnahme.pdf` (12 pages)
**Translation:** English (German original in `260403_Bestandsaufnahme_DE.md`)

> Full English translation of the stakeholder document. Content is unchanged; only language and layout are adapted.

---

## 1 Context / Background

Deepti Maheedharan's development work to port 100prosim into a web-capable tool, as part of her master's thesis, was completed in March 2026. She delivered the full core functionality bug-free and reached a far higher stage of development than could have been expected for such a complex task — **a great achievement!**

**ErnES's interest** is now to bring the tool to production readiness, and ideally to a state where the Excel-based 100prosim can be fully replaced across its entire relevant feature set. The following stocktaking is meant to serve as the basis for further development: what is still missing for **production readiness / readiness to replace Excel**?

---

## 2 Stocktaking

### 2.1 Hosting

Deepti had meanwhile stopped hosting the tool. When Ute and I asked about it, she set up hosting again on 2026-03-27 at <https://prosim-web-20260327121034-61780921a6b9.herokuapp.com/renewable/> to let the test phase continue. The login credentials from the previous hosting were no longer available and had to be recreated.

For ErnES to take over the 100prosim web application, it must be installed on an ErnES-owned platform. To guarantee a smooth transition, **the following is required by the end of the test phase:**

- **Provisioning** of a suitable **compute platform**
- A **working, runnable installation**
- Building **hosting know-how** inside the **ErnES administrator team** (at least 2 people, to avoid single-point-of-failure outage situations).

### 2.2 Response times

**Test case:** In the baseline scenario, the onshore wind-farm area is increased from 2.0 % to 2.3 %, and the offshore capacity is reduced from 70 GW to 60 GW. The reconciliation takes **5.8 seconds** in 100prosim-Excel vs. **120 seconds** in 100prosim-Web — i.e. **20× the response time**.

**Practically usable response times** are a **precondition** for **operational usability**. After installation on a performant compute platform, the **first thing** to **test** is the response time achievable there. The greater the performance gain of that platform compared to the PC Deepti has been hosting on, the more the drawbacks of the chosen software solution will be offset. This test therefore becomes the **acid test** for whether 100prosim-Web in its current state is fit for deployment.

If practically usable response times cannot be reached that way, the software architecture will have to be reviewed and reworked.

### 2.3 Data model

**Proposal:** an interface to use the existing Excel data-model files instead of the integrated data model in the current 100prosim-Web (reasoning below).

#### 2.3.1 Traceability

In 100prosim-Excel, every parameter value has its source references and underlying assumptions directly and easily traceable via hyperlinks. That is the decisive difference versus a "game console"-style tool.

In the current 100prosim-Web, the **origin and defensibility** of parameter values are **not traceable**. This is, however, a **precondition** for users gaining **insight** through **critical engagement** with the parameters — which is how they broaden and **solidify** their **own judgement**. The same applies to parameter **updates** of the **baseline scenario** by the administrators, which are required from time to time to keep the tool deployment-ready.

#### 2.3.2 Alternative regions

In 100prosim-Excel, not only Germany as the base region was modelled, but also various German federal states (see <https://www.ernes.de/seite/422657/softwaretools.html>). This lets users reflect region-specific conditions. It is made possible by a modular architecture in which the data model alone holds all region-specific data and can therefore be swapped trivially. The data model is edited in an Excel file (`D.xlsx`), no special admin rights are required.

The current 100prosim-Web is restricted to a Germany data model. Creating or accessing data models for alternative regions is not supported. This means region-specific use — e.g. intensive use by various Green-party state working groups — is not possible.

**Proposal: interface** to use the **existing Excel data-model files** instead of the integrated data model in the current 100prosim-Web.

### 2.4 Cockpit functionality

#### 2.4.1 Availability of the base value

In 100prosim-Excel, after a target parameter has been modified (red arrow), the original value in the baseline-scenario data model is kept unchanged. When the modification is deleted, the original value from the data model automatically reappears in the scenario being worked on (green arrow).

This **availability of the base value allows** easy retraction of a modification that turns out not to make sense, and therefore **free experimentation** on a **stable foundation**.

In the current 100prosim-Web, the base value is no longer available after modification. Deleting the modification value in the modification field still leaves the last entered value displayed there. This makes it hard to keep track of state, particularly for complex modifications spanning multiple parameters.

#### 2.4.2 Baseline

In the current 100prosim-Web, the "Baseline" button (3rd from the right in the top menu bar) offers "Create baseline" to store the current state as the base scenario, so that after finishing a scenario modification "Reset to baseline" loads that base-scenario state again for a new modification. This only works if some prior scenario state had already been stored as a baseline (using "Baseline" in the top-right menu, then "Create baseline"). **Drawbacks:**

1. A **missed baseline creation** cannot be **made up retroactively** — no baseline will be available.
2. Unlike 100prosim-Excel, it is not possible to present users with a central base scenario as a shared baseline. Without that, **evaluating and comparing different modifications** becomes much **harder**.

**Proposal:** use the menu item "Baseline" → "Reset to baseline" to load the administered base scenario as the baseline (see also 2.4.1 and 2.4.2). The "Create baseline" menu item can be removed.

#### 2.4.3 Scenario reconciliation (Balance)

In 100prosim-Excel, exactly **two options** are offered for reconciling the scenario balance between consumption and generation: adjust the open solar area, or adjust the onshore wind-farm area.

The current 100prosim-Web has **6 buttons** instead:

- Run Goal Seek
- WS Balance Solar
- Sector + WS Solar Balance
- WS Balance Wind
- Sector + WS Wind Balance
- Refresh ("Aktualisieren")

Even with thorough explanation of the different actions each of these triggers in the user manual, users would be very strained to build confidence in picking the right button each time.

If I read this correctly, the buttons **"Goal Seek"** and **"Refresh"** are redundant, since their functions run automatically anyway when the "Scenario reconciliation" window is opened and after "Balance". If that's the case, they should be **removed**.

It is unclear why the buttons **"WS Balance …"** and **"Sector + WS … Balance"** have to be **pressed sequentially** in that order. This should be possible via a **single button** for WS Balance Wind and WS Balance Solar respectively. During testing, the buttons were mostly non-functional after scenario changes — pressing them produced no reconciliation and no busy indicator.

#### 2.4.4 Recalculate

In the current 100prosim-Web, users are prompted on the Consumption page to switch to the Renewables page after every user change of a target value and run "Recalculate Renewables" there. For user-input changes on the Renewables page, there is no explicit hint that "Recalculate Renewables" is required. The consequences of not pressing this button after a change are unclear.

In 100prosim-Excel, the **entire recalculation** of areas, renewables, and consumption runs **automatically and immediately after every change**. Users do not have to pay any attention to this, and misinterpretations caused by accidentally skipped recalculation are avoided.

#### 2.4.5 Save All Values

In the current 100prosim-Web, users are offered a "Save All Values" button on the "Areas" (Flächen) page. Presumably saving the area values is meant to allow restoring that saved area-data state later. However, this is not provided either for the Renewables user data or for the Consumption data. The function would only make sense if all scenario values were saved for later continued work on that scenario variant. That is apparently already possible via "Scenarios" → "Save current Scenario" (top menu bar, right). If so, the **"Save All Values" button is redundant** and unnecessarily confusing.

### 2.5 Cockpit layout

#### 2.5.1 English vs. German

In the current 100prosim-Web, a substantial portion of terminology has not yet been translated from English to German. Example: the **menu bars** already say "Erneuerbare Energien", but the page heading still reads "Renewable Energy…". All **columns** and **buttons** are also still labelled in **English**. This inconsistency imposes unnecessary demands on users and is a source of misinterpretation.

The **user manual** is also currently **entirely in English**, which makes it harder to **understand** the partially German menu functions. Using a Google translation of the page produces incorrect translations of individual terms and button labels.

#### 2.5.2 Number format

In the current 100prosim-Web, numeric values are rendered in **English number format** (comma for thousands grouping, dot as decimal separator). For users in the German-speaking world this can be very **confusing**, since they are used to exactly the opposite separator convention (dot for thousands grouping, comma as decimal separator).

The "Scenario reconciliation" page is the only one that is already switched to the German number format.

#### 2.5.3 Menu navigation

In 100prosim-Web the left-hand page side-menu is nearly identical on almost all pages, but it is missing on the pages "Consumption" (Verbrauch), "Annual Electricity" (Jahresstrom), and "User Manual" (Benutzerhandbuch). On the "Cockpit" page it is present but formatted differently.

The leftmost entries in the top menu bar would be duplicated and therefore superfluous if the side-menu were present on all pages and the "100prosim" entry were placed there as well.

#### 2.5.4 Results overview

Display in 100prosim-Web: either Status or Target. Display in 100prosim-Excel: Status and Target side-by-side, with each individual contribution shown.

**Proposal:** increase expressiveness by using a richer diagram modelled on 100prosim-Excel.

#### 2.5.5 Modification details

Currently completely absent from 100prosim-Web: charts showing how individual consumption parameters change and the resulting requirement for energy generation from the various sources. **Without graphical visualization**, relying only on numbers, the specifics of **complex energy scenarios cannot** be **surveyed** at anywhere near the same depth.

The PDF shows examples of visualization snippets from 100prosim-Excel (AH Cockpit2): Demand drivers on final-energy consumption (variant comparison), efficiency drivers, final-energy consumption by application area incl. base materials, primary-energy contributions by source, expansion of renewable energy sources.

#### 2.5.6 Flow diagram electricity / H₂

In the current 100prosim-Web the electricity and hydrogen flows for the target scenario are shown on the "Annual Electricity" page.

Even after an initial rework, the diagram still does **not correctly represent** the underlying **structures** of the scenario, some **values are assigned to the wrong nodes**, and because of the **small font** the diagram is hard to read. The reference is the corresponding diagram from 100prosim-Excel (see PDF page 10).

#### 2.5.7 Annual electricity profile

In the current 100prosim-Web, the daily state of charge of the electricity storage via hydrogen is shown over the year on the Bilanz page. The scenario reconciliation at the end of a modification adjusts solar- or wind-electricity generation so that the state of charge at the end of the year exactly matches that at the start of the year.

However, the minimum required **capacity of hydrogen storage is not directly readable** from the diagram, because the state at the start of the year arbitrarily sets the zero point rather than the lowest state of charge (here Min: -127,422 GWh). The minimum required capacity is Max − Min. In addition, the **daily differences** between consumption and wind/solar generation — which drive discharge or charge — are **not visible**.

In 100prosim-Excel, in contrast, the daily values of covering contributions or surpluses from wind/solar electricity and the shortfall compensation, and the resulting storage state of charge, are visualized very clearly.

Instead of absolute values in GWh, here the unit **"daily load"** is used. This lets the scaling stay consistent regardless of whether the scenario is for Germany or a regional one (cf. Section 2.3.2).

**Proposal: reproduce** the **100prosim-Excel layout**.

#### 2.5.8 Modification history

In 100prosim-Excel, the step-by-step modification of the base scenario can be logged. The PDF shows an excerpt of a sufficiency scenario in which today's demand for energy-consuming services was reduced by 10 % each vs. the status year, and the reduced consumption was balanced by reducing open solar areas (modification steps from right (1) to left (8)).

This function supports insight, because it lets you retrace even complex modifications in terms of the measure taken and its resulting effect.

The current 100prosim-Web **lacks a history function**.
