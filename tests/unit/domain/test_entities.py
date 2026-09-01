"""
Test Domain Entities
"""

import unittest
from uuid import UUID

from todolist_mcp.domain.entities import Priority, Task, TaskStatus


class TestTask(unittest.TestCase):
    """Tests for Task entity."""

    def test_create_task_default_values(self):
        """Test task creation with default values."""
        task = Task(title="Test Task")

        assert task.title == "Test Task"
        assert task.description is None
        assert task.due_date is None
        assert task.priority == Priority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.id, UUID)
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_create_task_with_all_values(self):
        """Test task creation with all values specified."""
        task = Task(
            title="Test Task",
            description="Test Description",
            due_date="2026-12-31 23:59:59",
            priority=Priority.HIGH,
            status=TaskStatus.COMPLETED,
        )

        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.due_date == "2026-12-31 23:59:59"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.COMPLETED

    def test_to_dict(self):
        """Test task to_dict method."""
        task = Task(
            title="Test Task",
            description="Test Description",
            due_date="2026-12-31 23:59:59",
            priority=Priority.HIGH,
            status=TaskStatus.COMPLETED,
        )

        result = task.to_dict()

        assert result["title"] == "Test Task"
        assert result["description"] == "Test Description"
        assert result["due_date"] == "2026-12-31 23:59:59"
        assert result["priority"] == "high"
        assert result["status"] == "completed"
        assert "id" in result

    def test_from_dict(self):
        """Test task from_dict method."""
        data = {
            "title": "Test Task",
            "description": "Test Description",
            "due_date": "2026-12-31 23:59:59",
            "priority": "high",
            "status": "completed",
        }

        task = Task.from_dict(data)

        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.due_date == "2026-12-31 23:59:59"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.COMPLETED

    def test_update(self):
        """Test task update method."""
        task = Task(title="Original Title")

        task.update(
            title="Updated Title",
            description="Updated Description",
            priority=Priority.HIGH,
        )

        self.assertEqual(task.title, "Updated Title")
        self.assertEqual(task.description, "Updated Description")
        self.assertEqual(task.priority, Priority.HIGH)
        # updated_at should be a string timestamp
        self.assertIsInstance(task.updated_at, str)
        self.assertEqual(len(task.updated_at), 19)  # YYYY-MM-DD HH:MM:SS format

    def test_mark_completed(self):
        """Test mark_completed method."""
        task = Task(title="Test Task", status=TaskStatus.PENDING)

        task.mark_completed()

        assert task.status == TaskStatus.COMPLETED

    def test_mark_cancelled(self):
        """Test mark_cancelled method."""
        task = Task(title="Test Task", status=TaskStatus.PENDING)

        task.mark_cancelled()

        assert task.status == TaskStatus.CANCELLED


class TestPriority(unittest.TestCase):
    """Tests for Priority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"


class TestTaskStatus(unittest.TestCase):
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"
