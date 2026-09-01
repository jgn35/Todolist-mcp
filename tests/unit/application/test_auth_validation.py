"""
Test Authentication Validation for MCP Tools
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from todolist_mcp import complete_task, create_task, delete_task, get_task, list_tasks, update_task


class TestAuthValidation(unittest.TestCase):
    """Tests for authentication validation across all MCP tools."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # Mock the validate_auth function to return False (no token or invalid)
        self.patcher = patch('todolist_mcp.validate_auth', new_callable=AsyncMock)
        self.mock_validate = self.patcher.start()

    def tearDown(self):
        self.loop.close()
        self.patcher.stop()

    def test_create_task_missing_token(self):
        """Test create_task with missing token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await create_task(title="Test Task", token=None)

            self.assertIn("Unauthorized", str(context.exception))
            self.assertIn("Invalid or missing", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_create_task_invalid_token(self):
        """Test create_task with invalid token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await create_task(title="Test Task", token="invalid_token")

            self.assertIn("Unauthorized", str(context.exception))
            self.assertIn("Invalid or missing", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_get_task_missing_token(self):
        """Test get_task with missing token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await get_task(task_id="12345678-1234-1234-1234-123456789abc", token=None)

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_get_task_invalid_token(self):
        """Test get_task with invalid token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await get_task(task_id="12345678-1234-1234-1234-123456789abc", token="invalid_token")

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_list_tasks_missing_token(self):
        """Test list_tasks with missing token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await list_tasks(token=None)

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_list_tasks_invalid_token(self):
        """Test list_tasks with invalid token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await list_tasks(token="invalid_token")

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_update_task_missing_token(self):
        """Test update_task with missing token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await update_task(task_id="12345678-1234-1234-1234-123456789abc", token=None)

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_delete_task_missing_token(self):
        """Test delete_task with missing token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await delete_task(task_id="12345678-1234-1234-1234-123456789abc", token=None)

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())

    def test_complete_task_missing_token(self):
        """Test complete_task with missing token raises Unauthorized error."""
        async def run_test():
            self.mock_validate.return_value = False

            with self.assertRaises(ValueError) as context:
                await complete_task(task_id="12345678-1234-1234-1234-123456789abc", token=None)

            self.assertIn("Unauthorized", str(context.exception))

        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
