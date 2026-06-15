from simulator.owner_scope import reset_current_owner, set_current_owner
from simulator.region_scope import reset_current_region, set_current_region
from simulator.workspace_service import ensure_user_workspace_data


_DEFAULT_REGION_CODE = "DE"
_GLOBAL_ADMIN_PREFIXES = (
    "/admin/",
    "/admin-versionen/",
    "/admin-rollen/",
)


def _uses_global_admin_scope(request):
    """Django/admin-control pages edit shared admin data, not user workspaces."""
    path = getattr(request, "path_info", "") or getattr(request, "path", "") or ""
    return any(path.startswith(prefix) for prefix in _GLOBAL_ADMIN_PREFIXES)


def _active_region_code(request):
    """Read active region from session, default DE.

    Tolerates exotic test fixtures that lack `request.session` entirely
    (e.g. unit tests building requests manually) — falls back to DE
    rather than 500-ing the request.
    """
    session = getattr(request, "session", None)
    if session is None:
        return _DEFAULT_REGION_CODE
    try:
        return session.get("active_region_code", _DEFAULT_REGION_CODE) or _DEFAULT_REGION_CODE
    except AttributeError:
        return _DEFAULT_REGION_CODE


class OwnerScopeMiddleware:
    """
    Bind each authenticated webapp request to its own isolated data workspace.
    Django/admin-control URLs continue to use global admin rows.

    Phase B (T65): also binds the active region (from session, default
    DE) to a thread-local so OwnerScopedManager can scope queries by
    region. The user's workspace is ensured per (owner, region).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reset_current_owner()
        reset_current_region()

        region_code = _active_region_code(request)
        set_current_region(region_code)

        user = getattr(request, "user", None)

        if user and user.is_authenticated and not _uses_global_admin_scope(request):
            ensure_user_workspace_data(user, region_code=region_code)
            set_current_owner(user)

        try:
            response = self.get_response(request)
        finally:
            reset_current_owner()
            reset_current_region()

        return response
