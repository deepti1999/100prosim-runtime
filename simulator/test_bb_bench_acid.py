"""Smoke test for ``scripts/bench_acid_test.py`` (T6 acid-test bench).

Invariant protected: the bench script — invoked with the simplest possible
arguments (``--scenario A --runs 1``) against the running local stack —
must exit 0 and emit a JSON document with at minimum:

- top-level ``status == "completed"``
- top-level ``elapsed_seconds`` numeric and > 0
- ``scenarios[0].scenario == "A"``
- ``scenarios[0].elapsed_seconds_median > 0``
- ``markdown_summary_path`` pointing under ``verification/final_audit/``

This is the V2 deliverable for Task 4 (T6) — covers the JSON-shape
contract that downstream readers (PROGRESS.md, BENCHMARK_LOG.md) rely on.

Skips itself if the bench script's required URL is unreachable (e.g.
when the test runner has no live server, like CI without a web dyno).
"""
import json
import os
import subprocess
import sys
import unittest
import urllib.request
from pathlib import Path

from django.test import SimpleTestCase

SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "bench_acid_test.py"
)
BASE_URL = os.environ.get("BENCH_TEST_BASE_URL", "http://localhost:8001")


def _server_reachable(url: str) -> bool:
    try:
        urllib.request.urlopen(url + "/healthz", timeout=2).read()
        return True
    except Exception:  # noqa: BLE001
        return False


class BenchAcidJsonShapeTests(SimpleTestCase):
    """Run the bench end-to-end with the smallest possible arg set and
    validate that the emitted JSON satisfies the documented contract."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SCRIPT.exists():
            raise unittest.SkipTest(f"bench script not found at {SCRIPT}")
        if not _server_reachable(BASE_URL):
            raise unittest.SkipTest(
                f"server not reachable at {BASE_URL}/healthz; bench requires "
                f"a live HTTP target"
            )

    def test_scenario_A_runs1_emits_well_formed_json(self):
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--scenario", "A",
                "--runs", "1",
                "--base-url", BASE_URL,
            ],
            capture_output=True, text=True, timeout=120,
            cwd=str(SCRIPT.parent.parent),
        )
        self.assertEqual(
            result.returncode, 0,
            f"bench exited {result.returncode}; stderr: {result.stderr[:500]}",
        )

        payload = json.loads(result.stdout)
        self.assertIn("status", payload)
        self.assertEqual(payload["status"], "completed")

        self.assertIn("elapsed_seconds", payload)
        self.assertIsInstance(payload["elapsed_seconds"], (int, float))
        self.assertGreater(payload["elapsed_seconds"], 0)

        self.assertIn("scenarios", payload)
        self.assertGreaterEqual(len(payload["scenarios"]), 1)

        sc = payload["scenarios"][0]
        self.assertEqual(sc["scenario"], "A")
        self.assertEqual(sc["status"], "completed")
        self.assertGreater(sc["elapsed_seconds_median"], 0)
        self.assertGreater(sc["elapsed_seconds_max"], 0)
        self.assertEqual(sc["completed"], 1)

        self.assertIn("markdown_summary_path", payload)
        self.assertIn("verification/final_audit/", payload["markdown_summary_path"])

        # Top-level provenance
        self.assertIn("timestamp", payload)
        self.assertIn("commit_sha", payload)
        self.assertIn("base_url", payload)
        self.assertEqual(payload["base_url"], BASE_URL)
