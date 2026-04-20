# 100ProSim Runtime Bundle

This folder is the cleaned deployment handoff for the current 100ProSim web application.

## Included

- Django application code
- runtime templates and static assets
- calculation and orchestration modules
- database migrations
- bundled seed data
- bundled black-box and white-box tests
- Docker-based startup files
- process definition for separate web and worker execution

## Excluded

- thesis material
- PDFs
- screenshots not needed by runtime
- developer handoff notes
- temporary files

## Quick preview

Use the command in [START_HERE.md](START_HERE.md):

```bash
bash scripts/bootstrap_runtime.sh
```

This starts:

- PostgreSQL
- Django web application
- balance worker

and loads seed data when the target database is empty.

If local port `8001` is already occupied, the bootstrap script automatically selects the next free port and prints the final URL.

## Runtime architecture

The bundle is prepared for a production-style setup with:

- Django web application
- separate background worker for `BalanceJob` processing
- PostgreSQL as the main deployment database

The application can also be hosted on other platforms if they provide:

- a Python 3.11 runtime
- PostgreSQL
- one web process
- one worker process

## Main files

- `START_HERE.md`: first-run instructions
- `.env.example`: environment-variable template
- `docker-compose.yml`: local container startup
- `Dockerfile`: image build definition
- `Procfile`: separate web and worker process model

## Running the bundled tests

From this folder:

```bash
bash scripts/run_thesis_tests.sh
```

This runs the bundled black-box and white-box suites and prints pass/fail output directly in the terminal.

The exact test modules and their individual commands are listed in `START_HERE.md`.

## Production notes

Before public deployment, the host should set at least:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`

If the host uses a managed platform, the `web` and `worker` process split should be preserved.
