"""
Test Create Task Use Case - Missing Title Edge Case
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from todolist_mcp.application.use_cases.create_task import CreateTaskUseCase


class TestCreateTaskMissingTitle(unittest.TestCase):
    """Tests for CreateTaskUseCase edge cases."""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_create_task_with_empty_title(self):
        """Test creating a task with empty title raises ValueError."""
        async def run_test():
            mock_repo = MagicMock()
            use_case = CreateTaskUseCase(mock_repo)
            
            with self.assertRaises(ValueError) as context:
                await use_case.execute(title="")
            
            self.assertIn("Title is required", str(context.exception))
        
        self.loop.run_until_complete(run_test())
    
    def test_create_task_with_none_title(self):
        """Test creating a task with None title raises ValueError."""
        async def run_test():
            mock_repo = MagicMock()
            use_case = CreateTaskUseCase(mock_repo)
            
            with self.assertRaises(ValueError) as context:
                await use_case.execute(title=None)
            
            self.assertIn("Title is required", str(context.exception))
        
        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
