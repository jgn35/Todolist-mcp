"""Tests for the minimal iCalendar VTODO serializer/parser."""

from uuid import UUID

from todolist_mcp.domain.entities import Priority, Task, TaskStatus
from todolist_mcp.infrastructure.radicale_adapter.vtodo import (
    parse_vtodo_ical,
    task_to_vtodo_ical,
)


def _sample_task() -> Task:
    return Task(
        title="Buy milk",
        description="2 liters, semi-skimmed",
        due_date="2026-12-31 23:59:59",
        priority=Priority.HIGH,
        status=TaskStatus.PENDING,
        task_id=UUID("12345678-1234-5678-1234-567812345678"),
        created_at="2026-01-01 10:00:00",
        updated_at="2026-01-02 11:00:00",
    )


def test_round_trip_preserves_all_fields():
    task = _sample_task()
    parsed = parse_vtodo_ical(task_to_vtodo_ical(task))

    assert parsed is not None
    assert parsed.id == task.id
    assert parsed.title == task.title
    assert parsed.description == task.description
    assert parsed.due_date == task.due_date
    assert parsed.priority == Priority.HIGH
    assert parsed.status == TaskStatus.PENDING
    assert parsed.created_at == task.created_at
    assert parsed.updated_at == task.updated_at


def test_priority_and_status_mapping():
    for priority, ical_value in [
        (Priority.CRITICAL, "PRIORITY:1"),
        (Priority.HIGH, "PRIORITY:3"),
        (Priority.MEDIUM, "PRIORITY:5"),
        (Priority.LOW, "PRIORITY:9"),
    ]:
        task = Task(title="t", priority=priority)
        assert ical_value in task_to_vtodo_ical(task)

    assert "STATUS:NEEDS-ACTION" in task_to_vtodo_ical(Task(title="t"))
    assert "STATUS:COMPLETED" in task_to_vtodo_ical(
        Task(title="t", status=TaskStatus.COMPLETED)
    )
    assert "STATUS:CANCELLED" in task_to_vtodo_ical(
        Task(title="t", status=TaskStatus.CANCELLED)
    )


def test_text_escaping_round_trip():
    task = Task(
        title="Title, with; special\\chars",
        description="line1\nline2, with; punctuation",
    )
    ical = task_to_vtodo_ical(task)
    assert "line1\\nline2\\, with\\; punctuation" in ical

    parsed = parse_vtodo_ical(ical)
    assert parsed is not None
    assert parsed.title == task.title
    assert parsed.description == task.description


def test_long_lines_are_folded_and_unfolded():
    long_description = "x" * 200
    task = Task(title="t", description=long_description)
    ical = task_to_vtodo_ical(task)

    for line in ical.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75

    parsed = parse_vtodo_ical(ical)
    assert parsed is not None
    assert parsed.description == long_description


def test_optional_fields_omitted_when_absent():
    task = Task(title="bare")
    ical = task_to_vtodo_ical(task)
    assert "DESCRIPTION:" not in ical
    assert "DUE:" not in ical

    parsed = parse_vtodo_ical(ical)
    assert parsed is not None
    assert parsed.description is None
    assert parsed.due_date is None
    assert parsed.priority == Priority.MEDIUM
    assert parsed.status == TaskStatus.PENDING


def test_parse_returns_none_without_uid():
    ical = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VTODO\r\nSUMMARY:x\r\nEND:VTODO\r\nEND:VCALENDAR\r\n"
    assert parse_vtodo_ical(ical) is None
