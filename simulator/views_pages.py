"""Page-oriented view exports."""

from .page_auth import (
    landing_page,
    login_view,
    logout_view,
    main_simulation,
    register_view,
    test_storage,
    user_guide,
    user_manual,
)
from .page_bilanz import bilanz_view
from .page_cockpit import cockpit_view
from .page_landuse import landuse_detail, landuse_list
from .page_renewable import (
    annual_electricity_view,
    renewable_list,
)
from .page_smard import smard_solar_wind
from .views import update_landuse_percent, verbrauch_view
from .ws_api import ws_view

__all__ = [
    "annual_electricity_view",
    "bilanz_view",
    "cockpit_view",
    "landing_page",
    "landuse_detail",
    "landuse_list",
    "login_view",
    "logout_view",
    "main_simulation",
    "register_view",
    "renewable_list",
    "smard_solar_wind",
    "test_storage",
    "update_landuse_percent",
    "user_guide",
    "user_manual",
    "verbrauch_view",
    "ws_view",
]
