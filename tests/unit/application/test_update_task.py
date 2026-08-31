"""
Test Update Task Use Case
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from todolist_mcp.domain.entities import Task, Priority, TaskStatus
from todolist_mcp.application.use_cases.update_task import UpdateTaskUseCase


class TestUpdateTaskUseCase(unittest.TestCase):
    """Tests for UpdateTaskUseCase."""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_update_existing_task(self):
        """Test updating an existing task."""
        async def run_test():
            task_id = str(uuid4())
            existing_task = Task(
                title="Original Title",
                description="Original Description",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING,
                task_id=task_id,
            )
            
            updated_task = Task(
                title="Updated Title",
                description="Updated Description",
                priority=Priority.HIGH,
                status=TaskStatus.PENDING,
                task_id=task_id,
            )
            
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=existing_task)
            mock_repo.update = AsyncMock(return_value=updated_task)
            
            use_case = UpdateTaskUseCase(mock_repo)
            
            result = await use_case.execute(
                task_id=task_id,
                title="Updated Title",
                description="Updated Description",
                priority="high",
            )
            
            self.assertEqual(result.title, "Updated Title")
            self.assertEqual(result.description, "Updated Description")
            self.assertEqual(result.priority, Priority.HIGH)
            mock_repo.update.assert_called_once()
        
        self.loop.run_until_complete(run_test())
    
    def test_update_nonexistent_task(self):
        """Test updating a non-existent task raises ValueError."""
        async def run_test():
            task_id = str(uuid4())
            
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            
            use_case = UpdateTaskUseCase(mock_repo)
            
            with self.assertRaises(ValueError) as context:
                await use_case.execute(task_id=task_id, title="New Title")
            
            self.assertIn("not found", str(context.exception))
        
        self.loop.run_until_complete(run_test())
    
    def test_update_completed_task(self):
        """Test updating a completed task raises ValueError."""
        async def run_test():
            task_id = str(uuid4())
            completed_task = Task(
                title="Completed Task",
                status=TaskStatus.COMPLETED,
                task_id=task_id,
            )
            
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=completed_task)
            
            use_case = UpdateTaskUseCase(mock_repo)
            
            with self.assertRaises(ValueError) as context:
                await use_case.execute(task_id=task_id, title="New Title")
            
            self.assertIn("Cannot update completed task", str(context.exception))
        
        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
