"""
Unit tests for the MCP tool wrappers in todolist_mcp.__init__.

The @mcp.tool()-decorated functions remain directly callable, so we
exercise them with an in-memory fake repository (no real DB, no FastMCP
server) to cover the wrapper logic: argument validation, date parsing,
error mapping, and dict serialization.
"""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from todolist_mcp.domain.entities import Priority, Task, TaskStatus


class _BaseToolTest(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # Fresh fake repository per test.
        self.repo = MagicMock()
        self._patch = None

    def tearDown(self):
        if self._patch is not None:
            self._patch.stop()
        self.loop.close()

    def _patch_repository(self, repo=None):
        """Redirect get_repository() to return our fake repo."""
        from unittest.mock import patch

        self.repo = repo or self.repo
        self._patch = patch(
            "todolist_mcp.get_repository",
            new=AsyncMock(return_value=self.repo),
        )
        self._patch.start()


class TestCreateTaskTool(_BaseToolTest):
    def test_create_task_returns_task_dict(self):
        async def run():
            from todolist_mcp import create_task

            created = Task(title="T", priority=Priority.MEDIUM)
            self.repo.create = AsyncMock(return_value=created)
            self._patch_repository()

            result = await create_task(title="T", description="d", priority="high")
            self.assertEqual(result["title"], "T")
            self.repo.create.assert_awaited_once()

        self.loop.run_until_complete(run())

    def test_create_task_empty_title_raises(self):
        async def run():
            from todolist_mcp import create_task

            self._patch_repository()
            with self.assertRaises(ValueError):
                await create_task(title="")

        self.loop.run_until_complete(run())


class TestGetTaskTool(_BaseToolTest):
    def test_get_task_found(self):
        async def run():
            from todolist_mcp import get_task

            task = Task(title="T")
            self.repo.get_by_id = AsyncMock(return_value=task)
            self._patch_repository()

            result = await get_task(task_id=str(task.id))
            self.assertEqual(result["title"], "T")

        self.loop.run_until_complete(run())

    def test_get_task_not_found_raises(self):
        async def run():
            from todolist_mcp import get_task

            self.repo.get_by_id = AsyncMock(return_value=None)
            self._patch_repository()

            with self.assertRaises(ValueError):
                await get_task(task_id="missing-id")

        self.loop.run_until_complete(run())


class TestListTasksTool(_BaseToolTest):
    def test_list_tasks_today_filter(self):
        async def run():
            from todolist_mcp import list_tasks

            task = Task(title="T")
            self.repo.list_all = AsyncMock(return_value=([task], 1))
            self._patch_repository()

            result = await list_tasks(due_date="today")
            self.assertEqual(result["total"], 1)
            call = self.repo.list_all.call_args
            today = datetime.now().strftime("%Y-%m-%d")
            self.assertEqual(call.kwargs["due_date"], today)

        self.loop.run_until_complete(run())

    def test_list_tasks_tomorrow_filter(self):
        async def run():
            from todolist_mcp import list_tasks

            self.repo.list_all = AsyncMock(return_value=([], 0))
            self._patch_repository()

            await list_tasks(due_date="tomorrow")
            call = self.repo.list_all.call_args
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            self.assertEqual(call.kwargs["due_date"], tomorrow)

        self.loop.run_until_complete(run())

    def test_list_tasks_range_and_overdue_passthrough(self):
        async def run():
            from todolist_mcp import list_tasks

            self.repo.list_all = AsyncMock(return_value=([], 0))
            self._patch_repository()

            await list_tasks(due_date="2026-01-01..2026-01-31")
            self.assertEqual(
                self.repo.list_all.call_args.kwargs["due_date"],
                "2026-01-01..2026-01-31",
            )

            await list_tasks(due_date="overdue")
            self.assertEqual(self.repo.list_all.call_args.kwargs["due_date"], "overdue")

        self.loop.run_until_complete(run())

    def test_list_tasks_pagination_defaults(self):
        async def run():
            from todolist_mcp import list_tasks

            self.repo.list_all = AsyncMock(return_value=([], 0))
            self._patch_repository()

            await list_tasks()
            call = self.repo.list_all.call_args
            self.assertEqual(call.kwargs["limit"], 50)
            self.assertEqual(call.kwargs["offset"], 0)

        self.loop.run_until_complete(run())


class TestUpdateTaskTool(_BaseToolTest):
    def test_update_task_success(self):
        async def run():
            from todolist_mcp import update_task

            existing = Task(title="Old")
            self.repo.get_by_id = AsyncMock(return_value=existing)
            self.repo.update = AsyncMock(return_value=existing)
            self._patch_repository()

            result = await update_task(task_id=str(existing.id), title="New")
            self.assertEqual(result["title"], "New")

        self.loop.run_until_complete(run())

    def test_update_task_not_found_raises(self):
        async def run():
            from todolist_mcp import update_task

            self.repo.get_by_id = AsyncMock(return_value=None)
            self._patch_repository()

            with self.assertRaises(ValueError):
                await update_task(task_id="missing", title="New")

        self.loop.run_until_complete(run())


class TestDeleteTaskTool(_BaseToolTest):
    def test_delete_task_success(self):
        async def run():
            from todolist_mcp import delete_task

            task = Task(title="T")
            self.repo.get_by_id = AsyncMock(return_value=task)
            self.repo.delete = AsyncMock(return_value=True)
            self._patch_repository()

            result = await delete_task(task_id="some-id")
            self.assertIn("deleted", result["message"])

        self.loop.run_until_complete(run())

    def test_delete_task_not_found_raises(self):
        async def run():
            from todolist_mcp import delete_task

            self.repo.get_by_id = AsyncMock(return_value=None)
            self._patch_repository()

            with self.assertRaises(ValueError):
                await delete_task(task_id="missing")

        self.loop.run_until_complete(run())


class TestCompleteTaskTool(_BaseToolTest):
    def test_complete_task_success(self):
        async def run():
            from todolist_mcp import complete_task

            task = Task(title="T", status=TaskStatus.PENDING)
            self.repo.get_by_id = AsyncMock(return_value=task)
            self.repo.update = AsyncMock(return_value=task)
            self._patch_repository()

            result = await complete_task(task_id=str(task.id))
            self.assertEqual(result["status"], "completed")

        self.loop.run_until_complete(run())

    def test_complete_task_already_completed_raises(self):
        async def run():
            from todolist_mcp import complete_task

            task = Task(title="T", status=TaskStatus.COMPLETED)
            self.repo.get_by_id = AsyncMock(return_value=task)
            self._patch_repository()

            with self.assertRaises(ValueError):
                await complete_task(task_id=str(task.id))

        self.loop.run_until_complete(run())


if __name__ == "__main__":
    unittest.main()
