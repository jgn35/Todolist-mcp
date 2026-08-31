"""
Get Task Use Case

Handles retrieving a single task.
"""

from todolist_mcp.domain.entities import Task
from todolist_mcp.domain.repositories import TaskRepository


class GetTaskUseCase:
    """
    Use case for retrieving a task by ID.
    """

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    async def execute(self, task_id: str) -> Task:
        """
        Execute the get task use case.

        Args:
            task_id: Task UUID as string

        Returns:
            Task: Retrieved task

        Raises:
            ValueError: If task not found
        """
        task = await self.repository.get_by_id(task_id)

        if task is None:
            raise ValueError(f"Task with id {task_id} not found")

        return task
