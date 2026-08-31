"""
Delete Task Use Case

Handles deleting a task.
"""

from todolist_mcp.domain.repositories import TaskRepository


class DeleteTaskUseCase:
    """
    Use case for deleting a task.
    """
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    async def execute(self, task_id: str) -> None:
        """
        Execute the delete task use case.
        
        Args:
            task_id: Task UUID as string
        
        Raises:
            ValueError: If task not found
        """
        # Check if task exists
        task = await self.repository.get_by_id(task_id)
        
        if task is None:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Delete task
        await self.repository.delete(task_id)
