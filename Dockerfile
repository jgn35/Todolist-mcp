FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN uv sync --no-dev

FROM python:3.12-slim

RUN groupadd -r todolist && useradd -r -g todolist -u 1000 -m todolist

RUN mkdir -p /data && chown todolist:todolist /data

ENV TODOLIST_MCP_DB_PATH=/data/todolist.db
ENV TODOLIST_MCP_TRANSPORT=http
ENV TODOLIST_MCP_HTTP_PORT=8080

COPY --from=builder /build/.venv /opt/venv
COPY --from=builder /build/src /opt/todolist-mcp/src
COPY pyproject.toml /opt/todolist-mcp/

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/todolist-mcp/src:$PYTHONPATH"

WORKDIR /opt/todolist-mcp

USER todolist

EXPOSE 8080

VOLUME /data

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,socket; s=socket.socket(); s.settimeout(3); s.connect(('localhost', int(os.environ.get('TODOLIST_MCP_HTTP_PORT', '8080')))); s.close()" || exit 1

ENTRYPOINT ["python", "-m", "todolist_mcp"]
