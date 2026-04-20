from simulator.owner_scope import reset_current_owner, set_current_owner
from simulator.workspace_service import ensure_user_workspace_data

class OwnerScopeMiddleware:
    """
    Bind each authenticated non-staff request to its own isolated data workspace.
    Staff/admin users continue to use global baseline rows.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reset_current_owner()
        user = getattr(request, "user", None)

        if user and user.is_authenticated and not user.is_staff:
            ensure_user_workspace_data(user)
            set_current_owner(user)

        try:
            response = self.get_response(request)
        finally:
            reset_current_owner()

        return response
