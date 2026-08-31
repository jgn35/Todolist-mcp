"""
Integration Tests for MCP Tools

Tests end-to-end functionality of MCP tools with database.
"""

import unittest
import asyncio
import tempfile
import os
from uuid import uuid4

from todolist_mcp.domain.entities import Task, Priority, TaskStatus
from todolist_mcp.infrastructure.sqlite_adapter.repository import SQLiteTaskRepository


class TestMCPToolsIntegration(unittest.TestCase):
    """Integration tests for MCP tools with real database."""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        async def init_repo():
            self.repo = SQLiteTaskRepository(db_path=self.db_path)
            await self.repo.initialize()
        
        self.loop.run_until_complete(init_repo())
    
    def tearDown(self):
        self.loop.close()
        # Clean up temporary files
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_create_and_get_task(self):
        """Test creating a task and retrieving it."""
        async def run_test():
            # Create a task
            task = Task(
                title="Integration Test Task",
                description="Test Description",
                priority=Priority.HIGH,
                due_date="2026-12-31 23:59:59",
            )
            
            created = await self.repo.create(task)
            self.assertIsNotNone(created.id)
            
            # Retrieve the task
            retrieved = await self.repo.get_by_id(str(created.id))
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.title, "Integration Test Task")
            self.assertEqual(retrieved.description, "Test Description")
            self.assertEqual(retrieved.priority, Priority.HIGH)
            self.assertEqual(retrieved.due_date, "2026-12-31 23:59:59")
        
        self.loop.run_until_complete(run_test())
    
    def test_list_tasks_empty(self):
        """Test listing tasks from empty database."""
        async def run_test():
            tasks, total = await self.repo.list_all()
            self.assertEqual(len(tasks), 0)
            self.assertEqual(total, 0)
        
        self.loop.run_until_complete(run_test())
    
    def test_list_tasks_with_data(self):
        """Test listing tasks with data."""
        async def run_test():
            # Create multiple tasks
            for i in range(3):
                task = Task(title=f"Task {i}", priority=Priority.MEDIUM)
                await self.repo.create(task)
            
            # List all tasks
            tasks, total = await self.repo.list_all()
            self.assertEqual(len(tasks), 3)
            self.assertEqual(total, 3)
        
        self.loop.run_until_complete(run_test())
    
    def test_update_task(self):
        """Test updating a task."""
        async def run_test():
            # Create a task
            task = Task(title="Original Title", priority=Priority.LOW)
            created = await self.repo.create(task)
            
            # Update the task
            created.title = "Updated Title"
            created.priority = Priority.HIGH
            
            updated = await self.repo.update(created)
            self.assertEqual(updated.title, "Updated Title")
            self.assertEqual(updated.priority, Priority.HIGH)
        
        self.loop.run_until_complete(run_test())
    
    def test_delete_task(self):
        """Test deleting a task."""
        async def run_test():
            # Create a task
            task = Task(title="Task to Delete")
            created = await self.repo.create(task)
            task_id = str(created.id)
            
            # Verify task exists
            retrieved = await self.repo.get_by_id(task_id)
            self.assertIsNotNone(retrieved)
            
            # Delete the task
            deleted = await self.repo.delete(task_id)
            self.assertTrue(deleted)
            
            # Verify task is gone
            retrieved = await self.repo.get_by_id(task_id)
            self.assertIsNone(retrieved)
        
        self.loop.run_until_complete(run_test())
    
    def test_list_tasks_with_status_filter(self):
        """Test listing tasks with status filter."""
        async def run_test():
            # Create tasks with different statuses
            task1 = Task(title="Pending Task", status=TaskStatus.PENDING)
            task2 = Task(title="Completed Task", status=TaskStatus.COMPLETED)
            await self.repo.create(task1)
            await self.repo.create(task2)
            
            # List only pending tasks
            tasks, total = await self.repo.list_all(status="pending")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].status, TaskStatus.PENDING)
        
        self.loop.run_until_complete(run_test())
    
    def test_list_tasks_with_priority_filter(self):
        """Test listing tasks with priority filter."""
        async def run_test():
            # Create tasks with different priorities
            task1 = Task(title="Low Priority", priority=Priority.LOW)
            task2 = Task(title="High Priority", priority=Priority.HIGH)
            await self.repo.create(task1)
            await self.repo.create(task2)
            
            # List only high priority tasks
            tasks, total = await self.repo.list_all(priority="high")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].priority, Priority.HIGH)
        
        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
