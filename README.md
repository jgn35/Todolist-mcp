# Todolist MCP Server

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A **Model Context Protocol (MCP)** server for task management. Built with Python 3.12+, FastMCP, SQLAlchemy, and SQLite.

## Features

- **Task Management**: Create, read, update, delete, and complete tasks
- **Filtering**: List tasks by status, priority, or due date
- **Authentication**: Secure token-based authentication
- **Persistence**: SQLite database for data storage
- **MCP Protocol**: Full MCP server implementation with 6 tools

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `create_task` | Create a new task with title, description, due date, and priority |
| `get_task` | Retrieve a task by its ID |
| `list_tasks` | List all tasks with optional filters (status, priority, due date) |
| `update_task` | Update task attributes (title, description, due date, priority, status) |
| `delete_task` | Delete a task by its ID |
| `complete_task` | Mark a task as completed |

## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/jgn35/Todolist-mcp.git
cd Todolist-mcp

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Generate Authentication Token

All MCP tools require a valid authentication token. Generate one first:

```bash
# Using uv
uv run todolist-mcp-generate-token

# Or with Python
python -m todolist_mcp.cli generate-token

# Or directly
python -c "from todolist_mcp.infrastructure.auth_adapter.token_manager import TokenManager; print(TokenManager().generate_token())"
```

**Important**: Save the generated token. You'll need it for all MCP tool calls.

### Run the Server

```bash
# Using uv
uv run todolist-mcp

# Or with Python
python -m todolist_mcp

# Or directly
python -c "from todolist_mcp import main; main()"
```

The server will start and listen on stdin/stdout for MCP requests.

## Usage Examples

### Using MCP Client

```python
import asyncio
from mcp import Client

async def main():
    client = Client(command="uv run todolist-mcp")
    await client.connect()
    
    token = "YOUR_GENERATED_TOKEN"
    
    # Create a task
    task = await client.call_tool("create_task", {
        "title": "Learn MCP",
        "description": "Understand Model Context Protocol",
        "priority": "high",
        "token": token
    })
    print(f"Created task: {task['id']}")
    
    # List tasks
    result = await client.call_tool("list_tasks", {"token": token})
    print(f"Total tasks: {result['total']}")
    
    await client.disconnect()

asyncio.run(main())
```

### Direct Tool Calls

```python
from todolist_mcp import mcp
import asyncio

async def example():
    token = "YOUR_GENERATED_TOKEN"
    
    # Create task
    task = await mcp.create_task(
        title="Test Task",
        description="A test task",
        priority="high",
        token=token
    )
    print(f"Created: {task}")
    
    # List tasks
    result = await mcp.list_tasks(token=token)
    print(f"Tasks: {result['tasks']}")

asyncio.run(example())
```

## Project Structure

```
todolist-mcp/
├── src/
│   └── todolist_mcp/
│       ├── __init__.py           # MCP server entry point & tool definitions
│       ├── cli.py                # Command-line interface for token management
│       ├── domain/
│       │   ├── __init__.py
│       │   └── entities.py        # Task, Priority, TaskStatus entities
│       ├── application/
│       │   ├── __init__.py
│       │   ├── use_cases/         # Clean Architecture use cases
│       │   │   ├── __init__.py
│       │   │   ├── create_task.py
│       │   │   ├── get_task.py
│       │   │   ├── list_tasks.py
│       │   │   ├── update_task.py
│       │   │   ├── delete_task.py
│       │   │   └── complete_task.py
│       │   └── services/
│       │       └── auth_service.py
│       └── infrastructure/
│           ├── __init__.py
│           ├── sqlite_adapter/    # SQLite persistence
│           │   ├── __init__.py
│           │   ├── models.py      # SQLAlchemy models
│           │   └── repository.py  # TaskRepository implementation
│           └── auth_adapter/     # Authentication
│               ├── __init__.py
│               ├── models.py
│               └── token_manager.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   └── test_entities.py
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── test_create_task.py
│   │       ├── test_get_task.py
│   │       ├── test_list_tasks.py
│   │       ├── test_update_task.py
│   │       ├── test_delete_task.py
│   │       ├── test_complete_task.py
│   │       └── test_create_task_missing_title.py
│   └── integration/
│       ├── __init__.py
│       ├── test_mcp_tools_integration.py
│       └── mcp_tools/
│           └── __init__.py
├── pyproject.toml                 # Project configuration
├── AGENTS.md                      # Project context for agents
└── LICENSE                        # MIT License
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TODOLIST_MCP_DB_PATH` | Path to SQLite database | `~/.todolist-mcp/todolist.db` |
| `TODOLIST_MCP_TOKEN_PATH` | Path to token file | `~/.todolist-mcp/token.txt` |

### Token Storage

Tokens are stored in `~/.todolist-mcp/token.txt` by default. The directory is created automatically on first run.

## Development

### Setup Development Environment

```bash
# Install development dependencies
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/application/test_create_task.py

# Run integration tests
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=src/todolist_mcp --cov-report=term-missing
```

### Linting & Type Checking

```bash
# Run linter (Ruff)
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Run type checker (Pyright)
uv run pyright
```

### Code Formatting

This project uses Ruff for linting. Configure your editor to use:
- Line length: 100 characters
- Python version: 3.12

## Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│              MCP Server                  │  ← FastMCP tools
├─────────────────────────────────────────┤
│           Application Layer               │  ← Use cases
├─────────────────────────────────────────┤
│             Domain Layer                  │  ← Entities & interfaces
├─────────────────────────────────────────┤
│          Infrastructure Layer             │  ← SQLite, Auth
└─────────────────────────────────────────┘
```

### Data Flow

```
MCP Request → Auth Validation → Use Case → Repository → SQLite
```

## Task Entity

```python
from todolist_mcp.domain.entities import Task, Priority, TaskStatus

task = Task(
    title="My Task",
    description="Task description",
    due_date="2026-12-31 23:59:59",
    priority=Priority.HIGH,
    status=TaskStatus.PENDING
)
```

### Priority Levels

- `low` - Low priority
- `medium` - Medium priority (default)
- `high` - High priority

### Status Values

- `pending` - Task is pending (default)
- `completed` - Task is completed
- `cancelled` - Task is cancelled

## Filtering Tasks

The `list_tasks` tool supports various filters:

### Status Filter

```python
# List only pending tasks
list_tasks(status="pending", token=token)

# List completed tasks
list_tasks(status="completed", token=token)
```

### Priority Filter

```python
# List high priority tasks
list_tasks(priority="high", token=token)
```

### Due Date Filter

```python
# List tasks due today
list_tasks(due_date="today", token=token)

# List tasks due tomorrow
list_tasks(due_date="tomorrow", token=token)

# List overdue tasks
list_tasks(due_date="overdue", token=token)

# List tasks in date range
list_tasks(due_date="2026-08-01..2026-08-31", token=token)

# List tasks due on specific date
list_tasks(due_date="2026-12-31", token=token)
```

### Pagination

```python
# Get first 10 tasks
list_tasks(limit=10, offset=0, token=token)

# Get next 10 tasks
list_tasks(limit=10, offset=10, token=token)
```

## Error Handling

All tools raise `ValueError` with descriptive messages for:

- Invalid or missing authentication token
- Missing required fields (e.g., title for create_task)
- Invalid field values (e.g., invalid priority)
- Task not found
- Attempting to modify a completed task

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests and linting:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run pyright
   ```
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

### Pull Request Guidelines

- Follow existing code style
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/ModelContextProtocol/fastmcp)
- Uses [SQLAlchemy](https://www.sqlalchemy.org/) for ORM
- Uses [Pydantic](https://pydantic.dev/) for data validation
- Testing with [pytest](https://docs.pytest.org/)
- Linting with [Ruff](https://github.com/astral-sh/ruff)
- Type checking with [Pyright](https://github.com/microsoft/pyright)
