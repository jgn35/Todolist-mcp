"""
Todolist MCP Server Entry Point

FastMCP-based server for task management via MCP protocol.
Implements all 13 Functional Requirements from PRD.
Updated workflow triggers.
"""

import os

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(name="todolist-mcp", version="0.1.0")

# Global repository instance (initialized on first use)
_task_repository = None

# HTTP server instance
_http_app = None


async def get_repository():
    """Get or initialize the task repository."""
    global _task_repository
    if _task_repository is None:
        from todolist_mcp.infrastructure.sqlite_adapter.repository import SQLiteTaskRepository
        _task_repository = SQLiteTaskRepository()
        await _task_repository.initialize()
    return _task_repository


async def get_token_manager():
    """Get the token manager instance."""
    from todolist_mcp.infrastructure.auth_adapter.token_manager import TokenManager
    return TokenManager()


async def validate_auth(token: str | None = None) -> bool:
    """Validate authentication token."""
    if token is None:
        return False

    token_manager = await get_token_manager()
    return await token_manager.validate_token(token)


@mcp.tool()
async def create_task(
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
    token: str | None = None,
) -> dict:
    """
    Create a new task.

    Args:
        title: Task title (required)
        description: Task description (optional)
        due_date: Due date in YYYY-MM-DD HH:MM:SS format (optional)
        priority: Priority level (low, medium, high) (optional)
        token: Authentication token (required)

    Returns:
        dict: Created task with id, title, description, due_date, priority, status, created_at, updated_at

    Raises:
        ValueError: If title is missing or authentication fails
    """
    # Validate authentication
    if not await validate_auth(token):
        raise ValueError("Unauthorized - Invalid or missing authentication token")

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
    token: str | None = None,
) -> dict:
    """
    Get a task by ID.

    Args:
        task_id: Task UUID
        token: Authentication token (required)

    Returns:
        dict: Task details

    Raises:
        ValueError: If task not found or authentication fails
    """
    # Validate authentication
    if not await validate_auth(token):
        raise ValueError("Unauthorized - Invalid or missing authentication token")

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
    token: str | None = None,
) -> dict:
    """
    List tasks with optional filters.

    Args:
        status: Filter by status (pending, completed, cancelled)
        priority: Filter by priority (low, medium, high)
        due_date: Filter by due date (YYYY-MM-DD, today, tomorrow, overdue, or range like 2026-08-31..2026-09-02)
        limit: Maximum number of tasks to return (default 50)
        offset: Pagination offset (default 0)
        token: Authentication token (required)

    Returns:
        dict: List of tasks and pagination info

    Raises:
        ValueError: If authentication fails
    """
    # Validate authentication
    if not await validate_auth(token):
        raise ValueError("Unauthorized - Invalid or missing authentication token")

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
    token: str | None = None,
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
        token: Authentication token (required)

    Returns:
        dict: Updated task

    Raises:
        ValueError: If task not found, authentication fails, or task is completed
    """
    # Validate authentication
    if not await validate_auth(token):
        raise ValueError("Unauthorized - Invalid or missing authentication token")

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
    token: str | None = None,
) -> dict:
    """
    Delete a task.

    Args:
        task_id: Task UUID
        token: Authentication token (required)

    Returns:
        dict: Confirmation message

    Raises:
        ValueError: If task not found or authentication fails
    """
    # Validate authentication
    if not await validate_auth(token):
        raise ValueError("Unauthorized - Invalid or missing authentication token")

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
    token: str | None = None,
) -> dict:
    """
    Mark a task as completed.

    Args:
        task_id: Task UUID
        token: Authentication token (required)

    Returns:
        dict: Updated task

    Raises:
        ValueError: If task not found, authentication fails, or task is already completed
    """
    # Validate authentication
    if not await validate_auth(token):
        raise ValueError("Unauthorized - Invalid or missing authentication token")

    from todolist_mcp.application.use_cases.complete_task import CompleteTaskUseCase

    repo = await get_repository()
    use_case = CompleteTaskUseCase(repo)

    try:
        task = await use_case.execute(task_id=task_id)
        return task.to_dict()
    except ValueError as e:
        raise ValueError(str(e))


def main():
    """Run the MCP server."""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="Todolist MCP Server - Task management via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  todolist-mcp                    Start server with stdio transport (default)
  todolist-mcp --transport http   Start server with HTTP transport on port 8080
  todolist-mcp --transport both   Start server with both stdio and HTTP transports
  todolist-mcp --port 8000        Start HTTP server on port 8000
        """
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "both"],
        default="stdio",
        help="Transport protocol: stdio (default), http, or both"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port when using http or both transport (default: 8080)"
    )

    args = parser.parse_args()

    # Ensure database directory exists
    db_dir = os.path.expanduser("~/.todolist-mcp")
    os.makedirs(db_dir, exist_ok=True)

    print("Todolist MCP Server")
    print("=" * 40)
    print(f"Transport mode: {args.transport}")
    if args.transport in ["http", "both"]:
        print(f"HTTP port: {args.port}")
    print("Server is ready to handle MCP requests")
    print("\nAvailable tools:")
    print("  - create_task")
    print("  - get_task")
    print("  - list_tasks")
    print("  - update_task")
    print("  - delete_task")
    print("  - complete_task")
    print("\nNote: All tools require a valid 'token' parameter for authentication.")

    # Run the server based on transport mode
    if args.transport == "stdio":
        asyncio.run(mcp.run_stdio())
    elif args.transport == "http":
        run_http_server_sync(args.port)
    elif args.transport == "both":
        run_both_servers_sync(args.port)


def run_http_server_sync(port: int = 8080):
    """Run the MCP server with HTTP transport (synchronous)."""
    import uvicorn

    # Create the FastAPI app
    from fastapi import FastAPI, HTTPException, Request
    from pydantic import BaseModel

    app = FastAPI(title="Todolist MCP HTTP Server", version="0.1.0")

    class MCPRequest(BaseModel):
        tool: str
        arguments: dict

    class MCPResponse(BaseModel):
        result: dict | None = None
        error: str | None = None

    @app.get("/mcp/tools")
    async def list_tools(request: Request):
        """List all available MCP tools."""
        # Extract token from header or query param
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]
        else:
            token = request.query_params.get("token")

        # Validate auth
        if not await validate_auth(token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Get all tools from FastMCP
        tools = []
        for tool_name in mcp._tool_manager._tools:
            tool = mcp._tool_manager._tools[tool_name]
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_model.model_json_schema() if tool.args_model else {}
            })

        return {"tools": tools}

    @app.get("/mcp/tools/{tool_name}")
    async def get_tool_schema(tool_name: str, request: Request):
        """Get schema for a specific MCP tool."""
        # Extract token from header or query param
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]
        else:
            token = request.query_params.get("token")

        # Validate auth
        if not await validate_auth(token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Get tool from FastMCP
        if tool_name not in mcp._tool_manager._tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        tool = mcp._tool_manager._tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.args_model.model_json_schema() if tool.args_model else {}
        }

    @app.post("/mcp/call")
    async def call_tool(request: MCPRequest, http_request: Request):
        """Call an MCP tool via HTTP."""
        # Extract token from header or query param
        token = http_request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]
        else:
            token = http_request.query_params.get("token")

        # Validate auth
        if not await validate_auth(token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Get the tool
        tool_name = request.tool
        if tool_name not in mcp._tool_manager._tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        tool = mcp._tool_manager._tools[tool_name]

        try:
            # Call the tool with the provided arguments
            # Add token to arguments if not already present
            arguments = request.arguments.copy()
            if "token" not in arguments:
                arguments["token"] = token

            result = await tool.call(**arguments)
            return MCPResponse(result=result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)


async def run_http_server(port: int = 8080):
    """Run the MCP server with HTTP transport (async wrapper)."""
    run_http_server_sync(port)


def run_both_servers_sync(port: int = 8080):
    """Run the MCP server with both stdio and HTTP transports."""
    import asyncio
    import threading

    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server_sync, args=(port,))
    http_thread.daemon = True
    http_thread.start()

    # Run stdio server in main thread
    asyncio.run(mcp.run_stdio())

    # Clean up HTTP server
    # The thread will be terminated when main thread exits


if __name__ == "__main__":
    main()
