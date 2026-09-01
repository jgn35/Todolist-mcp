"""
Test Delete Task Use Case
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from todolist_mcp.application.use_cases.delete_task import DeleteTaskUseCase
from todolist_mcp.domain.entities import Task


class TestDeleteTaskUseCase(unittest.TestCase):
    """Tests for DeleteTaskUseCase."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_delete_existing_task(self):
        """Test deleting an existing task."""
        async def run_test():
            task_id = str(uuid4())
            existing_task = Task(title="Task to delete", task_id=task_id)

            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=existing_task)
            mock_repo.delete = AsyncMock(return_value=True)

            use_case = DeleteTaskUseCase(mock_repo)

            await use_case.execute(task_id=task_id)

            mock_repo.delete.assert_called_once_with(task_id)

        self.loop.run_until_complete(run_test())

    def test_delete_nonexistent_task(self):
        """Test deleting a non-existent task raises ValueError."""
        async def run_test():
            task_id = str(uuid4())

            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)

            use_case = DeleteTaskUseCase(mock_repo)

            with self.assertRaises(ValueError) as context:
                await use_case.execute(task_id=task_id)

            self.assertIn("not found", str(context.exception))

        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
