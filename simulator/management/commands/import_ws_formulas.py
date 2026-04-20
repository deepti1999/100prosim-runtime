"""Deprecated: legacy WS formula import command."""

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = (
        "Deprecated: WS formulas are now sourced from WS-365 services and unified Formula entries. "
        "No legacy WS template import is required."
    )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "This command is deprecated and intentionally does nothing."
            )
        )
        self.stdout.write(
            "Use the normal WS-365 flow (ws_365_service + unified recalc) instead."
        )
