"""
Test Get Task Use Case
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from todolist_mcp.application.use_cases.get_task import GetTaskUseCase
from todolist_mcp.domain.entities import Task


class TestGetTaskUseCase(unittest.TestCase):
    """Tests for GetTaskUseCase."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_get_existing_task(self):
        """Test getting an existing task."""
        async def run_test():
            task_id = str(uuid4())
            mock_task = Task(
                title="Existing Task",
                description="Test Description",
                task_id=task_id,
            )

            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_task)

            use_case = GetTaskUseCase(mock_repo)

            result = await use_case.execute(task_id=task_id)

            self.assertEqual(result.id, task_id)
            self.assertEqual(result.title, "Existing Task")
            mock_repo.get_by_id.assert_called_once_with(task_id)

        self.loop.run_until_complete(run_test())

    def test_get_nonexistent_task(self):
        """Test getting a non-existent task raises ValueError."""
        async def run_test():
            task_id = str(uuid4())

            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)

            use_case = GetTaskUseCase(mock_repo)

            with self.assertRaises(ValueError) as context:
                await use_case.execute(task_id=task_id)

            self.assertIn("not found", str(context.exception))
            mock_repo.get_by_id.assert_called_once_with(task_id)

        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
