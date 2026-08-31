"""
SQLite Task Repository

Implementation of TaskRepository interface using SQLite.
"""

import os
from datetime import datetime, timedelta

from sqlalchemy import and_, asc, create_engine, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from todolist_mcp.domain.entities import Priority, Task, TaskStatus
from todolist_mcp.domain.repositories import TaskRepository

from .models import Base, TaskModel


class SQLiteTaskRepository(TaskRepository):
    """
    SQLite implementation of TaskRepository.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.path.expanduser("~/.todolist-mcp/todolist.db")
        self.engine = None
        self.async_engine = None
        self.Session = None
        self.AsyncSession = None

    async def initialize(self) -> None:
        """Initialize the repository and create tables."""
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Create async engine
        self.async_engine = create_async_engine(f"sqlite+aiosqlite:///{self.db_path}")
        self.AsyncSession = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Create tables
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Also create sync engine for compatibility
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.Session = sessionmaker(bind=self.engine)

    def _to_orm(self, task: Task) -> TaskModel:
        """Convert Task entity to TaskModel ORM."""
        return TaskModel(
            id=str(task.id),
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority.value if task.priority else "medium",
            status=task.status.value if task.status else "pending",
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def _from_orm(self, model: TaskModel) -> Task:
        """Convert TaskModel ORM to Task entity."""
        return Task(
            title=model.title,
            description=model.description,
            due_date=model.due_date,
            priority=Priority(model.priority) if model.priority else None,
            status=TaskStatus(model.status) if model.status else None,
            task_id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def create(self, task: Task) -> Task:
        """Create a new task."""
        orm = self._to_orm(task)

        async with self.AsyncSession() as session:
            session.add(orm)
            await session.commit()
            await session.refresh(orm)

        # Return the task with the generated ID
        return self._from_orm(orm)

    async def get_by_id(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        async with self.AsyncSession() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.id == task_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._from_orm(model)

    async def list_all(
        self,
        status: str | None = None,
        priority: str | None = None,
        due_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[Task], int]:
        """List tasks with optional filters."""
        async with self.AsyncSession() as session:
            # Build query
            query = select(TaskModel)

            # Apply filters
            if status:
                query = query.where(TaskModel.status == status)
            if priority:
                query = query.where(TaskModel.priority == priority)

            # Handle due_date filter
            if due_date:
                due_date_lower = due_date.lower()
                if due_date_lower == "today":
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    query = query.where(TaskModel.due_date.startswith(today_str))
                elif due_date_lower == "tomorrow":
                    tomorrow = datetime.now() + timedelta(days=1)
                    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
                    query = query.where(TaskModel.due_date.startswith(tomorrow_str))
                elif due_date_lower == "overdue":
                    now = datetime.now()
                    query = query.where(
                        and_(
                            TaskModel.due_date.isnot(None),
                            TaskModel.status == "pending",
                            TaskModel.due_date < now.strftime("%Y-%m-%d %H:%M:%S")
                        )
                    )
                elif ".." in due_date:
                    # Range filter
                    start_date, end_date = due_date.split("..")
                    query = query.where(
                        and_(
                            TaskModel.due_date >= start_date,
                            TaskModel.due_date <= end_date
                        )
                    )
                else:
                    # Exact date or partial match
                    query = query.where(TaskModel.due_date.startswith(due_date))

            # Count total (apply same filters)
            count_query = select(TaskModel.id)
            if status:
                count_query = count_query.where(TaskModel.status == status)
            if priority:
                count_query = count_query.where(TaskModel.priority == priority)
            if due_date:
                due_date_lower = due_date.lower()
                if due_date_lower == "today":
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    count_query = count_query.where(TaskModel.due_date.startswith(today_str))
                elif due_date_lower == "tomorrow":
                    tomorrow = datetime.now() + timedelta(days=1)
                    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
                    count_query = count_query.where(TaskModel.due_date.startswith(tomorrow_str))
                elif due_date_lower == "overdue":
                    now = datetime.now()
                    count_query = count_query.where(
                        and_(
                            TaskModel.due_date.isnot(None),
                            TaskModel.status == "pending",
                            TaskModel.due_date < now.strftime("%Y-%m-%d %H:%M:%S")
                        )
                    )
                elif ".." in due_date:
                    start_date, end_date = due_date.split("..")
                    count_query = count_query.where(
                        and_(
                            TaskModel.due_date >= start_date,
                            TaskModel.due_date <= end_date
                        )
                    )
                else:
                    count_query = count_query.where(TaskModel.due_date.startswith(due_date))

            total_result = await session.execute(count_query)
            total = len(total_result.scalars().all())

            # Apply sorting: due_date ASC, then priority DESC
            query = query.order_by(
                asc(TaskModel.due_date),
                desc(TaskModel.priority)
            )

            # Apply pagination
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            # Execute query
            result = await session.execute(query)
            models = result.scalars().all()

            tasks = [self._from_orm(model) for model in models]

            return tasks, total

    async def update(self, task: Task) -> Task:
        """Update a task."""
        async with self.AsyncSession() as session:
            # Get existing record
            result = await session.execute(
                select(TaskModel).where(TaskModel.id == str(task.id))
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                raise ValueError(f"Task with id {task.id} not found")

            # Update fields
            existing.title = task.title
            existing.description = task.description
            existing.due_date = task.due_date
            existing.priority = task.priority.value if task.priority else "medium"
            existing.status = task.status.value if task.status else "pending"
            existing.updated_at = task.updated_at

            await session.commit()
            await session.refresh(existing)

        return self._from_orm(existing)

    async def delete(self, task_id: str) -> bool:
        """Delete a task."""
        async with self.AsyncSession() as session:
            result = await session.execute(
                delete(TaskModel).where(TaskModel.id == task_id)
            )

            deleted = result.rowcount > 0
            await session.commit()

            return deleted
