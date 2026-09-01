- source_spec: `spec-docker-containerization.md`
  summary: Pin Python base image version and add OCI labels to Dockerfile
  evidence: Blind hunter review: python:3.12-slim floats to latest patch, no version/maintainer labels. Nice-to-have for reproducibility and traceability, not a functional bug.
- source_spec: `spec-docker-containerization.md`
  summary: Add .env.example or documentation for the three new environment variables
  evidence: Blind hunter review: users have no reference for TODOLIST_MCP_DB_PATH, TODOLIST_MCP_TRANSPORT, TODOLIST_MCP_HTTP_PORT configuration options.
- source_spec: `spec-docker-containerization.md`
  summary: Add logging driver with size limits to docker-compose.yml
  evidence: Blind hunter review: long-running MCP servers can accumulate unbounded logs without a logging driver.
- source_spec: `spec-docker-containerization.md`
  summary: Healthcheck should handle stdio transport override in container
  evidence: Edge case hunter: if TODOLIST_MCP_TRANSPORT is overridden to stdio at runtime, no HTTP port is bound and the healthcheck fails indefinitely.
