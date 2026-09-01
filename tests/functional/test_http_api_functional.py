"""
Functional Tests for MCP HTTP Transport with Bearer Auth

Tests that the FastMCP server enforces Bearer token authentication on its
native HTTP (streamable-http) transport. Starts the server on a real port
and uses requests to verify auth behaviour end-to-end.
"""

import hashlib
import os
import socket
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta

import requests
import uvicorn
from fastmcp import FastMCP
from sqlalchemy import create_engine, delete, insert
from sqlalchemy.orm import sessionmaker

from todolist_mcp.infrastructure.auth_adapter.bearer_verifier import BearerTokenVerifier
from todolist_mcp.infrastructure.auth_adapter.models import AuthTokenModel, Base


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _build_test_server(db_path: str, token: str) -> FastMCP:
    """Build a FastMCP server wired to a temp DB and a verifier that accepts ``token``."""
    verifier = BearerTokenVerifier(db_path=db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        session.execute(delete(AuthTokenModel))
        session.execute(insert(AuthTokenModel).values(
            token=hashlib.sha256(token.encode()).hexdigest(),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
        ))
        session.commit()

    mcp = FastMCP(name="todolist-mcp-test", version="0.1.0", auth=verifier)

    @mcp.tool()
    async def ping() -> dict:
        return {"pong": True}

    return mcp


class TestMCPHttpAuthFunctional(unittest.TestCase):
    """Functional tests for bearer auth on the FastMCP HTTP transport."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.token = "functional_test_token_abc123"
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}/mcp"

        self.mcp = _build_test_server(self.db_path, self.token)
        app = self.mcp.http_app()

        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        for _ in range(50):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("127.0.0.1", self.port))
                    break
            except ConnectionRefusedError:
                time.sleep(0.1)

    def tearDown(self):
        self.server.should_exit = True
        self.thread.join(timeout=5)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def _init_request(self, headers: dict | None = None):
        return requests.post(
            self.url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            },
            headers={**(headers or {}), "Accept": "application/json, text/event-stream"},
            timeout=10,
        )

    def test_initialize_with_valid_bearer_token(self):
        """The MCP initialize handshake succeeds with a valid bearer token."""
        resp = self._init_request({"Authorization": f"Bearer {self.token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("protocolVersion", resp.text)

    def test_initialize_without_token_rejected(self):
        """Requests without a bearer token are rejected with 401."""
        resp = self._init_request()
        self.assertEqual(resp.status_code, 401)

    def test_initialize_with_invalid_token_rejected(self):
        """Requests with an invalid bearer token are rejected with 401."""
        resp = self._init_request({"Authorization": "Bearer wrong_token"})
        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
    unittest.main()
