"""Health endpoints for load balancers and uptime monitors."""

from django.db import connections
from django.http import JsonResponse

def healthz(request):
    """Liveness probe: process is up."""
    return JsonResponse({"status": "ok"})

def readyz(request):
    """Readiness probe: app can talk to primary database."""
    try:
        conn = connections["default"]
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ready"})
    except Exception as exc:
        return JsonResponse({"status": "not_ready", "error": str(exc)}, status=503)
