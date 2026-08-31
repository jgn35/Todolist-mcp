"""
Repository Interfaces (Ports)

Define the interface for task persistence.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import Task


class TaskRepository(ABC):
    """
    Abstract base class for task repository.
    
    Defines the interface for task persistence operations.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository (e.g., create database tables)."""
        pass
    
    @abstractmethod
    async def create(self, task: Task) -> Task:
        """
        Create a new task.
        
        Args:
            task: Task entity to create
        
        Returns:
            Task: Created task with generated ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task UUID as string
        
        Returns:
            Task: Task entity or None if not found
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> tuple[List[Task], int]:
        """
        List tasks with optional filters.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            due_date: Filter by due date
            limit: Maximum number of tasks
            offset: Pagination offset
        
        Returns:
            tuple: (list of tasks, total count)
        """
        pass
    
    @abstractmethod
    async def update(self, task: Task) -> Task:
        """
        Update a task.
        
        Args:
            task: Task entity with updated values
        
        Returns:
            Task: Updated task
        """
        pass
    
    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task UUID as string
        
        Returns:
            bool: True if deleted, False if not found
        """
        pass
