from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from simulator.workspace_service import ensure_user_workspace_data


_DEFAULT_REGION_CODE = "DE"


@receiver(user_logged_in)
def ensure_workspace_on_login(sender, user, request, **kwargs):
    # Phase B (T65): hand the active region from session to the
    # workspace service so first-login of a fresh user creates the
    # correct per-region overlay. Defaults to DE when session is
    # missing the key (existing behaviour for single-region setups).
    region_code = _DEFAULT_REGION_CODE
    if request is not None:
        session = getattr(request, "session", None)
        if session is not None:
            try:
                region_code = session.get("active_region_code", _DEFAULT_REGION_CODE) or _DEFAULT_REGION_CODE
            except AttributeError:
                pass

    ensure_user_workspace_data(user, region_code=region_code)
