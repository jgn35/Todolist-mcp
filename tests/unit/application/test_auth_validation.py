"""
Test Bearer Token Verifier

Tests the BearerTokenVerifier that bridges TokenManager to FastMCP's auth
provider system. Auth is now handled at the HTTP transport level, not per-tool.
"""

import asyncio
import os
import tempfile
import unittest

from todolist_mcp.infrastructure.auth_adapter.bearer_verifier import BearerTokenVerifier
from todolist_mcp.infrastructure.auth_adapter.token_manager import TokenManager


class TestBearerTokenVerifier(unittest.TestCase):
    """Tests for the BearerTokenVerifier auth provider."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_auth.db")

        self.token_manager = TokenManager(db_path=self.db_path)
        self.valid_token = self.token_manager.generate_token()
        self.verifier = BearerTokenVerifier(db_path=self.db_path)

    def tearDown(self):
        self.loop.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_valid_token_returns_access_token(self):
        """A valid token returns an AccessToken."""
        async def run_test():
            result = await self.verifier.verify_token(self.valid_token)
            self.assertIsNotNone(result)
            if result is not None:
                self.assertEqual(result.token, self.valid_token)

        self.loop.run_until_complete(run_test())

    def test_invalid_token_returns_none(self):
        """An invalid token returns None."""
        async def run_test():
            result = await self.verifier.verify_token("invalid_token_12345")
            self.assertIsNone(result)

        self.loop.run_until_complete(run_test())

    def test_empty_token_returns_none(self):
        """An empty string token returns None."""
        async def run_test():
            result = await self.verifier.verify_token("")
            self.assertIsNone(result)

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
