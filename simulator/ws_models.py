from django.conf import settings
from django.db import models
import re

from simulator.owner_scope import OwnerScopedManager


def _ws_default_region_pk():
    """Lazy default for WSData.region — avoids circular import with models.py.

    Returns DE.pk at row-create time. None during the brief window before
    migration 0052 has run on a fresh DB; the AddField step in the WSData
    region migration keeps the column nullable until after the backfill.
    """
    from simulator.models import Region

    try:
        return Region.objects.get(code="DE").pk
    except Region.DoesNotExist:
        return None


class WSData(models.Model):
    """
    Minimal WS input table.
    Only 4 daily input columns are stored in DB.
    Derived WS values are computed from WS365Formula expressions.
    """

    tag_im_jahr = models.IntegerField(help_text="Tag im Jahr (Day in Year)")

    # Input columns (promille)
    solar_promille = models.FloatField(null=True, blank=True, help_text="Solar Promille")
    wind_promille = models.FloatField(null=True, blank=True, help_text="Wind Promille")
    heizung_abwaerm_promille = models.FloatField(
        null=True,
        blank=True,
        help_text="Heizung Abwärm Promille",
    )
    verbrauch_promille = models.FloatField(null=True, blank=True, help_text="Verbrauch Promille")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ws_rows",
        db_index=True,
    )

    # Phase C (T66) — WSData is now per-(owner, region) workspace state.
    # Without this FK, a BB user sees DE timeseries derived from DE
    # parameters. PROTECT mirrors the LandUse/Renewable/Verbrauch
    # convention from Phase B step 2.
    region = models.ForeignKey(
        "simulator.Region",
        on_delete=models.PROTECT,
        default=_ws_default_region_pk,
        related_name="+",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OwnerScopedManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["tag_im_jahr"]
        verbose_name = "WS Data Entry"
        verbose_name_plural = "WS Data Entries"
        indexes = [
            models.Index(fields=["owner", "tag_im_jahr"]),
            models.Index(fields=["region", "tag_im_jahr"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "region", "tag_im_jahr"],
                name="wsdata_owner_region_day_uniq",
            ),
            models.UniqueConstraint(
                fields=["region", "tag_im_jahr"],
                condition=models.Q(owner__isnull=True),
                name="wsdata_global_region_day_uniq",
            ),
        ]

    def __str__(self):
        return f"Day {self.tag_im_jahr}"

class WS365Formula(models.Model):
    """
    Formula registry for WS 365 derived columns.

    `daily` stage formulas run day-by-day in order.
    `post` stage formulas run after all daily rows are computed
    (for operations like COL_MIN/COL_SUM shifts).
    """

    STAGE_DAILY = "daily"
    STAGE_POST = "post"
    STAGE_CHOICES = [
        (STAGE_DAILY, "Daily (day-by-day 1-365)"),
        (STAGE_POST, "Post (after full 365-day pass)"),
    ]

    column_name = models.CharField(
        max_length=64,
        unique=True,
        help_text="Output column key used by WS API/Frontend (example: einspeich).",
    )
    stage = models.CharField(
        max_length=16,
        choices=STAGE_CHOICES,
        default=STAGE_DAILY,
        help_text="Daily runs during day loop; Post runs after all days are available.",
    )
    order = models.PositiveIntegerField(
        default=100,
        help_text="Execution order inside the selected stage.",
    )
    expression = models.TextField(
        help_text=(
            "Main expression. Helpers: IF, MIN, MAX, ABS, ROUND, PREV('column'). "
            "Post-stage also supports COL_MIN/COL_MAX/COL_SUM."
        )
    )
    day1_expression = models.TextField(
        blank=True,
        help_text="Optional day-1 override expression. Leave blank to use main expression.",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["stage", "order", "column_name"]
        verbose_name = "WS 365 Formula"
        verbose_name_plural = "WS 365 Formulas"
        indexes = [
            models.Index(fields=["is_active", "stage", "order"]),
        ]

    def __str__(self):
        state = "ON" if self.is_active else "OFF"
        return f"{state} [{self.stage}] {self.column_name}"

    def save(self, *args, **kwargs):
        """
        Normalize column key so users can type friendly names in admin while
        formulas still get valid Python-like identifiers.
        """
        key = (self.column_name or "").strip().lower()
        key = re.sub(r"[^a-z0-9_]+", "_", key)
        key = re.sub(r"_+", "_", key).strip("_")
        if key and key[0].isdigit():
            key = f"col_{key}"
        self.column_name = key or self.column_name
        super().save(*args, **kwargs)
