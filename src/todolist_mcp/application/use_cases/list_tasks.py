"""
List Tasks Use Case

Handles listing tasks with filters.
"""

from typing import Optional
from dataclasses import dataclass
from todolist_mcp.domain.entities import Task
from todolist_mcp.domain.repositories import TaskRepository


@dataclass
class ListTasksResult:
    """Result of listing tasks."""
    tasks: list[Task]
    total: int
    limit: Optional[int]
    offset: Optional[int]


class ListTasksUseCase:
    """
    Use case for listing tasks.
    """
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    async def execute(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListTasksResult:
        """
        Execute the list tasks use case.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            due_date: Filter by due date
            limit: Maximum number of tasks
            offset: Pagination offset
        
        Returns:
            ListTasksResult: Tasks and pagination info
        """
        tasks, total = await self.repository.list_all(
            status=status,
            priority=priority,
            due_date=due_date,
            limit=limit,
            offset=offset,
        )
        
        return ListTasksResult(
            tasks=tasks,
            total=total,
            limit=limit,
            offset=offset,
        )
