# FastAPI + Prisma Postgres Records API

I built this project to demonstrate a complete backend deployment: creating a
Python API, connecting it to PostgreSQL, deploying it as a web service, and
fetching database records over HTTP. I use **FastAPI**, **Prisma Postgres**,
**Render**, and **uv**. The API exposes public sample records, and I keep the
application in one Python file.

API: [fetch records](https://demo-fastapi.onrender.com)
\| [interactive documentation](https://demo-fastapi.onrender.com/docs)
\| [process health](https://demo-fastapi.onrender.com/health)

## Contents

- [How it works](#how-it-works)
- [Repository files](#repository-files)
- [Run locally with uv](#run-locally-with-uv)
- [Set up the production database](#set-up-the-production-database)
- [Fetch data from the API](#fetch-data-from-the-api)
- [Deploy to Render](#deploy-to-render)
- [Source code walkthrough](#source-code-walkthrough)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## How it works

```mermaid
flowchart LR
    Client[Browser, curl, or another application] -->|GET /records| API[FastAPI on Render]
    API -->|SQL over TLS through Psycopg| DB[(One Prisma Postgres production database)]
    DB -->|Rows| API
    API -->|JSON| Client
```

Prisma Postgres is the managed PostgreSQL hosting service. I connect with
Psycopg, a Python PostgreSQL driver, so this repository does not need Prisma ORM,
generated clients, Node.js, or npm. Prisma supports ordinary
[PostgreSQL clients](https://www.prisma.io/docs/postgres/database/connecting-to-your-database).

I use exactly **one production database** for this project. Local manual runs
connect to that same database. The pooled runtime URL and the direct setup URL
are two ways to reach the same database; they are not separate databases.
Automated tests mock the connection and create no database. Preview environments
are disabled, and I configure no Prisma branches or preview database automation.

The provisioned Prisma project and database are named `demo-api-production` in
Singapore, and the project's only branch is the production `main` branch.

This replaces the original Railway service and Supabase integration. Because
the previous resources were deleted, setup creates a fresh table and sample
data; it does not recover the deleted records.

## Repository files

| File | Purpose |
| --- | --- |
| [`main.py`](main.py) | Application, response model, health endpoint, and SQL read endpoint. |
| [`setup_database.py`](setup_database.py) | Explicit, manual database initialization command. |
| [`schema.sql`](schema.sql) | Table definition and three public sample records. |
| [`pyproject.toml`](pyproject.toml) | Metadata, Python 3.14.7 requirement, dependencies, Ruff rules, and Pyrefly configuration. |
| [`uv.lock`](uv.lock) | Exact dependency versions for repeatable installation. |
| [`.python-version`](.python-version) | Pins Python 3.14.7 for uv and Render. |
| [`.env.example`](.env.example) | Placeholder connection strings without real credentials. |
| [`render.yaml`](render.yaml) | Render settings and disabled Blueprint previews. |
| [`tests/test_api.py`](tests/test_api.py) | HTTP checks with a mocked database connection. |
| [`.gitignore`](.gitignore) | Excludes credentials, environments, caches, and private editor settings. |
| [`.vscode/settings.json`](.vscode/settings.json) | Workspace interpreter and `.env.local` selection. |
| [`.vscode/extensions.json`](.vscode/extensions.json) | Python and Pyrefly extension recommendations. |
| [`README.md`](README.md) | Architecture, commands, deployment, and source explanation. |

`pyproject.toml` and `uv.lock` replace `requirements.txt`; `render.yaml` replaces
`railway.toml`. Local credentials, environments, and private editor settings
are not part of the published source. The obsolete notebook and standalone
Pyrefly configuration have been removed.

## Run locally with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
these commands from the repository root in PowerShell:

```powershell
uv sync --locked
Copy-Item .env.example .env.local
```

Only copy the example when `.env.local` does not already contain your working
configuration. Edit `.env.local` privately with the pooled and direct URLs for the
project's production database:

```dotenv
DATABASE_URL="postgres://USER:PASSWORD@pooled.db.prisma.io:5432/postgres?sslmode=require"
DIRECT_URL="postgres://USER:PASSWORD@db.prisma.io:5432/postgres?sslmode=require"
```

These are placeholders. Obtain real credentials from Prisma Console. Keep
`sslmode=require` and keep `.env.local` out of Git. Exported environment variables
take precedence over `.env.local`. On Render, the service uses its configured
environment variable instead of a local file.

After database setup, start the API:

```powershell
uv run --locked uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the API with Swagger UI. OpenAPI JSON
is at `/openapi.json`, and ReDoc is at `/redoc`.

uv manages the environment, so activation and manual pip installation are
unnecessary. If an old `.venv` references a removed Python installation,
rename it and run `uv sync --locked` again. If the default uv cache is
inaccessible, add `--cache-dir .uv-cache` immediately after `uv`.

### VS Code interpreter and import diagnostics

The shared workspace settings select `.venv` as the default interpreter and
`.env.local` as the environment file. I keep Pyrefly configuration in
`pyproject.toml`, where its interpreter discovery command asks uv for this
project's environment. This prevents dependency resolution from relying on a
global Python installation.

After `uv sync --locked`, use **Python: Select Interpreter** and select
`.venv\Scripts\python.exe` if VS Code has remembered an earlier interpreter.
Run **Pyrefly: Restart Server** or **Developer: Reload Window** once if stale
import diagnostics remain. The configuration resolves installed dependencies;
it does not hide missing-import errors.

## Set up the production database

1. Create or select this project's single production database in
   [Prisma Console](https://console.prisma.io/). Use Singapore to match Render.
2. Generate a connection credential and put its pooled and direct PostgreSQL
   URLs in `.env.local`. Both must identify the same production database.
3. Initialize it explicitly:

   ```powershell
   uv run --locked python setup_database.py
   ```

The command runs `schema.sql` inside a transaction. It creates `public.records`
with an integer primary key and three required text columns: `name`, `value`,
and `status`. It inserts three sample rows using `ON CONFLICT (id) DO NOTHING`.
Running it again preserves existing rows with those IDs. It does not alter an
existing incompatible table; schema errors require inspection.

Setup is the only application-provided database write command. I run it
manually against production, not during builds, API startup, or each deploy.
Render only needs `DATABASE_URL`; I keep `DIRECT_URL` for setup.

## Fetch data from the API

| Method and path | Result |
| --- | --- |
| `GET /` or `GET /records` | Up to 100 records ordered by `id`. |
| `GET /records?limit=2&offset=0` | Two records, starting at the first row. |
| `GET /health` | `{"status":"ok"}` when the API process is serving requests. |

Fetch records using PowerShell or curl:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/records?limit=2&offset=0'
```

```sh
curl "http://127.0.0.1:8000/records?limit=2&offset=0"
```

For the initial sample rows, the response is:

```json
[
  {"id": 1, "name": "Example record A", "value": "FastAPI", "status": "active"},
  {"id": 2, "name": "Example record B", "value": "Prisma Postgres", "status": "active"}
]
```

Replace localhost with the service's `https://...onrender.com` origin to fetch
deployed data. This public demo endpoint requires no credentials. Database
credentials stay on the backend.

`limit` accepts integers from 1 to 100; `offset` accepts nonnegative integers.
Invalid parameters produce HTTP 422. A page with no rows returns `[]`.
Database connection or query failures produce HTTP 503 with
`{"detail":"Records are temporarily unavailable."}`. `/health` checks the
process only; successful `/records` requests verify the database integration.

## Deploy to Render

The intended deployment is one free Python web service in Singapore, built
from this repository's `main` branch. Prisma hosts the database separately;
the Render configuration does not provision another database.

The service is linked directly to
[`asteroidcrib729/demo-api`](https://github.com/asteroidcrib729/demo-api).
`render.yaml` is the reference configuration for recreating it; this existing
service is managed through Render's service settings, not a Blueprint sync.

| Setting | Value |
| --- | --- |
| Service name | `demo-fastapi` |
| Runtime | Exactly Python 3.14.7, pinned in `.python-version` and `PYTHON_VERSION` |
| Region / plan | Singapore / free |
| Branch | `main` |
| Build | `uv sync --locked --no-dev` |
| Start | `uv run --locked --no-dev --no-sync uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Platform health check | Render's default TCP check; `/health` is available over HTTP. |
| uv version | `0.12.9`, configured as `UV_VERSION` |
| Secret | `DATABASE_URL`, containing the pooled production URL |

Commit and push the source and lockfile before deployment. For a fresh
deployment, create the web service with these settings or import `render.yaml`
as a Blueprint. Blueprint creation prompts for `DATABASE_URL` because it is
marked `sync: false`.

Use one deployment method for the existing service; creating another service
is unnecessary. A directly created service does not automatically read later
`render.yaml` edits: update its Dashboard settings to match. For a
Blueprint-managed service, synchronize the Blueprint instead. Secrets stay
in Render, outside version control.

Leave service previews disabled. The Blueprint also explicitly sets
`previews.generation: off`. Keep only the one Prisma production database.

Render uses its default TCP health check. I also expose `/health` for manual
HTTP checks. An optional HTTP health-check path can be set to `/health` in the
Dashboard; it is not required to fetch records from the API.

After deployment reports `live`, fetch `/health`, `/records`, and `/docs`.
Check the deployed commit and compare the record response with the production
table. A successful build or `/health` response alone does not prove database
connectivity. Free services can sleep while idle, so the first request can
take longer; see [Render's free-service behavior](https://render.com/docs/free).

## Source code walkthrough

### `main.py`: configuration and model

`load_dotenv(Path(__file__).with_name(".env.local"))` loads the configuration
beside the source file without replacing exported variables, even if the
process starts in a different working directory.
`DATABASE_URL` is required at import time, so missing configuration stops startup
with a clear message. Creating the app does not open a database connection.

`Record` is a Pydantic model describing the JSON contract: `id` is an integer;
`name`, `value`, and `status` are strings. The table's `NOT NULL` constraints
match those requirements. FastAPI validates and serializes rows using
`response_model=list[Record]` and publishes that model in OpenAPI.

### `main.py`: request handling and SQL

`health()` returns process health. Both `/` and `/records` use the same
`get_records()` function; the root alias keeps the address short. The function
uses regular `def` because
Psycopg is synchronous. FastAPI runs this handler in its thread pool, keeping
blocking database work out of the event loop.

For each request, the handler connects through Prisma's pooler with a five-second
connection timeout. `dict_row` produces mappings matching `Record`.
`prepare_threshold=None` avoids automatic prepared statements for compatibility
with transaction pooling.

The connection uses a read-only transaction and a five-second statement timeout.
The query selects exactly the four response columns, orders by `id`, and binds
pagination values as separate SQL parameters:

```sql
SELECT id, name, value, status FROM public.records
ORDER BY id LIMIT %s OFFSET %s
```

The context closes the connection on success or failure. Psycopg errors become
a generic HTTP 503. Logs record the error class without copying database
diagnostics or credentials into the HTTP response.

### `setup_database.py` and `schema.sql`

The setup script loads environment settings, requires `DIRECT_URL`, reads the
adjacent SQL file, and executes it using a connection context. Success commits
the transaction; an error rolls it back. The `if __name__ == "__main__"` guard
prevents database initialization when the file is imported.

I keep SQL separate so the table definition and sample data can also be read
or run in Prisma's SQL editor. Future schema changes should use explicit,
reviewed SQL rather than destructive resets.

### Dependency and deployment files

`pyproject.toml` declares runtime dependencies and a development group for HTTP
testing and linting. `uv.lock` records exact versions across supported platforms.
`uv sync --locked` fails if the project and lockfile disagree. Production
installation omits development tools, and `--no-sync` prevents package changes
when the service starts.

`.python-version` pins Python to exactly 3.14.7, matching `requires-python` and
Render's `PYTHON_VERSION`. `.env.example` documents
configuration without publishing credentials. `.gitignore` protects local
secrets and generated files. `render.yaml` describes hosting settings, not
the Prisma database schema or credentials.

## Verification

```powershell
uv run --locked python -m unittest discover -s tests -v
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Tests cover process health, record serialization, pagination validation, empty
results, safe database errors, connection cleanup, and rejected write methods.
They mock the connection and never access production. Fetching `/records` from
Render is the separate end-to-end deployment check.

On October 24, 2026, I verified the initial Render deployment against the
production database: `/records` returned all three sample rows; pagination and
empty pages worked; an invalid limit returned 422; and `/health`, `/docs`, and
`/openapi.json` returned 200. The initial seven automated tests, Ruff checks, formatting,
dependency compatibility check, and Render public JSON Schema validation passed.
This records that verification, rather than guaranteeing future service uptime.

## Troubleshooting

| Symptom | What I check |
| --- | --- |
| Startup says `Set DATABASE_URL` | Populate `.env.local` or the Render environment variable. |
| `/records` returns 503 | Check database availability, PostgreSQL URL, TLS, and table initialization. |
| Setup says `Set DIRECT_URL` | Supply the direct URL for the same production database. |
| Setup fails on an existing table | Compare its columns with `schema.sql`; setup does not reset tables. |
| A page returns `[]` | Check whether the table is empty or the offset exceeds its rows. |
| Render rejects the lockfile | Run `uv lock` after dependency changes and commit both dependency files. |
| Render cannot bind the port | Use `0.0.0.0` and `$PORT`, as configured above. |
| The first request takes longer | Allow time for a free service to wake from idle sleep. |

References: [uv with FastAPI](https://docs.astral.sh/uv/guides/integration/fastapi/),
[Psycopg](https://www.psycopg.org/psycopg3/docs/basic/usage.html), and
[Render Blueprints](https://render.com/docs/blueprint-spec).
