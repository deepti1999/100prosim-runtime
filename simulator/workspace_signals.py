from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from simulator.workspace_service import ensure_user_workspace_data

@receiver(user_logged_in)
def ensure_workspace_on_login(sender, user, request, **kwargs):
    ensure_user_workspace_data(user)
