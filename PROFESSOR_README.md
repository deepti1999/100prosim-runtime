# 100ProSim Runtime Package

This is a clean runtime handoff package for the Django web application.

Start locally with Docker:

```bash
bash scripts/bootstrap_runtime.sh
```

The startup script runs PostgreSQL, migrations, seed import, web, and worker.

Default login:

- Username: testsim
- Password: TestSim!2026

Included: application code, migrations, templates/static assets, Docker startup files, and current seed data.

Excluded: Git history, local database files, PDFs, screenshots, verification reports, workbooks, local development artifacts, caches, and tests.
