"""
Phase B (T65) — region switcher endpoint.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST


@require_POST
@login_required
def set_active_region(request):
    """Persist the selected region_code on the user's session.

    Validates that the requested code matches an existing active Region.
    Redirects to HTTP_REFERER (or main_simulation as a safe fallback)
    so the user lands back on the page they came from with the new
    region scope already in effect.
    """
    code = (request.POST.get("region_code") or "").strip()
    if not code:
        return HttpResponseBadRequest("region_code required")

    # Local import keeps test isolation clean (Region model is in
    # simulator.models which transitively imports a lot).
    from simulator.models import Region

    if not Region.objects.filter(code=code, active=True).exists():
        return HttpResponseBadRequest(f"unknown or inactive region: {code}")

    request.session["active_region_code"] = code
    request.session.modified = True

    referer = request.META.get("HTTP_REFERER") or ""
    if referer.startswith("/"):
        return redirect(referer)
    return redirect(reverse("simulator:main_simulation"))
