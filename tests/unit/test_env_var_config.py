"""Tests for environment variable configuration (TODOLIST_MCP_DB_PATH, TODOLIST_MCP_TRANSPORT, TODOLIST_MCP_HTTP_PORT)."""

import os
import tempfile
from unittest.mock import patch

import pytest


class TestDbPathEnvVar:
    """Test that TODOLIST_MCP_DB_PATH is respected by repository and token manager."""

    @pytest.fixture
    def temp_db_path(self):
        with tempfile.TemporaryDirectory() as d:
            yield os.path.join(d, "test.db")

    @pytest.mark.asyncio
    async def test_repository_uses_env_var(self, temp_db_path):
        with patch.dict(os.environ, {"TODOLIST_MCP_DB_PATH": temp_db_path}):
            from todolist_mcp.infrastructure.sqlite_adapter.repository import (
                SQLiteTaskRepository,
            )

            repo = SQLiteTaskRepository()
            assert repo.db_path == temp_db_path
            await repo.initialize()
            assert os.path.exists(temp_db_path)

    def test_repository_env_var_empty_falls_back_to_default(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_DB_PATH": ""}):
            from todolist_mcp.infrastructure.sqlite_adapter.repository import (
                SQLiteTaskRepository,
            )

            repo = SQLiteTaskRepository()
            assert repo.db_path == os.path.expanduser("~/.todolist-mcp/todolist.db")

    def test_repository_explicit_db_path_overrides_env_var(self, temp_db_path):
        with patch.dict(os.environ, {"TODOLIST_MCP_DB_PATH": "/should/not/use.db"}):
            from todolist_mcp.infrastructure.sqlite_adapter.repository import (
                SQLiteTaskRepository,
            )

            repo = SQLiteTaskRepository(db_path=temp_db_path)
            assert repo.db_path == temp_db_path

    def test_token_manager_uses_env_var(self, temp_db_path):
        with patch.dict(os.environ, {"TODOLIST_MCP_DB_PATH": temp_db_path}):
            from todolist_mcp.infrastructure.auth_adapter.token_manager import (
                TokenManager,
            )

            tm = TokenManager()
            assert tm.db_path == temp_db_path

    def test_token_manager_env_var_empty_falls_back_to_default(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_DB_PATH": ""}):
            from todolist_mcp.infrastructure.auth_adapter.token_manager import (
                TokenManager,
            )

            tm = TokenManager()
            assert tm.db_path == os.path.expanduser("~/.todolist-mcp/todolist.db")


class TestTransportEnvVar:
    """Test that TODOLIST_MCP_TRANSPORT is respected by main() argparse."""

    def test_transport_env_var_sets_default(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_TRANSPORT": "http"}):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--transport",
                choices=["stdio", "http", "both"],
                default=os.environ.get("TODOLIST_MCP_TRANSPORT", "stdio"),
            )
            args = parser.parse_args([])
            assert args.transport == "http"

    def test_transport_env_var_overridden_by_cli(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_TRANSPORT": "http"}):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--transport",
                choices=["stdio", "http", "both"],
                default=os.environ.get("TODOLIST_MCP_TRANSPORT", "stdio"),
            )
            args = parser.parse_args(["--transport", "stdio"])
            assert args.transport == "stdio"

    def test_transport_no_env_var_defaults_to_stdio(self):
        with patch.dict(os.environ, {}, clear=True):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--transport",
                choices=["stdio", "http", "both"],
                default=os.environ.get("TODOLIST_MCP_TRANSPORT", "stdio"),
            )
            args = parser.parse_args([])
            assert args.transport == "stdio"


class TestHttpPortEnvVar:
    """Test that TODOLIST_MCP_HTTP_PORT is respected by main() argparse."""

    def test_port_env_var_sets_default(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_HTTP_PORT": "9000"}):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--port",
                type=int,
                default=int(os.environ.get("TODOLIST_MCP_HTTP_PORT", "8080")),
            )
            args = parser.parse_args([])
            assert args.port == 9000

    def test_port_env_var_overridden_by_cli(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_HTTP_PORT": "9000"}):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--port",
                type=int,
                default=int(os.environ.get("TODOLIST_MCP_HTTP_PORT", "8080")),
            )
            args = parser.parse_args(["--port", "7000"])
            assert args.port == 7000

    def test_port_no_env_var_defaults_to_8080(self):
        with patch.dict(os.environ, {}, clear=True):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--port",
                type=int,
                default=int(os.environ.get("TODOLIST_MCP_HTTP_PORT", "8080")),
            )
            args = parser.parse_args([])
            assert args.port == 8080
