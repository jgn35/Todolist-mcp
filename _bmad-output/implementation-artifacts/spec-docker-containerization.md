---
title: 'Docker Containerization for Todolist MCP'
type: 'feature'
created: '2026-09-01'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'e42f7b1'
context:
  - "{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Todolist-mcp-2026-08-31/ARCHITECTURE-SPINE.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Todolist MCP server has no containerization support. The SQLite database path is hardcoded to `~/.todolist-mcp/todolist.db`, and the transport mode has no environment-variable fallback, making it impossible to run the server in a Docker container with a volume-mounted database.

**Approach:** Add environment-variable configuration for the database path (`TODOLIST_MCP_DB_PATH`), transport mode (`TODOLIST_MCP_TRANSPORT`), and HTTP port (`TODOLIST_MCP_HTTP_PORT`). Create a multi-stage Dockerfile, docker-compose.yml, and .dockerignore following invariants AD-9 through AD-12 from the architecture spine.

## Boundaries & Constraints

**Always:**
- Follow AD-9: DB path must read `TODOLIST_MCP_DB_PATH` env var with `~/.todolist-mcp/todolist.db` as local default
- Follow AD-10: Transport mode must read `TODOLIST_MCP_TRANSPORT` env var (default `stdio` local, `http` in container)
- Follow AD-11: Docker image must be multi-stage on `python:3.12-slim`, run as non-root user `todolist`, contain only runtime deps
- Follow AD-12: SQLite DB at `/data/todolist.db` in container, backed by named volume `todolist-mcp-data`
- Preserve existing local behavior when env vars are not set (backward compatible)
- `bearer_verifier.py` already forwards `db_path` to `TokenManager` — no change needed there

**Ask First:**
- Publishing the image to a container registry
- Adding a dedicated `/health` endpoint (currently using `/mcp/tools` as implicit healthcheck)

**Never:**
- Run the container as root
- Include dev dependencies (pytest, ruff, pyright) in the runtime image
- Break existing local stdio mode when no env vars are set
- Add Kubernetes manifests (deferred per architecture)

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Container starts with defaults | No env vars set in Dockerfile | Server starts on port 8080, transport=http, DB at /data/todolist.db | N/A |
| Container with custom port | TODOLIST_MCP_HTTP_PORT=9000 | Server starts on port 9000 | N/A |
| Local run without env vars | No TODOLIST_MCP_* env vars | Server uses stdio, DB at ~/.todolist-mcp/todolist.db (backward compatible) | N/A |
| Local run with env vars | TODOLIST_MCP_DB_PATH=/tmp/test.db | Server uses /tmp/test.db for SQLite | N/A |
| Container DB volume not mounted | /data exists but no volume | Server creates DB file in /data, data lost on container removal | N/A |
| DB path env var set but directory missing | TODOLIST_MCP_DB_PATH=/nonexistent/path.db | Repository.initialize() creates parent directory | Existing behavior, no change needed |

</frozen-after-approval>

## Code Map

- `src/todolist_mcp/infrastructure/sqlite_adapter/repository.py:25-26` -- `SQLiteTaskRepository.__init__` sets `db_path` default to `~/.todolist-mcp/todolist.db`; must read `TODOLIST_MCP_DB_PATH` env var as fallback
- `src/todolist_mcp/infrastructure/auth_adapter/token_manager.py:25-26` -- `TokenManager.__init__` same pattern as repository; must read `TODOLIST_MCP_DB_PATH`
- `src/todolist_mcp/infrastructure/auth_adapter/bearer_verifier.py:16-18` -- `BearerTokenVerifier.__init__` forwards `db_path` to `TokenManager`; no change needed (picks up env var via TokenManager)
- `src/todolist_mcp/__init__.py:287-298` -- `main()` argparse defaults for `--transport` (default `stdio`) and `--port` (default `8080`); must read `TODOLIST_MCP_TRANSPORT` and `TODOLIST_MCP_HTTP_PORT` env vars as argparse defaults
- `src/todolist_mcp/__init__.py:302-304` -- `main()` creates `~/.todolist-mcp` directory; must respect `TODOLIST_MCP_DB_PATH` for parent dir creation
- `src/todolist_mcp/__init__.py:16` -- `BearerTokenVerifier()` instantiated at module level with no args; picks up env var via TokenManager change — no change needed
- `src/todolist_mcp/cli.py:94-108` -- `run_server()` rebuilds `sys.argv` and delegates to `main()`; needs no change (env vars flow through argparse defaults in main())
- `src/todolist_mcp/cli.py:73-84` -- CLI subparser defaults for `--transport` and `--port`; optional update to read env vars for consistency
- `pyproject.toml:23-25` -- `[project.scripts]` entry points: `todolist-mcp`, `todolist-mcp-generate-token`, `todolist-mcp-run`
- `Dockerfile` -- NEW: multi-stage build, python:3.12-slim, uv install, non-root user, /data volume
- `docker-compose.yml` -- NEW: service def with port 8080, named volume, env vars
- `.dockerignore` -- NEW: exclude .git, tests, _bmad-output, __pycache__, .env, .venv, etc.

## Tasks & Acceptance

**Execution:**
- [x] `src/todolist_mcp/infrastructure/sqlite_adapter/repository.py` -- Change `db_path` fallback to read `TODOLIST_MCP_DB_PATH` env var -- AD-9: DB path must be env-configurable
- [x] `src/todolist_mcp/infrastructure/auth_adapter/token_manager.py` -- Same env var change as repository.py -- AD-9: both components share the same DB path
- [x] `src/todolist_mcp/__init__.py` -- Update argparse defaults for `--transport` and `--port` to read `TODOLIST_MCP_TRANSPORT` and `TODOLIST_MCP_HTTP_PORT` env vars; update db_dir creation to respect `TODOLIST_MCP_DB_PATH` -- AD-10: container defaults to HTTP transport
- [x] `src/todolist_mcp/cli.py` -- Update CLI subparser defaults to read env vars for consistency -- Ensures `todolist-mcp run` respects env vars the same way as `main()`
- [x] `Dockerfile` -- Create multi-stage Dockerfile: builder stage with uv sync, runtime stage with python:3.12-slim, non-root user todolist, /data volume, env defaults, healthcheck -- AD-11, AD-12
- [x] `docker-compose.yml` -- Create compose file with port 8080, named volume todolist-mcp-data, env vars, restart policy -- AD-12
- [x] `.dockerignore` -- Create dockerignore excluding .git, tests, _bmad-output, __pycache__, .env, .venv, .ruff_cache, docs -- AD-11: minimal image

**Acceptance Criteria:**
- Given no TODOLIST_MCP_* env vars are set, when the server starts locally, then it uses stdio transport and ~/.todolist-mcp/todolist.db (backward compatible)
- Given TODOLIST_MCP_DB_PATH=/data/todolist.db is set, when SQLiteTaskRepository initializes, then it creates the database at /data/todolist.db
- Given TODOLIST_MCP_TRANSPORT=http is set, when main() runs, then the server starts in HTTP mode without requiring --transport CLI flag
- Given the Dockerfile is built, when `docker build -t todolist-mcp .` runs, then the image builds successfully with python:3.12-slim base
- Given the container is running, when `docker exec` checks the user, then the process runs as non-root user `todolist`
- Given docker-compose up is run, when a task is created, then the data persists in the named volume across container restarts
- Given the existing test suite, when `uv run pytest` runs, then all tests still pass (no regressions from env var changes)

## Spec Change Log

## Design Notes

**Env var fallback pattern for db_path:**
```python
self.db_path = db_path or os.environ.get(
    "TODOLIST_MCP_DB_PATH",
    os.path.expanduser("~/.todolist-mcp/todolist.db"),
)
```

**Env var fallback pattern for argparse defaults:**
```python
parser.add_argument(
    "--transport",
    choices=["stdio", "http", "both"],
    default=os.environ.get("TODOLIST_MCP_TRANSPORT", "stdio"),
    help="Transport protocol: stdio (default), http, or both",
)
parser.add_argument(
    "--port",
    type=int,
    default=int(os.environ.get("TODOLIST_MCP_HTTP_PORT", "8080")),
    help="HTTP port when using http or both transport (default: 8080)",
)
```

**Dockerfile entrypoint:** `python -m todolist_mcp` — the `__main__.py` delegates to `main()`, which reads env vars as argparse defaults. The Dockerfile sets `ENV TODOLIST_MCP_TRANSPORT=http` and `ENV TODOLIST_MCP_DB_PATH=/data/todolist.db` so the server starts correctly without CLI flags.

**Healthcheck:** Uses `python -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('localhost',8080)); s.close()"` — a lightweight socket-level check that the HTTP server is listening. A full HTTP request would hit the 401 auth gate, so socket connect is the simplest reliable signal.

## Verification

**Commands:**
- `uv run pytest` -- expected: All existing tests pass (no regressions)
- `uv run ruff check .` -- expected: No lint errors
- `docker build -t todolist-mcp .` -- expected: Image builds successfully
- `docker compose up -d` then `docker compose down` then `docker compose up -d` -- expected: Data persists across restarts
- `docker run --rm todolist-mcp python -c "import os; print(os.getuid())"` -- expected: 1000 (non-root)

**Manual checks:**
- Verify no dev dependencies (pytest, ruff, pyright) in the runtime image layers
- Verify /data directory is owned by todolist user in the container

## Suggested Review Order

**Environment Variable Configuration (AD-9, AD-10)**

- Entry point: argparse defaults now read env vars for transport and port
  [`__init__.py:290`](../../src/todolist_mcp/__init__.py#L290)

- db_dir creation respects TODOLIST_MCP_DB_PATH for volume-mounted paths
  [`__init__.py:303`](../../src/todolist_mcp/__init__.py#L303)

- Repository db_path uses `or` chain: explicit arg > env var > default
  [`repository.py:26`](../../src/todolist_mcp/infrastructure/sqlite_adapter/repository.py#L26)

- TokenManager mirrors the same `or` chain for shared DB consistency
  [`token_manager.py:26`](../../src/todolist_mcp/infrastructure/auth_adapter/token_manager.py#L26)

- CLI subparser defaults and run_server comparison logic updated for consistency
  [`cli.py:76`](../../src/todolist_mcp/cli.py#L76)

**Docker Infrastructure (AD-11, AD-12)**

- Multi-stage Dockerfile: uv builder, non-root runtime, /data volume, env defaults
  [`Dockerfile:1`](../../Dockerfile#L1)

- Compose service with named volume, port mapping, restart policy
  [`docker-compose.yml:1`](../../docker-compose.yml#L1)

- Build context excludes non-runtime files for minimal image
  [`.dockerignore:1`](../../.dockerignore#L1)

**Tests**

- 11 new tests covering env var fallback, empty-string handling, and CLI override
  [`test_env_var_config.py:1`](../../tests/unit/test_env_var_config.py#L1)
