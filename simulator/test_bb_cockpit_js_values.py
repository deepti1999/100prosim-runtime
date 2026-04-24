"""Cockpit JS-value contract test — covers T43, T44, T45, T46, T47.

Invariant protected: the ``/cockpit/`` page must expose every numeric chart
value via HTML ``data-*`` attributes whose serialised text is JavaScript
``parseFloat()``-clean (matches ``^-?\\d+(\\.\\d+)?$``). This is the contract
that closes bug #111.

Background: pre-fix, ``cockpit.html`` interpolated 36 floats directly into
a JS object literal under ``USE_L10N=True`` + ``LANGUAGE_CODE='de'``. Django
auto-formatted those floats as German display strings (``2.432.616,134``)
which JS literals cannot parse → entire ``<script>`` block parse-failed →
all 3 Chart.js canvases stayed blank. Fix: render values into a hidden
``<div id="bilanzDataPayload">`` with one ``data-<scope>-<key>`` attribute
per value, each rendered with the ``|unlocalize`` filter (English numeric
formatting). JS reads via ``document.getElementById('bilanzDataPayload')
.dataset.<scopeKey>`` and applies ``parseFloat()``.

This test is structurally robust against seed-data quality: it asserts
PRESENCE of ≥30 ``data-(status|ziel)-*`` attributes (post-fix expects 36),
and PARSEABILITY of every value (matches ``^-?\\d+(\\.\\d+)?$``). Pre-fix
the page has 0 such attributes → assertion fails. Post-fix the page has 36
parseable attributes → assertion passes.
"""
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


_PARSE_FLOAT_CLEAN = re.compile(r"^-?\d+(\.\d+)?$")
_BILANZ_ATTR = re.compile(
    r'data-(status|ziel)-[\w-]+\s*=\s*"([^"]*)"',
    re.IGNORECASE,
)


class CockpitDataAttributesParseFloatTests(TestCase):
    """T43-T47: cockpit must expose all bilanz values as parseFloat-clean
    data-attributes (closes bug #111)."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="cockpit_data_attr_user", password="x"
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_cockpit_exposes_bilanz_values_via_data_attributes(self):
        response = self.client.get(reverse("simulator:cockpit"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")

        matches = _BILANZ_ATTR.findall(body)
        self.assertGreaterEqual(
            len(matches),
            30,
            f"expected >=30 data-(status|ziel)-* attributes carrying chart "
            f"values; got {len(matches)}. Pre-fix this is 0 because "
            f"cockpit.html still interpolates floats directly into JS literals "
            f"(#111). Post-fix a #bilanzDataPayload div should expose 36.",
        )

        offending = [v for _scope, v in matches if not _PARSE_FLOAT_CLEAN.match(v)]
        self.assertEqual(
            offending,
            [],
            f"every cockpit data-(status|ziel)-* attribute must be "
            f"JS parseFloat-clean (^-?\\d+(\\.\\d+)?$). Use |unlocalize "
            f"to defeat Django L10N. First 10 offending values: "
            f"{offending[:10]}",
        )

    def test_cockpit_payload_div_exists(self):
        """Document the post-fix structural contract."""
        response = self.client.get(reverse("simulator:cockpit"))
        body = response.content.decode("utf-8")
        self.assertIn(
            'id="bilanzDataPayload"',
            body,
            "expected a <div id='bilanzDataPayload'> carrying chart values "
            "as data-attributes per the bug #111 fix.",
        )
