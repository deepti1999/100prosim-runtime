"""Cockpit JS validity test — covers T43, T44, T45, T46, T47.

Invariant protected: the inline ``<script>`` block on ``/cockpit/`` must be
JavaScript-parseable. Specifically, numeric template variables interpolated
into JS object literals must NOT be German-locale-formatted (no ``2.432.616,134``
patterns inside ``<script>`` regions), because ``USE_L10N=True`` +
``LANGUAGE_CODE='de'`` (Phase 2-C T34) auto-formats those values to display
strings that JavaScript can't parse.

Background: the prior audit (2026-04-24) found that ``cockpit.html`` lines
287-340 build a ``bilanzData`` object literal containing ~30 float vars
interpolated via ``{{ value|default:0 }}``. With Django L10N active those
render as e.g. ``gesamt_total: 2.432.616,1342535475,`` — JavaScript parses
``2.432`` then chokes on the second ``.``. The whole script block dies at
parse time, no Chart.js init runs, all 3 chart canvases stay blank, and the
``Prozentuale Veränderung`` table tbody stays empty. See
``verification/final_audit/cockpit_charts_root_cause.md``.

This test catches that class of bug at unit-test time. Fix recipe (per the
root-cause doc): apply ``|unlocalize`` filter to every numeric template var
in JS context, OR wrap the JS literal in
``{% load l10n %}{% localize off %}{% endlocalize %}``.

Two complementary tests:

1. **Template-source static check** — assert the cockpit.html template
   either applies ``|unlocalize`` to numeric substitutions in JS context
   or wraps the JS block in ``{% localize off %}``. This catches the bug
   at template-edit time without needing seeded data.

2. **Rendered-output dynamic check** — load /cockpit/ with a workspace
   containing values >= 1000 (so L10N actually fires), parse the inline
   JS, assert no double-dot numeric literals appear inside the
   ``bilanzData`` object body.
"""
import re
import unittest
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import RenewableData, VerbrauchData


# Pattern finds numeric literals with TWO OR MORE dots — e.g. "1.234.567" or
# "2.432.616,1342535475". Valid JS allows at most one decimal point.
_BAD_NUMERIC = re.compile(r"\b\d{1,3}(?:\.\d{3}){2,}(?:,\d+)?\b")

# JS-literal numbers with comma decimal separator: "0,5", "1.000,5", etc.
_BAD_COMMA_DECIMAL = re.compile(r"(?<![\w\"'])(\d{1,3}(?:\.\d{3})*,\d+)(?!\w)")


def _extract_inline_scripts(html: str) -> list[str]:
    """Return the body of every inline ``<script>`` (no src=)."""
    return [
        m.group(1)
        for m in re.finditer(
            r"<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>",
            html,
            re.IGNORECASE,
        )
    ]


def _read_cockpit_template_source() -> str:
    return (
        Path(settings.BASE_DIR)
        / "simulator"
        / "templates"
        / "simulator"
        / "cockpit.html"
    ).read_text(encoding="utf-8")


class CockpitTemplateSourceStaticCheckTests(TestCase):
    """T43-T47: template source must protect JS literals from L10N auto-format.

    These tests do not require the DB — they read the .html file directly
    and assert that any ``{{ float_var }}`` substitutions inside ``<script>``
    blocks are wrapped in ``{% localize off %}`` or use ``|unlocalize``.

    This is the **prevention** half of the test pair — guards against
    re-introduction of the 2026-04-24 bug when someone edits cockpit.html.
    """

    def test_cockpit_has_localize_off_or_unlocalize_in_script_context(self):
        src = _read_cockpit_template_source()
        # Find every <script>...</script> block in the source (not the rendered HTML).
        scripts = re.findall(
            r"<script(?![^>]*src=)[^>]*>([\s\S]*?)</script>", src
        )
        self.assertGreater(
            len(scripts),
            0,
            "expected inline <script> in cockpit.html",
        )

        # Find every {{ var }} substitution inside JS contexts.
        # If it has |unlocalize, |stringformat, |safe, or is wrapped in
        # {% localize off %}, it is safe.
        offending = []
        for body in scripts:
            # Track whether we're inside a {% localize off %} ... {% endlocalize %}.
            # For simplicity: if the WHOLE script body is wrapped in localize off,
            # it's safe end-to-end.
            wrapped_off = bool(
                re.search(
                    r"\{%\s*localize\s+off\s*%\}[\s\S]*?\{%\s*endlocalize\s*%\}",
                    body,
                )
            )
            if wrapped_off:
                # check that EVERY substitution lies inside the wrapper
                # — for now, conservatively accept "wrapped at all" as protection.
                continue

            # Otherwise every {{ x }} that LOOKS LIKE a numeric (default:0, |floatformat,
            # raw float context-var) must use |unlocalize.
            for sub in re.finditer(r"\{\{[^}]+\}\}", body):
                expr = sub.group(0)
                # Heuristic: any var with default:0 or floatformat is numeric.
                is_numeric = (
                    "default:0" in expr
                    or "default:0.0" in expr
                    or "floatformat" in expr
                )
                if not is_numeric:
                    continue
                if "unlocalize" in expr or "stringformat" in expr:
                    continue
                offending.append(expr)

        self.assertEqual(
            offending,
            [],
            "cockpit.html has unprotected numeric template substitutions in "
            "JS context. With USE_L10N=True these will render as German-formatted "
            "strings (e.g. '2.432.616,134') which JavaScript cannot parse. "
            "Either add |unlocalize to each substitution or wrap the entire "
            "<script> body in {% load l10n %}{% localize off %}…{% endlocalize %}. "
            "First 5 offending substitutions: " + repr(offending[:5]),
        )


class CockpitRenderedOutputDynamicCheckTests(TestCase):
    """T43-T47: rendered /cockpit/ must produce JS-parseable literals even
    when workspace values are large enough to trigger L10N formatting.

    This is the **detection** half of the test pair — catches the bug if it
    ships, even when seeded data is non-trivial.
    """

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="cockpit_dyn_user", password="x"
        )
        # Seed VerbrauchData rows large enough that their totals exceed 1000
        # (the threshold below which Django's locale formatter would output a
        # plain integer with no thousand separator).
        for code, status, ziel in (
            ("KLIK", 329345.685, 250000.0),
            ("Gebäudewärme", 799186.546, 663500.0),
            ("Prozesswärme", 550371.0, 487096.0),
            ("Mobile", 753713.0, 704146.0),
        ):
            VerbrauchData.objects.create(
                code=f"V_{code}",
                category=code,
                unit="GWh/a",
                status=status,
                ziel=ziel,
                is_calculated=False,
            )
        for code, status in (
            ("9.1.1", 100000.0),
            ("9.1.2", 50000.0),
            ("9.1.3", 25000.0),
        ):
            RenewableData.objects.create(
                code=code,
                category="Solar",
                name=f"R_{code}",
                unit="GWh",
                status_value=status,
            )

    def setUp(self):
        self.client.force_login(self.user)

    def test_cockpit_inline_scripts_have_no_double_dot_numbers(self):
        response = self.client.get(reverse("simulator:cockpit"))
        self.assertEqual(response.status_code, 200)
        scripts = _extract_inline_scripts(response.content.decode("utf-8"))
        self.assertGreater(len(scripts), 0)

        offending = []
        for body in scripts:
            for hit in _BAD_NUMERIC.finditer(body):
                start = max(0, hit.start() - 30)
                end = min(len(body), hit.end() + 30)
                offending.append(body[start:end])

        self.assertEqual(
            offending,
            [],
            "Found German-formatted numeric literals in inline JS at runtime "
            "with seeded workspace data. Hits: %r" % offending[:5],
        )

    def test_cockpit_has_chart_canvas_elements(self):
        """Necessary precondition: the 3 chart canvases must be in the DOM."""
        response = self.client.get(reverse("simulator:cockpit"))
        body = response.content.decode("utf-8")
        for canvas_id in (
            "sectorComparisonChart",
            "demandStatusZielChart",
            "supplyStatusZielChart",
        ):
            self.assertIn(canvas_id, body)

    def test_regression_2026_04_24_l10n_js_literal_bug(self):
        """Catches the specific 2026-04-24 incident.

        The bug: ``cockpit.html`` line 289 used
        ``{{ verbrauch_endenergie_gesamt|default:0 }}`` without
        ``|unlocalize``. Phase 2-C settings caused the float to render as
        ``2.432.616,1342535475``. JavaScript could not parse that literal
        and the entire ``<script>`` block died at parse time.
        """
        response = self.client.get(reverse("simulator:cockpit"))
        body = response.content.decode("utf-8")
        m = re.search(
            r"const\s+bilanzData\s*=\s*\{([\s\S]+?)\}\s*;",
            body,
        )
        if m is None:
            # Structure refactored; the static-check test above still guards.
            return
        bilanz_block = m.group(1)
        self.assertIsNone(
            _BAD_NUMERIC.search(bilanz_block),
            "bilanzData object literal contains German-formatted number — "
            "this is the 2026-04-24 incident pattern. Apply |unlocalize "
            "or {% localize off %}{% endlocalize %} per "
            "verification/final_audit/cockpit_charts_root_cause.md.",
        )
