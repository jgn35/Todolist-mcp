"""
Radicale (CalDAV) Task Repository

Implementation of TaskRepository interface using a CalDAV server such as
Radicale. Each task is stored as one VTODO inside a calendar collection.
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import aiohttp

from todolist_mcp.domain.entities import Task
from todolist_mcp.domain.repositories import TaskRepository

from .vtodo import parse_vtodo_ical, task_to_vtodo_ical

_DAV = "DAV:"
_CALDAV = "urn:ietf:params:xml:ns:caldav"

_CALENDAR_QUERY = f"""<?xml version="1.0" encoding="utf-8"?>
<C:calendar-query xmlns:D="{_DAV}" xmlns:C="{_CALDAV}">
  <D:prop>
    <D:getetag/>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="VTODO"/>
    </C:comp-filter>
  </C:filter>
</C:calendar-query>
"""

_PRIORITY_WEIGHT = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


class RadicaleTaskRepository(TaskRepository):
    """
    CalDAV implementation of TaskRepository targeting a Radicale server.

    Configuration (constructor args override environment variables):
        url:        TODOLIST_MCP_RADICALE_URL (default http://localhost:5232)
        username:   TODOLIST_MCP_RADICALE_USERNAME
        password:   TODOLIST_MCP_RADICALE_PASSWORD
        collection: TODOLIST_MCP_RADICALE_COLLECTION (default "todolist")
    """

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        collection: str | None = None,
    ):
        self.base_url = (
            url
            or os.environ.get("TODOLIST_MCP_RADICALE_URL")
            or "http://localhost:5232"
        ).rstrip("/")
        self.username = username if username is not None else os.environ.get(
            "TODOLIST_MCP_RADICALE_USERNAME", ""
        )
        self.password = password if password is not None else os.environ.get(
            "TODOLIST_MCP_RADICALE_PASSWORD", ""
        )
        self.collection = (
            collection
            or os.environ.get("TODOLIST_MCP_RADICALE_COLLECTION")
            or "todolist"
        ).strip("/")
        self._session: aiohttp.ClientSession | None = None

    @property
    def collection_url(self) -> str:
        return f"{self.base_url}/{self.collection}/"

    def _resource_url(self, task_id: str) -> str:
        return f"{self.collection_url}{task_id}.ics"

    async def initialize(self) -> None:
        """Open the HTTP session and make sure the calendar collection exists."""
        auth = None
        if self.username:
            auth = aiohttp.BasicAuth(self.username, self.password)
        self._session = aiohttp.ClientSession(
            auth=auth,
            headers={"Accept": "text/calendar, application/xml"},
        )
        status, _ = await self._request("MKCOL", self.collection_url)
        # 201 = created, 405 = already exists; both are fine.
        if status not in (200, 201, 405):
            raise ConnectionError(
                f"Cannot create Radicale collection {self.collection_url} "
                f"(HTTP {status})"
            )

    async def _request(
        self,
        method: str,
        url: str,
        data: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        """Perform one HTTP request and return (status, body text)."""
        if self._session is None:
            raise RuntimeError("Repository not initialized; call initialize() first")
        request_headers = {"Content-Type": "text/calendar; charset=utf-8"}
        if headers:
            request_headers.update(headers)
        async with self._session.request(
            method, url, data=data, headers=request_headers
        ) as response:
            body = await response.text()
            return response.status, body

    async def create(self, task: Task) -> Task:
        """Create a new task as a VTODO resource."""
        ical = task_to_vtodo_ical(task)
        status, _ = await self._request("PUT", self._resource_url(str(task.id)), data=ical)
        if status not in (200, 201, 204):
            raise ConnectionError(
                f"Failed to create task {task.id} on Radicale (HTTP {status})"
            )
        return task

    async def get_by_id(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        status, body = await self._request("GET", self._resource_url(task_id))
        if status == 404:
            return None
        if status != 200:
            raise ConnectionError(
                f"Failed to fetch task {task_id} from Radicale (HTTP {status})"
            )
        return parse_vtodo_ical(body)

    async def list_all(
        self,
        status: str | None = None,
        priority: str | None = None,
        due_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[Task], int]:
        """List tasks with optional filters (same semantics as the SQLite backend)."""
        status_code, body = await self._request(
            "REPORT",
            self.collection_url,
            data=_CALENDAR_QUERY,
            headers={"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
        )
        if status_code not in (200, 207):
            raise ConnectionError(
                f"Failed to list tasks from Radicale (HTTP {status_code})"
            )

        tasks = self._parse_multistatus(body)
        filtered = [t for t in tasks if self._matches(t, status, priority, due_date)]
        total = len(filtered)

        # Same order as the SQLite backend: due_date ASC (NULLs first),
        # then priority weight DESC (critical > high > medium > low).
        filtered.sort(
            key=lambda t: (
                t.due_date is not None,
                t.due_date or "",
                -_PRIORITY_WEIGHT.get(t.priority.value if t.priority else "", 0),
            )
        )

        if offset:
            filtered = filtered[offset:]
        if limit:
            filtered = filtered[:limit]

        return filtered, total

    async def update(self, task: Task) -> Task:
        """Update a task (full overwrite of its VTODO resource)."""
        status, _ = await self._request("GET", self._resource_url(str(task.id)))
        if status == 404:
            raise ValueError(f"Task with id {task.id} not found")
        ical = task_to_vtodo_ical(task)
        status, _ = await self._request("PUT", self._resource_url(str(task.id)), data=ical)
        if status not in (200, 201, 204):
            raise ConnectionError(
                f"Failed to update task {task.id} on Radicale (HTTP {status})"
            )
        return task

    async def delete(self, task_id: str) -> bool:
        """Delete a task resource."""
        status, _ = await self._request("DELETE", self._resource_url(task_id))
        return status in (200, 204)

    def _parse_multistatus(self, body: str) -> list[Task]:
        """Extract every VTODO from a multistatus REPORT response."""
        tasks: list[Task] = []
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return tasks
        for calendar_data in root.iter(f"{{{_CALDAV}}}calendar-data"):
            if calendar_data.text:
                task = parse_vtodo_ical(calendar_data.text)
                if task is not None:
                    tasks.append(task)
        return tasks

    def _matches(
        self,
        task: Task,
        status: str | None,
        priority: str | None,
        due_date: str | None,
    ) -> bool:
        """Apply the same filter semantics as the SQLite repository."""
        if status and (task.status is None or task.status.value != status):
            return False
        if priority and (task.priority is None or task.priority.value != priority):
            return False
        if due_date:
            if not self._matches_due_date(task, due_date):
                return False
        return True

    def _matches_due_date(self, task: Task, due_date: str) -> bool:
        due = task.due_date
        lowered = due_date.lower()
        if lowered == "today":
            return due is not None and due.startswith(datetime.now().strftime("%Y-%m-%d"))
        if lowered == "tomorrow":
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            return due is not None and due.startswith(tomorrow)
        if lowered == "overdue":
            return (
                due is not None
                and task.status is not None
                and task.status.value == "pending"
                and due < datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        if ".." in due_date:
            start_date, end_date = due_date.split("..", 1)
            return due is not None and start_date <= due <= end_date
        return due is not None and due.startswith(due_date)
