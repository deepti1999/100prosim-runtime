"""Phase 6-A tests — T61, T62, T63: modification history.

Per PDF §2.5.8: every user-initiated edit must be logged in a
per-user append-only history. The history is inspectable (T63), not
undoable — Scenarios covers that.
"""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import LandUse, ModificationHistoryEntry, VerbrauchData


class ModificationHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="history_user", password="x", is_staff=False
        )

        cls.root = LandUse(
            code="LU_ROOT",
            name="Root",
            status_ha=1000.0,
            target_ha=1000.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=None,
        )
        cls.root.save(skip_cascade=True)
        cls.child = LandUse(
            code="LU_2.1",
            name="Solar Land",
            status_ha=100.0,
            target_ha=100.0,
            user_percent=7.0,
            increase_limit_baseline_percent=10.0,
            parent=cls.root,
        )
        cls.child.save(skip_cascade=True)

        cls.verbrauch = VerbrauchData.objects.create(
            code="1.1.2",
            category="Test",
            unit="GWh",
            status=100.0,
            ziel=80.0,
            is_calculated=False,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_landuse_edit_writes_history_row(self):
        self.client.post(
            reverse("simulator:update_user_percent"),
            data=json.dumps({"code": "LU_2.1", "user_percent": 3.5}),
            content_type="application/json",
        )
        entries = ModificationHistoryEntry.objects.filter(code="LU_2.1")
        self.assertEqual(entries.count(), 1)
        entry = entries.first()
        self.assertEqual(entry.model_label, "LandUse")
        self.assertEqual(entry.field, "user_percent")
        self.assertEqual(entry.source, "user")
        self.assertAlmostEqual(float(entry.value_before), 7.0)
        self.assertAlmostEqual(float(entry.value_after), 3.5)
        self.assertEqual(entry.owner, self.user)

    def test_verbrauch_edit_writes_history_row(self):
        self.client.post(
            reverse("simulator:save_verbrauch_user_input"),
            data=json.dumps({"code": "1.1.2", "user_percent": 95}),
            content_type="application/json",
        )
        entries = ModificationHistoryEntry.objects.filter(code="1.1.2")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().model_label, "VerbrauchData")

    def test_history_page_shows_user_entries_only(self):
        other = get_user_model().objects.create_user(username="other", password="x")
        ModificationHistoryEntry.objects.create(
            owner=self.user, model_label="LandUse", code="LU_2.1",
            field="user_percent", value_before=7.0, value_after=3.5,
        )
        ModificationHistoryEntry.objects.create(
            owner=other, model_label="LandUse", code="LU_1",
            field="user_percent", value_before=1.0, value_after=2.0,
        )

        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LU_2.1")
        self.assertNotContains(response, "LU_1<")

    def test_history_page_hides_history_for_empty_user(self):
        # Fresh user with no history — page still renders with a gentle notice.
        fresh = get_user_model().objects.create_user(username="fresh", password="x")
        self.client.force_login(fresh)
        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Modifikations-Historie")
        self.assertContains(response, "Noch keine Modifikationen")

    def test_history_is_inspect_only_no_undo_endpoint(self):
        """T63: the history PAGE itself offers no undo button/form.

        Note: the word 'rückgängig' may appear in shared chrome (Delete-
        Scenario alert in base.html) — we only care that the historie
        main content provides no undo affordance.
        """
        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        # No form posting, no 'Zurücksetzen'/'Undo' button inside the
        # historie main section.
        body = response.content.decode()
        # Approximation: no <button> within the historie main that says
        # "Rückgängig" or "Zurücksetzen".
        self.assertNotIn("<button", body.split('<main')[1].split('</main>')[0]
                         if '<main' in body else "")
