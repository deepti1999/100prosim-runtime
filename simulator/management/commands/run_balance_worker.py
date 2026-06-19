import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from simulator.balance_jobs import claim_next_job, recover_interrupted_jobs, run_balance_job
from simulator.models import BalanceJob

class Command(BaseCommand):
    help = "Run background worker for Sector+WS balance jobs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process at most one available job and exit.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=2.0,
            help="Seconds to sleep when queue is empty (default: 2.0).",
        )

    def handle(self, *args, **options):
        run_once = bool(options.get("once"))
        sleep_seconds = max(0.1, float(options.get("sleep", 2.0)))

        self.stdout.write(self.style.SUCCESS("Balance worker started"))
        recovered = recover_interrupted_jobs()
        if recovered["requeued"] or recovered["failed"]:
            self.stdout.write(
                "Recovered interrupted jobs: "
                f"{recovered['requeued']} requeued, {recovered['failed']} failed"
            )

        while True:
            job = claim_next_job()
            if job is None:
                if run_once:
                    self.stdout.write("No queued jobs. Exiting.")
                    return
                time.sleep(sleep_seconds)
                continue

            self.stdout.write(f"Processing {job.id} ({job.job_type})...")
            try:
                result = run_balance_job(job)
                job.status = BalanceJob.STATUS_SUCCEEDED
                job.result = result or {}
                job.error = ""
                job.finished_at = timezone.now()
                job.save(update_fields=["status", "result", "error", "finished_at", "updated_at"])
                self.stdout.write(self.style.SUCCESS(f"Completed {job.id}"))
            except Exception as exc:
                job.status = BalanceJob.STATUS_FAILED
                job.error = str(exc)
                job.finished_at = timezone.now()
                job.save(update_fields=["status", "error", "finished_at", "updated_at"])
                self.stderr.write(self.style.ERROR(f"Failed {job.id}: {exc}"))

            if run_once:
                return
