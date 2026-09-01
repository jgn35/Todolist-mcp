"""
Test List Tasks Use Case
"""

import asyncio
import unittest
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

from todolist_mcp.application.use_cases.list_tasks import ListTasksUseCase
from todolist_mcp.domain.entities import Priority, Task, TaskStatus


@dataclass
class MockListTasksResult:
    tasks: list
    total: int
    limit: int
    offset: int


class TestListTasksUseCase(unittest.TestCase):
    """Tests for ListTasksUseCase."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_list_all_tasks(self):
        """Test listing all tasks."""
        async def run_test():
            task1 = Task(title="Task 1", priority=Priority.HIGH)
            task2 = Task(title="Task 2", priority=Priority.LOW)

            mock_repo = MagicMock()
            mock_repo.list_all = AsyncMock(return_value=([task1, task2], 2))

            use_case = ListTasksUseCase(mock_repo)

            result = await use_case.execute()

            self.assertEqual(len(result.tasks), 2)
            self.assertEqual(result.total, 2)
            self.assertIsNone(result.limit)
            self.assertIsNone(result.offset)

        self.loop.run_until_complete(run_test())

    def test_list_tasks_with_status_filter(self):
        """Test listing tasks with status filter."""
        async def run_test():
            task1 = Task(title="Task 1", status=TaskStatus.COMPLETED)

            mock_repo = MagicMock()
            mock_repo.list_all = AsyncMock(return_value=([task1], 1))

            use_case = ListTasksUseCase(mock_repo)

            result = await use_case.execute(status="completed")

            self.assertEqual(len(result.tasks), 1)
            self.assertEqual(result.tasks[0].status, TaskStatus.COMPLETED)
            mock_repo.list_all.assert_called_once()
            call_args = mock_repo.list_all.call_args
            self.assertEqual(call_args[1]['status'], "completed")

        self.loop.run_until_complete(run_test())

    def test_list_tasks_with_priority_filter(self):
        """Test listing tasks with priority filter."""
        async def run_test():
            task1 = Task(title="Task 1", priority=Priority.HIGH)

            mock_repo = MagicMock()
            mock_repo.list_all = AsyncMock(return_value=([task1], 1))

            use_case = ListTasksUseCase(mock_repo)

            result = await use_case.execute(priority="high")

            self.assertEqual(len(result.tasks), 1)
            self.assertEqual(result.tasks[0].priority, Priority.HIGH)

        self.loop.run_until_complete(run_test())

    def test_list_tasks_with_pagination(self):
        """Test listing tasks with pagination."""
        async def run_test():
            task1 = Task(title="Task 1")
            task2 = Task(title="Task 2")

            mock_repo = MagicMock()
            mock_repo.list_all = AsyncMock(return_value=([task1, task2], 2))

            use_case = ListTasksUseCase(mock_repo)

            result = await use_case.execute(limit=10, offset=0)

            self.assertEqual(result.limit, 10)
            self.assertEqual(result.offset, 0)
            mock_repo.list_all.assert_called_once()
            call_args = mock_repo.list_all.call_args
            self.assertEqual(call_args[1]['limit'], 10)
            self.assertEqual(call_args[1]['offset'], 0)

        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
