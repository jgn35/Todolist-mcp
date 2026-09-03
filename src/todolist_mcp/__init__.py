"""
Todolist MCP Server Entry Point

FastMCP-based server for task management via MCP protocol.
Implements all 13 Functional Requirements from PRD.
Updated workflow triggers.
"""

import os

from fastmcp import FastMCP

from todolist_mcp.infrastructure.auth_adapter.bearer_verifier import BearerTokenVerifier

# Initialize FastMCP server with Bearer token auth for HTTP transport
mcp = FastMCP(name="todolist-mcp", version="0.1.0", auth=BearerTokenVerifier())

# Global repository instance (initialized on first use)
_task_repository = None


async def get_repository():
    """Get or initialize the task repository."""
    global _task_repository
    if _task_repository is None:
        from todolist_mcp.infrastructure.sqlite_adapter.repository import SQLiteTaskRepository
        _task_repository = SQLiteTaskRepository()
        await _task_repository.initialize()
    return _task_repository


@mcp.tool()
async def create_task(
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
) -> dict:
    """
    Create a new task.

    Args:
        title: Task title (required)
        description: Task description (optional)
        due_date: Due date in YYYY-MM-DD HH:MM:SS format (optional)
        priority: Priority level (low, medium, high) (optional)

    Returns:
        dict: Created task with id, title, description, due_date, priority, status, created_at, updated_at

    Raises:
        ValueError: If title is missing
    """
    if not title:
        raise ValueError("Title is required")

    from todolist_mcp.application.use_cases.create_task import CreateTaskUseCase

    repo = await get_repository()
    use_case = CreateTaskUseCase(repo)

    task = await use_case.execute(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
    )

    return task.to_dict()


@mcp.tool()
async def get_task(
    task_id: str,
) -> dict:
    """
    Get a task by ID.

    Args:
        task_id: Task UUID

    Returns:
        dict: Task details

    Raises:
        ValueError: If task not found
    """
    from todolist_mcp.application.use_cases.get_task import GetTaskUseCase

    repo = await get_repository()
    use_case = GetTaskUseCase(repo)

    try:
        task = await use_case.execute(task_id=task_id)
        return task.to_dict()
    except ValueError as e:
        raise ValueError(f"Task not found: {e}")


@mcp.tool()
async def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict:
    """
    List tasks with optional filters.

    Args:
        status: Filter by status (pending, completed, cancelled)
        priority: Filter by priority (low, medium, high)
        due_date: Filter by due date (YYYY-MM-DD, today, tomorrow, overdue, or range like 2026-08-31..2026-09-02)
        limit: Maximum number of tasks to return (default 50)
        offset: Pagination offset (default 0)

    Returns:
        dict: List of tasks and pagination info
    """
    from datetime import datetime

    from todolist_mcp.application.use_cases.list_tasks import ListTasksUseCase

    repo = await get_repository()
    use_case = ListTasksUseCase(repo)

    # Parse due_date filter
    parsed_due_date = None
    if due_date:
        due_date_lower = due_date.lower()
        if due_date_lower == "today":
            parsed_due_date = datetime.now().strftime("%Y-%m-%d")
        elif due_date_lower == "tomorrow":
            from datetime import timedelta

            parsed_due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif due_date_lower == "overdue":
            # Handle overdue in the use case
            parsed_due_date = "overdue"
        elif ".." in due_date:
            # Range - handle in use case
            parsed_due_date = due_date
        else:
            parsed_due_date = due_date

    result = await use_case.execute(
        status=status,
        priority=priority,
        due_date=parsed_due_date,
        limit=limit or 50,
        offset=offset or 0,
    )

    return {
        "tasks": [task.to_dict() for task in result.tasks],
        "total": result.total,
        "limit": result.limit,
        "offset": result.offset,
    }


@mcp.tool()
async def update_task(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
    status: str | None = None,
) -> dict:
    """
    Update a task.

    Args:
        task_id: Task UUID
        title: New title (optional)
        description: New description (optional)
        due_date: New due date (optional)
        priority: New priority (optional)
        status: New status (optional)

    Returns:
        dict: Updated task

    Raises:
        ValueError: If task not found or task is completed
    """
    from todolist_mcp.application.use_cases.update_task import UpdateTaskUseCase

    repo = await get_repository()
    use_case = UpdateTaskUseCase(repo)

    try:
        task = await use_case.execute(
            task_id=task_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
        )
        return task.to_dict()
    except ValueError as e:
        raise ValueError(str(e))


@mcp.tool()
async def delete_task(
    task_id: str,
) -> dict:
    """
    Delete a task.

    Args:
        task_id: Task UUID

    Returns:
        dict: Confirmation message

    Raises:
        ValueError: If task not found
    """
    from todolist_mcp.application.use_cases.delete_task import DeleteTaskUseCase

    repo = await get_repository()
    use_case = DeleteTaskUseCase(repo)

    try:
        await use_case.execute(task_id=task_id)
        return {"message": f"Task {task_id} deleted successfully"}
    except ValueError as e:
        raise ValueError(str(e))


@mcp.tool()
async def complete_task(
    task_id: str,
) -> dict:
    """
    Mark a task as completed.

    Args:
        task_id: Task UUID

    Returns:
        dict: Updated task

    Raises:
        ValueError: If task not found or task is already completed
    """
    from todolist_mcp.application.use_cases.complete_task import CompleteTaskUseCase

    repo = await get_repository()
    use_case = CompleteTaskUseCase(repo)

    try:
        task = await use_case.execute(task_id=task_id)
        return task.to_dict()
    except ValueError as e:
        raise ValueError(str(e))


def main():
    """Run the MCP server, or dispatch a CLI subcommand (generate-token, run)."""
    import sys

    # Delegate CLI subcommands to the dedicated CLI entry point (FR-13).
    if len(sys.argv) > 1 and sys.argv[1] in ("generate-token", "run"):
        from todolist_mcp.cli import main as cli_main
        cli_main()
        return

    import argparse

    parser = argparse.ArgumentParser(
        description="Todolist MCP Server - Task management via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  todolist-mcp                    Start server with stdio transport (default)
  todolist-mcp --transport http   Start server with HTTP transport on port 8080
  todolist-mcp --transport both   Start server with both stdio and HTTP transports
  todolist-mcp --port 8000        Start HTTP server on port 8000
  todolist-mcp --host 0.0.0.0     Start server listening on all interfaces
  todolist-mcp --host 192.168.1.1 Start server listening on specific IP
        """
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "both"],
        default=os.environ.get("TODOLIST_MCP_TRANSPORT", "stdio"),
        help="Transport protocol: stdio (default), http, or both"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("TODOLIST_MCP_HTTP_PORT", "8080")),
        help="HTTP port when using http or both transport (default: 8080)"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("TODOLIST_MCP_HOST"),
        help="Host IP address to listen on (default: from TODOLIST_MCP_HOST env var, or 127.0.0.1 for stdio, 0.0.0.0 for http/both)"
    )

    args = parser.parse_args()

    # Ensure database directory exists
    db_path = (
        os.environ.get("TODOLIST_MCP_DB_PATH")
        or os.path.expanduser("~/.todolist-mcp/todolist.db")
    )
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    print("Todolist MCP Server")
    print("=" * 40)
    print(f"Transport mode: {args.transport}")
    if args.transport in ["http", "both"]:
        print(f"HTTP host: {args.host}")
        print(f"HTTP port: {args.port}")
    print("Server is ready to handle MCP requests")
    print("\nAvailable tools:")
    print("  - create_task")
    print("  - get_task")
    print("  - list_tasks")
    print("  - update_task")
    print("  - delete_task")
    print("  - complete_task")

    # Run the server using FastMCP's native transport
    # stdio does not accept a port argument; http/both need port and host
    # Resolve host: CLI arg > env var > default based on transport
    host = args.host or os.environ.get("TODOLIST_MCP_HOST", "127.0.0.1" if args.transport == "stdio" else "0.0.0.0")
    if args.transport == "stdio":
        mcp.run(transport=args.transport)
    else:
        mcp.run(transport=args.transport, host=host, port=args.port)


if __name__ == "__main__":
    main()
