"""
Integration tests for repository sorting (FR-3) and date filters (FR-10).

These exercise the real SQLiteTaskRepository to verify the sort order
(due_date ASC, then priority DESC) and the date filter keywords
(today, tomorrow, overdue, range) that the unit tests mock out.
"""

import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timedelta

from todolist_mcp.domain.entities import Priority, Task, TaskStatus
from todolist_mcp.infrastructure.sqlite_adapter.repository import SQLiteTaskRepository


class TestRepositorySortingAndDateFilters(unittest.TestCase):
    """Verify FR-3 sorting and FR-10 date filtering against the SQLite repository."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

        async def init_repo():
            self.repo = SQLiteTaskRepository(db_path=self.db_path)
            await self.repo.initialize()

        self.loop.run_until_complete(init_repo())

    def tearDown(self):
        self.loop.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    # --- FR-3: sorting ---------------------------------------------------

    def test_sort_due_date_asc_then_priority_desc(self):
        """Tasks sort by due_date ASC, then priority DESC."""
        async def run_test():
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            # Same due_date, priorities out of order: expect HIGH before LOW
            await self.repo.create(
                Task(title="low-first", due_date=f"{today} 10:00:00", priority=Priority.LOW)
            )
            await self.repo.create(
                Task(title="high-second", due_date=f"{today} 10:00:00", priority=Priority.HIGH)
            )
            # Earlier due_date should come first regardless of priority
            await self.repo.create(
                Task(title="tomorrow-low", due_date=f"{tomorrow} 08:00:00", priority=Priority.LOW)
            )

            tasks, total = await self.repo.list_all()
            self.assertEqual(total, 3)
            titles = [t.title for t in tasks]
            # Expected: today-high, today-low, tomorrow-low
            self.assertEqual(
                titles,
                ["high-second", "low-first", "tomorrow-low"],
                f"sort order wrong: {titles}",
            )

        self.loop.run_until_complete(run_test())

    def test_sort_critical_priority_highest(self):
        """CRITICAL sorts above HIGH within the same due_date."""
        async def run_test():
            today = datetime.now().strftime("%Y-%m-%d")
            await self.repo.create(
                Task(title="high", due_date=f"{today} 10:00:00", priority=Priority.HIGH)
            )
            await self.repo.create(
                Task(title="critical", due_date=f"{today} 10:00:00", priority=Priority.CRITICAL)
            )

            tasks, _ = await self.repo.list_all()
            self.assertEqual(tasks[0].title, "critical")
            self.assertEqual(tasks[1].title, "high")

        self.loop.run_until_complete(run_test())

    # --- FR-10: date filters ---------------------------------------------

    def test_filter_today(self):
        """due_date='today' returns only tasks due today."""
        async def run_test():
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            await self.repo.create(Task(title="due-today", due_date=f"{today} 12:00:00"))
            await self.repo.create(Task(title="due-tomorrow", due_date=f"{tomorrow} 12:00:00"))

            tasks, total = await self.repo.list_all(due_date="today")
            self.assertEqual(total, 1)
            self.assertEqual(tasks[0].title, "due-today")

        self.loop.run_until_complete(run_test())

    def test_filter_tomorrow(self):
        """due_date='tomorrow' returns only tasks due tomorrow."""
        async def run_test():
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            await self.repo.create(Task(title="due-today", due_date=f"{today} 12:00:00"))
            await self.repo.create(Task(title="due-tomorrow", due_date=f"{tomorrow} 12:00:00"))

            tasks, total = await self.repo.list_all(due_date="tomorrow")
            self.assertEqual(total, 1)
            self.assertEqual(tasks[0].title, "due-tomorrow")

        self.loop.run_until_complete(run_test())

    def test_filter_overdue(self):
        """due_date='overdue' returns pending tasks with past due_date."""
        async def run_test():
            past = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
            future = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

            await self.repo.create(
                Task(title="overdue-pending", due_date=past, status=TaskStatus.PENDING)
            )
            # Completed past task should NOT be overdue
            await self.repo.create(
                Task(title="past-completed", due_date=past, status=TaskStatus.COMPLETED)
            )
            # Future pending task should NOT be overdue
            await self.repo.create(
                Task(title="future-pending", due_date=future, status=TaskStatus.PENDING)
            )

            tasks, total = await self.repo.list_all(due_date="overdue")
            self.assertEqual(total, 1)
            self.assertEqual(tasks[0].title, "overdue-pending")

        self.loop.run_until_complete(run_test())

    def test_filter_date_range(self):
        """due_date range 'start..end' returns tasks within the interval."""
        async def run_test():
            start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            mid = datetime.now().strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            outside = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")

            await self.repo.create(Task(title="mid", due_date=f"{mid} 12:00:00"))
            await self.repo.create(Task(title="far", due_date=f"{outside} 12:00:00"))

            tasks, total = await self.repo.list_all(due_date=f"{start}..{end}")
            self.assertEqual(total, 1)
            self.assertEqual(tasks[0].title, "mid")

        self.loop.run_until_complete(run_test())

    def test_filter_exact_date(self):
        """due_date exact date matches tasks with that date prefix."""
        async def run_test():
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            await self.repo.create(Task(title="today-task", due_date=f"{today} 09:00:00"))
            await self.repo.create(Task(title="tomorrow-task", due_date=f"{tomorrow} 09:00:00"))

            tasks, total = await self.repo.list_all(due_date=today)
            self.assertEqual(total, 1)
            self.assertEqual(tasks[0].title, "today-task")

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
