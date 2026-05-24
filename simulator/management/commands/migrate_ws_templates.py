"""Deprecated: legacy WS template migration command."""

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = (
        "Deprecated: WSFormulaTemplate migration is no longer used in the WS-365 architecture."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Accepted for backward compatibility; no action is performed.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Accepted for backward compatibility; no action is performed.',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "This command is deprecated and intentionally does nothing."
            )
        )
        self.stdout.write(
            "Use WS-365 services and unified Formula entries directly."
        )
