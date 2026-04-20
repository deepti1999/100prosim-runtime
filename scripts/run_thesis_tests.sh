#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== Core black-box suite =="
python3 manage.py test \
  simulator.test_bb_val \
  simulator.test_bb_calc \
  simulator.test_bb_bal \
  simulator.test_bb_e2e \
  -v 1

echo
echo "== Supplementary current-webapp black-box suite =="
python3 manage.py test \
  simulator.test_bb_current_app \
  simulator.test_bb_renewable_edit \
  simulator.test_e2e_current_scenario_flow \
  -v 1

echo
echo "== Main white-box suite =="
python3 manage.py test \
  simulator.test_wb_ws365_formula_engine \
  simulator.test_wb_scenario_state \
  simulator.test_wb_queue_jobs_middleware \
  simulator.test_it_current_recalc_contracts \
  -v 1

echo
echo "== WS365 regression suite =="
python3 manage.py test simulator.test_ws365_formulas -v 1
