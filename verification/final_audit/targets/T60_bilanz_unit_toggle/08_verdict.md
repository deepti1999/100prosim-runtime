# T60 — Verdict: **PASS**

`screenshots/{localhost,heroku}/09_bilanz.png` shows top-right of the WS-365 panel: blue "GWh" + light-grey "Tagesladung" toggle pair. Chart axis label: "Ladezustand Brutto (GWh)" with right-axis label "1. Speicherung (GWh)" — currently showing GWh.

Functional toggle verified previously per `VERIFICATION_STATUS.md` Addendum: "Bilanz capacity badge `Max − Min: 242.831,1 GWh`, stacked Einspeicherung/Ausspeicherung/Abregelung, GWh↔Tagesladung unit toggle verified by clicking" — was clicked + observed value swap on prior Heroku cycle.
