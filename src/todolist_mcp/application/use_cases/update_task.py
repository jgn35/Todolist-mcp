"""
Update Task Use Case

Handles updating a task.
"""

from typing import Optional
from todolist_mcp.domain.entities import Task, Priority, TaskStatus
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
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
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
            ValueError: If task not found
        """
        # Get existing task
        task = await self.repository.get_by_id(task_id)
        
        if task is None:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Parse priority
        priority_enum = None
        if priority:
            priority_enum = Priority(priority.lower())
        
        # Parse status
        status_enum = None
        if status:
            status_enum = TaskStatus(status.lower())
        
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
