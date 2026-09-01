"""
Unit tests for the CLI module (todolist_mcp.cli) — FR-13.

Covers generate_token() (with TokenManager and input() monkeypatched so no
real DB or interactive prompt is touched) and main() subcommand dispatch.
"""

import asyncio
import io
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCLIGenerateToken(unittest.TestCase):
    """Cover generate_token() paths (FR-13)."""

    def _run_async(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_generate_token_no_existing(self):
        """When no token exists, a new token is generated and printed."""
        from todolist_mcp import cli

        fake_tm = MagicMock()
        fake_tm.get_token = AsyncMock(return_value=None)
        fake_tm.generate_token = MagicMock(return_value="new-token-123")

        with (
            patch("todolist_mcp.cli.TokenManager", return_value=fake_tm),
            patch("builtins.input", return_value="n"),
            patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            cli.generate_token()

        self.assertIn("new-token-123", out.getvalue())
        fake_tm.generate_token.assert_called_once()

    def test_generate_token_existing_cancel(self):
        """When a token already exists and user declines, generation is cancelled."""
        from todolist_mcp import cli

        fake_tm = MagicMock()
        fake_tm.get_token = AsyncMock(return_value="existing-token")

        with (
            patch("todolist_mcp.cli.TokenManager", return_value=fake_tm),
            patch("builtins.input", return_value="n"),
            patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            cli.generate_token()

        self.assertIn("cancelled", out.getvalue().lower())
        fake_tm.generate_token.assert_not_called()


class TestCLIMainDispatch(unittest.TestCase):
    """Cover cli.main() argument dispatch."""

    def test_main_no_command_prints_help(self):
        """`cli.main()` with no subcommand prints help and does not run a server."""
        from todolist_mcp import cli

        with (
            patch("sys.argv", ["todolist-mcp"]),
            patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            cli.main()
        self.assertIn("generate-token", out.getvalue())

    def test_main_generate_token_dispatches(self):
        """`cli.main(['generate-token'])` calls generate_token."""
        from todolist_mcp import cli

        with (
            patch("sys.argv", ["todolist-mcp", "generate-token"]),
            patch.object(cli, "generate_token") as gen,
        ):
            cli.main()
        gen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
