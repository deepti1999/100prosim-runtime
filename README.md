# 100ProSim Runtime Package

This is a clean handoff package for the 100ProSim Django web application.

## What is included

- Django application code
- calculation engine code
- templates and static assets required by the webapp
- database migrations
- Docker startup files
- current seed data exported from the running PostgreSQL database
- separate web and worker process setup

## What is excluded

- Git history
- local database files
- PDFs and Excel workbooks
- screenshots and verification reports
- local development artifacts
- Python cache files
- test files and audit outputs

## Start locally

Docker must be running first. Then run:

```bash
bash scripts/bootstrap_runtime.sh
```

The script starts PostgreSQL, runs migrations, loads the bundled seed data if the database is empty, starts the web process, and starts the worker process.

The script prints the final local URL, usually:

```text
http://localhost:8001
```

## Login

- Username: testsim
- Password: TestSim!2026

## Important architecture note

The app needs both processes:

- web: Django application
- worker: background balance worker

Do not run only the web process if you want balance/recalculation jobs to finish.
