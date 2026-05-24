from django.urls import path

from .views_balance import (
    balance_all,
    balance_energy,
    balance_energy_lu6,
    balance_full_system,
    balance_ws_storage,
)
from .views_pages import (
    annual_electricity_view,
    bilanz_view,
    cockpit_view,
    landing_page,
    landuse_detail,
    landuse_list,
    login_view,
    logout_view,
    main_simulation,
    register_view,
    renewable_list,
    smard_solar_wind,
    test_storage,
    update_landuse_percent,
    user_guide,
    user_manual,
    verbrauch_view,
    ws_view,
)
from .views_recalc import (
    create_baseline,
    create_scenario,
    delete_scenario,
    get_baseline_info,
    list_scenarios,
    recalc_verbrauch_view,
    recalc_ws_formulas_view,
    rename_scenario,
    restore_baseline,
    restore_scenario,
    run_full_recalc_view,
    run_renewables_recalc_view,
    save_renewable_user_input,
    save_all_user_inputs,
    save_and_recalculate_verbrauch,
    save_verbrauch_user_input,
    unified_recalc_view,
    update_user_percent,
    update_verbrauch_bulk,
)
from .views import gebaeudewaerme_view, update_user_percent_by_code
from .views_region import set_active_region
from .page_historie import historie_view
from .page_modifikationsdetails import modifikationsdetails_view
from .views_ws import (
    ws_api_apply_balance,
    ws_api_apply_balance_wind,
    ws_api_apply_full_balance,
    ws_api_apply_full_balance_wind,
    ws_api_balance_job_status,
    ws_api_data,
    ws_api_goal_seek,
    ws_api_summary,
)

app_name = 'simulator'

urlpatterns = [
    # Landing and Authentication
    path('', landing_page, name='landing_page'),
    path('guide/', user_guide, name='user_guide'),
    path('test-storage/', test_storage, name='test_storage'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Simulation Pages (Protected)
    path('simulation/', main_simulation, name='main_simulation'),
    path('user-manual/', user_manual, name='user_manual'),
    # Phase 6-A (T61-T63): Modifikations-Historie
    path('historie/', historie_view, name='historie'),
    # Phase 6-B (T48-T52): Variantenvergleich-Charts
    path('modifikationsdetails/', modifikationsdetails_view, name='modifikationsdetails'),
    path('landuse/', landuse_list, name='landuse_list'),
    path('landuse/<int:pk>/update_percent/', update_landuse_percent, name='update_landuse_percent'),
    path('landuse/<int:pk>/', landuse_detail, name='landuse_detail'),
    path('renewable/', renewable_list, name='renewable_list'),
    path('verbrauch/', verbrauch_view, name='verbrauch'),
    # §2.3 Phase A (T64): expose the existing GebaeudewaermeData view that was
    # previously dead code so the provenance popover ships on all 4 parameter
    # pages per Pascal's deliverable spec. The view itself is unchanged.
    path('gebaeudewarme/', gebaeudewaerme_view, name='gebaeudewaerme'),
    path('ws/', ws_view, name='ws'),  # NEW: WS 365 Days
    path('cockpit/', cockpit_view, name='cockpit'),
    path('annual-electricity/', annual_electricity_view, name='annual_electricity'),
    path('smard/', smard_solar_wind, name='smard_solar_wind'),
    path('bilanz/', bilanz_view, name='bilanz'),
    # §2.3 Phase B (T65): region switcher endpoint — POST region_code,
    # session updated, user redirected back. Validates against
    # Region.objects.filter(active=True).
    path('api/region/set/', set_active_region, name='set_active_region'),
    path('api/balance-energy/', balance_energy, name='balance_energy'),
    path('api/balance-energy-lu6/', balance_energy_lu6, name='balance_energy_lu6'),
    path('api/ws/balance/', balance_ws_storage, name='balance_ws_storage'),
    path('api/balance-full/', balance_full_system, name='balance_full_system'),
    path('api/balance-all/', balance_all, name='balance_all'),
    
    # WS 365 API Endpoints
    path('api/ws/data/', ws_api_data, name='ws_api_data'),
    path('api/ws/summary/', ws_api_summary, name='ws_api_summary'),
    path('api/ws/goal-seek/', ws_api_goal_seek, name='ws_api_goal_seek'),
    path('api/ws/apply-balance/', ws_api_apply_balance, name='ws_api_apply_balance'),
    path('api/ws/apply-full-balance/', ws_api_apply_full_balance, name='ws_api_apply_full_balance'),
    path('api/ws/apply-balance-wind/', ws_api_apply_balance_wind, name='ws_api_apply_balance_wind'),
    path('api/ws/apply-full-balance-wind/', ws_api_apply_full_balance_wind, name='ws_api_apply_full_balance_wind'),
    path('api/ws/balance-job/<uuid:job_id>/', ws_api_balance_job_status, name='ws_api_balance_job_status'),
    
    # API Endpoints
    path('api/update-user-percent/', update_user_percent, name='update_user_percent'),
    path('api/update/<str:code>/', update_user_percent_by_code, name='update_user_percent_code'),
    path('api/save-all-inputs/', save_all_user_inputs, name='save_all_inputs'),
    path('api/run-full-recalc/', run_full_recalc_view, name='run_full_recalc'),
    path('api/recalc-renewables/', run_renewables_recalc_view, name='recalc_renewables'),
    path('api/recalc-verbrauch/', recalc_verbrauch_view, name='recalc_verbrauch'),
    path('api/recalc-ws-formulas/', recalc_ws_formulas_view, name='recalc_ws_formulas'),
    path('api/update-verbrauch-bulk/', update_verbrauch_bulk, name='update_verbrauch_user_percent_bulk'),
    path('api/save-renewable-user-input/', save_renewable_user_input, name='save_renewable_user_input'),
    path('api/save-recalc-verbrauch/', save_and_recalculate_verbrauch, name='save_recalc_verbrauch'),
    path('api/save-verbrauch-user-input/', save_verbrauch_user_input, name='save_verbrauch_user_input'),
    path('api/unified-recalc/', unified_recalc_view, name='unified_recalc'),
    
    # Baseline Backup Management
    path('api/baseline/create/', create_baseline, name='create_baseline'),
    path('api/baseline/restore/', restore_baseline, name='restore_baseline'),
    path('api/baseline/info/', get_baseline_info, name='get_baseline_info'),
    path('api/scenario/create/', create_scenario, name='create_scenario'),
    path('api/scenario/list/', list_scenarios, name='list_scenarios'),
    path('api/scenario/<int:scenario_id>/restore/', restore_scenario, name='restore_scenario'),
    path('api/scenario/<int:scenario_id>/rename/', rename_scenario, name='rename_scenario'),
    path('api/scenario/<int:scenario_id>/delete/', delete_scenario, name='delete_scenario'),
]
