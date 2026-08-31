"""
Update Task Use Case

Handles updating a task.
"""


from todolist_mcp.domain.entities import Priority, Task, TaskStatus
from todolist_mcp.domain.repositories import TaskRepository


class UpdateTaskUseCase:
    """
    Use case for updating a task.
    """

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    async def execute(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        status: str | None = None,
    ) -> Task:
        """
        Execute the update task use case.

        Args:
            task_id: Task UUID as string
            title: New title
            description: New description
            due_date: New due date
            priority: New priority
            status: New status

        Returns:
            Task: Updated task

        Raises:
            ValueError: If task not found or task is completed
        """
        # Get existing task
        task = await self.repository.get_by_id(task_id)

        if task is None:
            raise ValueError(f"Task with id {task_id} not found")

        # Cannot update completed tasks
        if task.status == TaskStatus.COMPLETED:
            raise ValueError("Cannot update completed task")

        # Parse priority
        priority_enum = None
        if priority:
            try:
                priority_enum = Priority(priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority value: {priority}. Must be low, medium, high, or critical")

        # Parse status
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status.lower())
            except ValueError:
                raise ValueError(f"Invalid status value: {status}. Must be pending, completed, or cancelled")

        # Update task
        task.update(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority_enum,
            status=status_enum,
        )

        # Save to repository
        updated_task = await self.repository.update(task)

        return updated_task
