"""
Create Task Use Case

Handles task creation logic.
"""

from typing import Optional
from todolist_mcp.domain.entities import Task, Priority, TaskStatus
from todolist_mcp.domain.repositories import TaskRepository


class CreateTaskUseCase:
    """
    Use case for creating a new task.
    """
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    async def execute(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Task:
        """
        Execute the create task use case.
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date string
            priority: Priority string (low, medium, high)
        
        Returns:
            Task: Created task
        
        Raises:
            ValueError: If title is empty or None
        """
        # Validate title
        if not title:
            raise ValueError("Title is required")
        
        # Parse priority
        priority_enum = None
        if priority:
            try:
                priority_enum = Priority(priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority value: {priority}. Must be low, medium, high, or critical")
        
        # Create task entity
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority_enum,
            status=TaskStatus.PENDING,
        )
        
        # Save to repository
        created_task = await self.repository.create(task)
        
        return created_task
