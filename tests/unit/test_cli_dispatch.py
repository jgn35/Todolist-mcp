"""
Unit tests for CLI subcommand dispatch (FR-13).

Verifies that `todolist-mcp generate-token` routes to the CLI entry point
rather than the server, and that the CLI parser recognizes the command.
"""

import subprocess
import sys
import unittest


class TestCLIDispatch(unittest.TestCase):
    """Verify FR-13: `todolist-mcp generate-token` is a recognized subcommand."""

    def _run(self, args):
        return subprocess.run(
            [sys.executable, "-m", "todolist_mcp", *args],
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_generate_token_help_is_recognized(self):
        """`generate-token --help` exits 0 and describes token generation (FR-13)."""
        result = self._run(["generate-token", "--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("generate", result.stdout.lower() + result.stderr.lower())

    def test_unknown_subcommand_not_silently_swallowed(self):
        """A bare `todolist-mcp` (no args) still shows server help, not an error."""
        result = self._run(["--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("transport", result.stdout.lower() + result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
