"""Tests for RadicaleTaskRepository using a fake _request transport."""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from todolist_mcp.domain.entities import Priority, Task, TaskStatus
from todolist_mcp.infrastructure.radicale_adapter.repository import RadicaleTaskRepository
from todolist_mcp.infrastructure.radicale_adapter.vtodo import task_to_vtodo_ical

TASK_ID = UUID("12345678-1234-5678-1234-567812345678")


def _task(title="Task", **kwargs) -> Task:
    kwargs.setdefault("task_id", TASK_ID)
    return Task(title=title, **kwargs)


def _multistatus(*icals: str) -> str:
    responses = "".join(
        f"""
  <D:response>
    <D:href>/todolist/{i}.ics</D:href>
    <D:propstat>
      <D:prop>
        <D:getetag>"etag{i}"</D:getetag>
        <C:calendar-data>{ical}</C:calendar-data>
      </D:prop>
      <D:status>HTTP/1.1 200 OK</D:status>
    </D:propstat>
  </D:response>"""
        for i, ical in enumerate(icals)
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">'
        f"{responses}"
        "</D:multistatus>"
    )


class FakeRadicaleRepository(RadicaleTaskRepository):
    """Repository whose HTTP layer is replaced by a handler function."""

    def __init__(self, handler, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler
        self.calls: list[tuple] = []

    async def _request(self, method, url, data=None, headers=None):
        self.calls.append((method, url, data, headers))
        return self.handler(method, url, data, headers)


def _ok_handler(method, url, data=None, headers=None):
    return 201, ""


class TestConfiguration:
    def test_env_var_configuration(self):
        env = {
            "TODOLIST_MCP_RADICALE_URL": "http://radicale.local:5232/",
            "TODOLIST_MCP_RADICALE_USERNAME": "alice",
            "TODOLIST_MCP_RADICALE_PASSWORD": "secret",
            "TODOLIST_MCP_RADICALE_COLLECTION": "/tasks/",
        }
        with patch.dict(os.environ, env):
            repo = RadicaleTaskRepository()
        assert repo.base_url == "http://radicale.local:5232"
        assert repo.username == "alice"
        assert repo.password == "secret"
        assert repo.collection == "tasks"
        assert repo.collection_url == "http://radicale.local:5232/tasks/"

    def test_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            repo = RadicaleTaskRepository()
        assert repo.base_url == "http://localhost:5232"
        assert repo.collection == "todolist"

    def test_constructor_overrides_env(self):
        with patch.dict(os.environ, {"TODOLIST_MCP_RADICALE_URL": "http://env:5232"}):
            repo = RadicaleTaskRepository(url="http://ctor:5232")
        assert repo.base_url == "http://ctor:5232"


class TestInitialize:
    async def _initialize(self, mkcol_status: int) -> RadicaleTaskRepository:
        with (
            patch(
                "todolist_mcp.infrastructure.radicale_adapter.repository.aiohttp.ClientSession"
            ) as session_cls,
            patch.object(
                RadicaleTaskRepository,
                "_request",
                new=AsyncMock(return_value=(mkcol_status, "")),
            ) as request_mock,
        ):
            repo = RadicaleTaskRepository()
            await repo.initialize()
        assert repo._session is session_cls.return_value
        request_mock.assert_awaited_once_with("MKCOL", repo.collection_url)
        return repo

    async def test_initialize_creates_collection(self):
        await self._initialize(201)

    async def test_initialize_accepts_existing_collection(self):
        await self._initialize(405)

    async def test_initialize_raises_on_server_error(self):
        with (
            patch(
                "todolist_mcp.infrastructure.radicale_adapter.repository.aiohttp.ClientSession"
            ),
            patch.object(
                RadicaleTaskRepository,
                "_request",
                new=AsyncMock(return_value=(500, "boom")),
            ),
        ):
            repo = RadicaleTaskRepository()
            with pytest.raises(ConnectionError):
                await repo.initialize()


class TestCreate:
    async def test_create_puts_vtodo_resource(self):
        repo = FakeRadicaleRepository(_ok_handler)
        task = _task(title="Write tests", priority=Priority.HIGH)

        result = await repo.create(task)

        assert result.id == TASK_ID
        method, url, data, _ = repo.calls[0]
        assert method == "PUT"
        assert url == f"{repo.collection_url}{TASK_ID}.ics"
        assert f"UID:{TASK_ID}" in data
        assert "SUMMARY:Write tests" in data
        assert "PRIORITY:3" in data
        assert "STATUS:NEEDS-ACTION" in data

    async def test_create_raises_on_failure(self):
        repo = FakeRadicaleRepository(lambda m, u, d=None, h=None: (500, "err"))
        with pytest.raises(ConnectionError):
            await repo.create(_task())


class TestGetById:
    async def test_get_existing_task(self):
        task = _task(title="Fetch me", due_date="2026-12-31 23:59:59")
        ical = task_to_vtodo_ical(task)
        repo = FakeRadicaleRepository(lambda m, u, d=None, h=None: (200, ical))

        result = await repo.get_by_id(str(TASK_ID))

        assert result is not None
        assert result.id == TASK_ID
        assert result.title == "Fetch me"
        assert result.due_date == "2026-12-31 23:59:59"
        method, url, _, _ = repo.calls[0]
        assert method == "GET"
        assert url.endswith(f"{TASK_ID}.ics")

    async def test_get_missing_task_returns_none(self):
        repo = FakeRadicaleRepository(lambda m, u, d=None, h=None: (404, ""))
        assert await repo.get_by_id(str(uuid4())) is None


class TestListAll:
    def _repo_with_tasks(self, tasks: list[Task]) -> FakeRadicaleRepository:
        body = _multistatus(*[task_to_vtodo_ical(t) for t in tasks])
        return FakeRadicaleRepository(lambda m, u, d=None, h=None: (207, body))

    async def test_list_all_returns_everything_with_total(self):
        today = datetime.now().strftime("%Y-%m-%d")
        tasks = [
            _task(title="a", task_id=uuid4(), due_date=f"{today} 10:00:00"),
            _task(title="b", task_id=uuid4()),
        ]
        repo = self._repo_with_tasks(tasks)

        result, total = await repo.list_all()

        assert total == 2
        assert len(result) == 2
        method, url, data, headers = repo.calls[0]
        assert method == "REPORT"
        assert url == repo.collection_url
        assert "calendar-query" in data
        assert headers["Depth"] == "1"

    async def test_filter_by_status(self):
        tasks = [
            _task(title="open", task_id=uuid4(), status=TaskStatus.PENDING),
            _task(title="done", task_id=uuid4(), status=TaskStatus.COMPLETED),
        ]
        repo = self._repo_with_tasks(tasks)

        result, total = await repo.list_all(status="completed")

        assert total == 1
        assert result[0].title == "done"

    async def test_filter_by_priority(self):
        tasks = [
            _task(title="low", task_id=uuid4(), priority=Priority.LOW),
            _task(title="crit", task_id=uuid4(), priority=Priority.CRITICAL),
        ]
        repo = self._repo_with_tasks(tasks)

        result, total = await repo.list_all(priority="critical")

        assert total == 1
        assert result[0].title == "crit"

    async def test_filter_due_today_and_overdue(self):
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        tasks = [
            _task(title="today", task_id=uuid4(), due_date=f"{today} 08:00:00"),
            _task(title="overdue", task_id=uuid4(), due_date=yesterday),
            _task(title="later", task_id=uuid4(), due_date="2099-01-01 00:00:00"),
        ]
        repo = self._repo_with_tasks(tasks)

        result, total = await repo.list_all(due_date="today")
        assert total == 1 and result[0].title == "today"

        result, total = await repo.list_all(due_date="overdue")
        assert total == 1 and result[0].title == "overdue"

    async def test_filter_due_range(self):
        tasks = [
            _task(title="in", task_id=uuid4(), due_date="2026-08-15 10:00:00"),
            _task(title="out", task_id=uuid4(), due_date="2026-09-01 10:00:00"),
        ]
        repo = self._repo_with_tasks(tasks)

        result, total = await repo.list_all(due_date="2026-08-01..2026-08-31")

        assert total == 1
        assert result[0].title == "in"

    async def test_sorting_due_date_then_priority_weight(self):
        tasks = [
            _task(title="low-late", task_id=uuid4(), due_date="2026-12-31 00:00:00", priority=Priority.LOW),
            _task(title="high-early", task_id=uuid4(), due_date="2026-01-01 00:00:00", priority=Priority.HIGH),
            _task(title="crit-late", task_id=uuid4(), due_date="2026-12-31 00:00:00", priority=Priority.CRITICAL),
        ]
        repo = self._repo_with_tasks(tasks)

        result, total = await repo.list_all()

        assert total == 3
        assert [t.title for t in result] == ["high-early", "crit-late", "low-late"]

    async def test_pagination(self):
        tasks = [_task(title=f"t{i}", task_id=uuid4()) for i in range(5)]
        repo = self._repo_with_tasks(tasks)

        page, total = await repo.list_all(limit=2, offset=2)

        assert total == 5
        assert len(page) == 2


class TestUpdate:
    async def test_update_missing_task_raises_value_error(self):
        repo = FakeRadicaleRepository(lambda m, u, d=None, h=None: (404, ""))
        with pytest.raises(ValueError, match="not found"):
            await repo.update(_task(title="ghost"))

    async def test_update_puts_new_vtodo(self):
        calls = []

        def handler(method, url, data=None, headers=None):
            calls.append(method)
            if method == "GET":
                return 200, task_to_vtodo_ical(_task(title="old"))
            return 204, ""

        repo = FakeRadicaleRepository(handler)
        updated = _task(title="new title", status=TaskStatus.COMPLETED)

        result = await repo.update(updated)

        assert result.title == "new title"
        assert calls == ["GET", "PUT"]
        put_data = repo.calls[-1][2]
        assert "SUMMARY:new title" in put_data
        assert "STATUS:COMPLETED" in put_data


class TestDelete:
    async def test_delete_existing_returns_true(self):
        repo = FakeRadicaleRepository(lambda m, u, d=None, h=None: (204, ""))
        assert await repo.delete(str(TASK_ID)) is True
        method, url, _, _ = repo.calls[0]
        assert method == "DELETE"
        assert url.endswith(f"{TASK_ID}.ics")

    async def test_delete_missing_returns_false(self):
        repo = FakeRadicaleRepository(lambda m, u, d=None, h=None: (404, ""))
        assert await repo.delete(str(uuid4())) is False


class TestBackendSelection:
    def test_storage_backend_env_var(self):
        import todolist_mcp

        with patch.dict(os.environ, {"TODOLIST_MCP_STORAGE_BACKEND": "radicale"}):
            assert todolist_mcp._storage_backend() == "radicale"
        with patch.dict(os.environ, {}, clear=True):
            assert todolist_mcp._storage_backend() == "sqlite"

    async def test_get_repository_returns_radicale_backend(self):
        import todolist_mcp
        from todolist_mcp.infrastructure.radicale_adapter.repository import (
            RadicaleTaskRepository,
        )

        with patch.dict(os.environ, {"TODOLIST_MCP_STORAGE_BACKEND": "radicale"}):
            with patch.object(
                RadicaleTaskRepository, "initialize", new=AsyncMock()
            ), patch.object(todolist_mcp, "_task_repository", None):
                repo = await todolist_mcp.get_repository()
        assert isinstance(repo, RadicaleTaskRepository)
