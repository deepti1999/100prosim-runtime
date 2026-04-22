"""Modifikations-Historie page (Phase 6-A, T61–T63, PDF §2.5.8).

Renders an inspectable log of user-initiated modifications. Read-only by
design — this is a paper trail, not a time-machine. Scenario snapshots
cover the time-travel use case.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import ModificationHistoryEntry


@login_required
def historie_view(request):
    """Render the modification history for the current user.

    Staff see all entries (cross-user); regular users see only their own.
    Limited to the most recent 500 rows to keep the DOM size sane.
    """
    qs = ModificationHistoryEntry.objects.all()
    if not request.user.is_staff:
        qs = qs.filter(owner=request.user)

    total = qs.count()
    entries = list(qs[:500])
    entries_serialized = [
        {
            "id": e.id,
            "model_label": e.model_label,
            "code": e.code,
            "field": e.field,
            "value_before": e.value_before,
            "value_after": e.value_after,
            "source": e.source,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]

    context = {
        "entries": entries,
        "entries_serialized": entries_serialized,
        "total_count": total,
        "display_count": len(entries),
        "capped_at": 500,
        "current_section": "historie",
    }
    return render(request, "simulator/historie.html", context)
