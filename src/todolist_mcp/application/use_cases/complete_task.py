"""
Complete Task Use Case

Handles marking a task as completed.
"""

from todolist_mcp.domain.entities import Task, TaskStatus
from todolist_mcp.domain.repositories import TaskRepository


class CompleteTaskUseCase:
    """
    Use case for marking a task as completed.
    """

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    async def execute(self, task_id: str) -> Task:
        """
        Execute the complete task use case.

        Args:
            task_id: Task UUID as string

        Returns:
            Task: Updated task

        Raises:
            ValueError: If task not found or task is already completed
        """
        # Get existing task
        task = await self.repository.get_by_id(task_id)

        if task is None:
            raise ValueError(f"Task with id {task_id} not found")

        # Cannot complete already completed tasks
        if task.status == TaskStatus.COMPLETED:
            raise ValueError("Task already completed")

        # Mark as completed
        task.mark_completed()

        # Save to repository
        updated_task = await self.repository.update(task)

        return updated_task
