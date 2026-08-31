"""
Domain Entities

Pure Python entities with no external dependencies.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class Priority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task:
    """
    Task entity representing a user's task.

    Attributes:
        id: Unique task identifier (UUID v4)
        title: Task title
        description: Task description (optional)
        due_date: Due date as string in YYYY-MM-DD HH:MM:SS format (optional)
        priority: Task priority
        status: Task status
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
        task_id: UUID | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ):
        self.id = task_id if task_id else uuid4()
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority if priority else Priority.MEDIUM
        self.status = status if status else TaskStatus.PENDING
        self.created_at = created_at if created_at else self._get_current_timestamp()
        self.updated_at = updated_at if updated_at else self.created_at

    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current timestamp in local timezone format."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        """Convert task to dictionary representation."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a Task from dictionary data."""
        return cls(
            title=data.get("title", ""),
            description=data.get("description"),
            due_date=data.get("due_date"),
            priority=Priority(data.get("priority", "medium")) if data.get("priority") else None,
            status=TaskStatus(data.get("status", "pending")) if data.get("status") else None,
            task_id=UUID(data.get("id", str(uuid4()))),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def update(
        self,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
    ) -> None:
        """Update task attributes."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if due_date is not None:
            self.due_date = due_date
        if priority is not None:
            self.priority = priority
        if status is not None:
            self.status = status
        self.updated_at = self._get_current_timestamp()

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = self._get_current_timestamp()

    def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.updated_at = self._get_current_timestamp()
