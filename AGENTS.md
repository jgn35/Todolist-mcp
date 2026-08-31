<!-- bmad:context -->
<!-- Verified 2026-08-31 against 9465fef. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## Todolist-mcp

Python MCP server project. Follows standard Python practices: type hints, modern tooling (uv/ruff), and clean separation of concerns.

## Policy

- No direct pushes to main; PRs only, 1 approval required.
- Never commit secrets or .env files.

## Where things are

- MCP server entry: `src/todolist_mcp/__init__.py`
- Tests: `tests/`
- Config: `pyproject.toml`
- Planning and docs: `docs/`
- BMad artifacts: `_bmad-output/`

## Running and verifying

- Install: `uv sync`
- Run server: `uv run python -m todolist_mcp`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Type check: `uv run pyright`

## Conventions that differ from defaults

- All MCP tools must be async and registered with proper schemas.
- Use absolute imports within the package.

## Known pitfalls

- Always validate MCP tool inputs against the protocol spec.

<!-- /bmad:context -->
