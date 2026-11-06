"""
Functional tests for the Radicale (CalDAV) storage backend.

These tests start a real Radicale server bound to 127.0.0.1 with a temporary
storage directory (loopback only, nothing is exposed) and exercise
RadicaleTaskRepository end-to-end over HTTP: MKCOL, PUT, GET, REPORT, DELETE.

The whole module is skipped when the ``radicale`` package is not installed.
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

pytest.importorskip("radicale")

import requests

from todolist_mcp.domain.entities import Priority, Task, TaskStatus
from todolist_mcp.infrastructure.radicale_adapter.repository import RadicaleTaskRepository


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def radicale_url():
    """Start a local Radicale server and return its base URL."""
    port = _free_port()
    workdir = tempfile.mkdtemp(prefix="radicale-func-")
    config_path = os.path.join(workdir, "config")
    with open(config_path, "w", encoding="utf-8") as fh:
        fh.write(
            "[server]\n"
            f"hosts = 127.0.0.1:{port}\n"
            "[auth]\n"
            "type = none\n"
            "[storage]\n"
            f"filesystem_folder = {os.path.join(workdir, 'storage')}\n"
        )

    proc = subprocess.Popen(
        [sys.executable, "-m", "radicale", "--config", config_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                if requests.get(url, timeout=1).status_code in (200, 401, 404):
                    break
            except requests.RequestException:
                time.sleep(0.2)
        else:
            raise RuntimeError("Radicale test server did not start in time")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(workdir, ignore_errors=True)


@pytest.fixture
async def repo(radicale_url):
    """Repository on a fresh, unique collection of the test Radicale server."""
    repository = RadicaleTaskRepository(url=radicale_url, collection=f"test-{uuid4().hex[:8]}")
    await repository.initialize()
    yield repository
    await repository.close()


def _task(title: str, **kwargs) -> Task:
    return Task(title=title, **kwargs)


async def test_create_and_get_task_round_trip(repo):
    task = _task(
        "Acheter du lait",
        description="2 litres",
        due_date="2026-12-31 23:59:59",
        priority=Priority.HIGH,
    )

    created = await repo.create(task)
    fetched = await repo.get_by_id(str(created.id))

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Acheter du lait"
    assert fetched.description == "2 litres"
    assert fetched.due_date == "2026-12-31 23:59:59"
    assert fetched.priority == Priority.HIGH
    assert fetched.status == TaskStatus.PENDING


async def test_get_unknown_task_returns_none(repo):
    assert await repo.get_by_id(str(uuid4())) is None


async def test_list_filters_and_sorting(repo):
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    tasks = [
        _task("due today", due_date=f"{today} 10:00:00", priority=Priority.LOW),
        _task("overdue", due_date=yesterday, priority=Priority.CRITICAL),
        _task("done", status=TaskStatus.COMPLETED),
    ]
    for task in tasks:
        await repo.create(task)

    all_tasks, total = await repo.list_all()
    assert total == 3
    # due_date ASC first: overdue (yesterday) then today; the one without a
    # due date sorts first like the SQLite backend (NULLs first).
    assert [t.title for t in all_tasks] == ["done", "overdue", "due today"]

    pending, pending_total = await repo.list_all(status="pending")
    assert pending_total == 2
    assert {t.title for t in pending} == {"due today", "overdue"}

    critical, _ = await repo.list_all(priority="critical")
    assert [t.title for t in critical] == ["overdue"]

    today_tasks, _ = await repo.list_all(due_date="today")
    assert [t.title for t in today_tasks] == ["due today"]

    overdue_tasks, _ = await repo.list_all(due_date="overdue")
    assert [t.title for t in overdue_tasks] == ["overdue"]

    page, page_total = await repo.list_all(limit=1, offset=1)
    assert page_total == 3
    assert len(page) == 1


async def test_update_task(repo):
    task = await repo.create(_task("old title", priority=Priority.LOW))

    task.update(title="new title", priority=Priority.CRITICAL, status=TaskStatus.COMPLETED)
    updated = await repo.update(task)
    fetched = await repo.get_by_id(str(task.id))

    assert updated.title == "new title"
    assert fetched is not None
    assert fetched.title == "new title"
    assert fetched.priority == Priority.CRITICAL
    assert fetched.status == TaskStatus.COMPLETED


async def test_update_unknown_task_raises(repo):
    with pytest.raises(ValueError, match="not found"):
        await repo.update(_task("ghost", task_id=uuid4()))


async def test_delete_task(repo):
    task = await repo.create(_task("to delete"))

    assert await repo.delete(str(task.id)) is True
    assert await repo.get_by_id(str(task.id)) is None
    assert await repo.delete(str(task.id)) is False
