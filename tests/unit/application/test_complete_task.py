"""
Test Complete Task Use Case
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from todolist_mcp.domain.entities import Task, Priority, TaskStatus
from todolist_mcp.application.use_cases.complete_task import CompleteTaskUseCase


class TestCompleteTaskUseCase(unittest.TestCase):
    """Tests for CompleteTaskUseCase."""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_complete_existing_task(self):
        """Test completing an existing task."""
        async def run_test():
            task_id = str(uuid4())
            existing_task = Task(
                title="Task to complete",
                status=TaskStatus.PENDING,
                task_id=task_id,
            )
            
            completed_task = Task(
                title="Task to complete",
                status=TaskStatus.COMPLETED,
                task_id=task_id,
            )
            
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=existing_task)
            mock_repo.update = AsyncMock(return_value=completed_task)
            
            use_case = CompleteTaskUseCase(mock_repo)
            
            result = await use_case.execute(task_id=task_id)
            
            self.assertEqual(result.status, TaskStatus.COMPLETED)
            mock_repo.update.assert_called_once()
        
        self.loop.run_until_complete(run_test())
    
    def test_complete_nonexistent_task(self):
        """Test completing a non-existent task raises ValueError."""
        async def run_test():
            task_id = str(uuid4())
            
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            
            use_case = CompleteTaskUseCase(mock_repo)
            
            with self.assertRaises(ValueError) as context:
                await use_case.execute(task_id=task_id)
            
            self.assertIn("not found", str(context.exception))
        
        self.loop.run_until_complete(run_test())
    
    def test_complete_already_completed_task(self):
        """Test completing an already completed task raises ValueError."""
        async def run_test():
            task_id = str(uuid4())
            completed_task = Task(
                title="Already completed",
                status=TaskStatus.COMPLETED,
                task_id=task_id,
            )
            
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=completed_task)
            
            use_case = CompleteTaskUseCase(mock_repo)
            
            with self.assertRaises(ValueError) as context:
                await use_case.execute(task_id=task_id)
            
            self.assertIn("already completed", str(context.exception).lower())
        
        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
