"""
Test Create Task Use Case
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from todolist_mcp.application.use_cases.create_task import CreateTaskUseCase
from todolist_mcp.domain.entities import Priority, Task, TaskStatus


class TestCreateTaskUseCase(unittest.TestCase):
    """Tests for CreateTaskUseCase."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_create_task_with_all_parameters(self):
        """Test creating a task with all parameters."""
        async def run_test():
            # Create mock repository
            mock_repo = MagicMock()
            mock_task = Task(
                title="Test Task",
                description="Test Description",
                due_date="2026-12-31 23:59:59",
                priority=Priority.HIGH,
                status=TaskStatus.PENDING,
            )
            mock_repo.create = AsyncMock(return_value=mock_task)

            # Create use case
            use_case = CreateTaskUseCase(mock_repo)

            # Execute
            result = await use_case.execute(
                title="Test Task",
                description="Test Description",
                due_date="2026-12-31 23:59:59",
                priority="high",
            )

            # Verify
            self.assertEqual(result.title, "Test Task")
            self.assertEqual(result.description, "Test Description")
            self.assertEqual(result.due_date, "2026-12-31 23:59:59")
            self.assertEqual(result.priority, Priority.HIGH)
            self.assertEqual(result.status, TaskStatus.PENDING)
            mock_repo.create.assert_called_once()

        self.loop.run_until_complete(run_test())

    def test_create_task_with_minimal_parameters(self):
        """Test creating a task with only required parameters."""
        async def run_test():
            mock_repo = MagicMock()
            mock_task = Task(
                title="Minimal Task",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING,
            )
            mock_repo.create = AsyncMock(return_value=mock_task)

            use_case = CreateTaskUseCase(mock_repo)

            result = await use_case.execute(title="Minimal Task")

            self.assertEqual(result.title, "Minimal Task")
            self.assertIsNone(result.description)
            self.assertIsNone(result.due_date)
            self.assertEqual(result.priority, Priority.MEDIUM)
            mock_repo.create.assert_called_once()

        self.loop.run_until_complete(run_test())

    def test_create_task_with_medium_priority(self):
        """Test creating a task with medium priority (default)."""
        async def run_test():
            mock_repo = MagicMock()
            mock_task = Task(
                title="Medium Priority Task",
                priority=Priority.MEDIUM,
            )
            mock_repo.create = AsyncMock(return_value=mock_task)

            use_case = CreateTaskUseCase(mock_repo)

            result = await use_case.execute(
                title="Medium Priority Task",
                priority="medium",
            )

            self.assertEqual(result.priority, Priority.MEDIUM)

        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
