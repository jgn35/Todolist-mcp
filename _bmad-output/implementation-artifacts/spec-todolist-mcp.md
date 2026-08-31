---
title: 'Todolist MCP Server Implementation'
type: 'feature'
created: '2026-08-31'
status: 'done'
review_loop_iteration: 0
baseline_commit: '6f8d660'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Todolist MCP server needs to be fully implemented to enable LLM-based task management via MCP protocol. Current state has domain entities and basic structure but lacks complete MCP tool integration, proper async database operations, and authentication.

**Approach:** Implement all 13 Functional Requirements from PRD using Hexagonal Architecture pattern. Domain layer defines entities and repository interfaces, application layer contains use cases, infrastructure layer provides SQLite persistence and MCP server implementation. Follow AD-1 through AD-8 architectural decisions.

## Boundaries & Constraints

**Always:**
- Follow Hexagonal Architecture: Domain has zero dependencies, dependencies flow inward (Infrastructure -> Application -> Domain)
- All MCP tools must be async and registered with proper schemas
- Use UUID v4 for all task IDs (server-generated, client-provided IDs ignored)
- All dates use local machine timezone in YYYY-MM-DD HH:MM:SS format
- SQLite persistence via SQLAlchemy ORM with aiosqlite for async support
- Token-based authentication mandatory for all MCP tool calls
- Database location: ~/.todolist-mcp/todolist.db

**Ask First:**
- Any changes to database schema after initial implementation
- Modifications to authentication mechanism
- Changes to MCP tool signatures

**Never:**
- Multi-user support (v1 is mono-user only)
- Direct HTTP, CLI, or other protocol access bypassing MCP
- REST API or direct CLI commands (except token generation)
- Advanced filtering beyond basic status/priority/due_date
- Automatic token rotation
- Task limits or rate limiting

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Create task with valid data | title="Test", description="Desc", priority="high", due_date="2026-12-31 12:00:00" | Returns task with generated UUID, status="pending", created_at and updated_at set | N/A |
| Create task with missing title | title=null | Returns error: title is required | 400 Bad Request |
| Get existing task | task_id=valid_uuid | Returns complete task object | N/A |
| Get non-existent task | task_id=invalid_uuid | Returns error: Task not found | 404 Not Found |
| List tasks with no filters | None | Returns all tasks, paginated (default limit=50, offset=0) | N/A |
| List tasks with status filter | status="completed" | Returns only completed tasks | N/A |
| Update task with valid data | task_id=valid, title="Updated" | Returns updated task with new updated_at | N/A |
| Update completed task | task_id=valid, status="completed" | Returns error: Cannot update completed task | 400 Bad Request |
| Delete existing task | task_id=valid | Returns confirmation message | N/A |
| Delete non-existent task | task_id=invalid | Returns error: Task not found | 404 Not Found |
| Complete task | task_id=valid | Returns task with status="completed" | N/A |
| Complete already completed task | task_id=valid, status="completed" | Returns error: Task already completed | 400 Bad Request |
| Missing authentication token | Any tool call without token | Returns error: Unauthorized | 401 Unauthorized |
| Invalid authentication token | Any tool call with invalid token | Returns error: Unauthorized | 401 Unauthorized |

</frozen-after-approval>

## Code Map

- `src/todolist_mcp/__init__.py` -- MCP server entry point with FastMCP, registers all tools (create_task, get_task, list_tasks, update_task, delete_task, complete_task)
- `src/todolist_mcp/domain/entities.py` -- Task entity with Priority and TaskStatus enums, UUID v4 generation, timestamp management
- `src/todolist_mcp/domain/repositories.py` -- TaskRepository abstract interface (create, get_by_id, list_all, update, delete)
- `src/todolist_mcp/application/use_cases/create_task.py` -- CreateTaskUseCase: validates input, creates Task entity, persists via repository
- `src/todolist_mcp/application/use_cases/get_task.py` -- GetTaskUseCase: retrieves single task by ID, raises ValueError if not found
- `src/todolist_mcp/application/use_cases/list_tasks.py` -- ListTasksUseCase: lists tasks with optional filters (status, priority, due_date), returns paginated results
- `src/todolist_mcp/application/use_cases/update_task.py` -- UpdateTaskUseCase: retrieves existing task, applies updates, prevents updates to completed tasks
- `src/todolist_mcp/application/use_cases/delete_task.py` -- DeleteTaskUseCase: deletes task by ID, raises ValueError if not found
- `src/todolist_mcp/application/use_cases/complete_task.py` -- CompleteTaskUseCase: marks task as completed, raises ValueError if already completed
- `src/todolist_mcp/application/services/auth_service.py` -- AuthService: validates tokens via TokenManager
- `src/todolist_mcp/infrastructure/sqlite_adapter/models.py` -- SQLAlchemy models: TaskModel (tasks table), AuthTokenModel (auth_tokens table)
- `src/todolist_mcp/infrastructure/sqlite_adapter/repository.py` -- SQLiteTaskRepository: concrete implementation of TaskRepository interface using SQLAlchemy ORM and aiosqlite
- `src/todolist_mcp/infrastructure/auth_adapter/token_manager.py` -- TokenManager: generates, stores (hashed), and validates auth tokens using SQLite
- `src/todolist_mcp/infrastructure/auth_adapter/models.py` -- AuthTokenModel for token storage
- `pyproject.toml` -- Project configuration with dependencies (fastmcp, sqlalchemy, aiosqlite, pydantic)
- `tests/unit/domain/test_entities.py` -- Unit tests for domain entities (9 tests passing)

## Tasks & Acceptance

**Execution:**
- [ ] `src/todolist_mcp/__init__.py` -- Integrate FastMCP server with proper tool registration and async handling -- MCP protocol requires async tools
- [ ] `src/todolist_mcp/__init__.py` -- Add authentication middleware to validate tokens on all tool calls -- FR-12 requires mandatory token authentication
- [ ] `src/todolist_mcp/infrastructure/sqlite_adapter/repository.py` -- Fix async implementation to work with aiosqlite properly -- Current implementation needs async session management
- [ ] `src/todolist_mcp/infrastructure/auth_adapter/token_manager.py` -- Ensure token validation works with MCP headers -- Token must be extracted from MCP request
- [ ] `src/todolist_mcp/application/use_cases/list_tasks.py` -- Implement sorting by due_date ASC, then priority DESC -- FR-3 requires specific sorting order
- [ ] `src/todolist_mcp/application/use_cases/list_tasks.py` -- Implement date filter parsing (today, tomorrow, overdue, ranges) -- FR-10 requires advanced date filtering
- [ ] `src/todolist_mcp/application/use_cases/update_task.py` -- Add validation to prevent updates to completed tasks -- FR-4 requires this constraint
- [ ] `src/todolist_mcp/application/use_cases/complete_task.py` -- Add validation to prevent completing already completed tasks -- FR-6 requires this constraint
- [ ] `pyproject.toml` -- Add CLI entry point for token generation: todolist-mcp generate-token -- FR-13 requires CLI token generation
- [ ] `tests/unit/application/` -- Add unit tests for all use cases -- Currently only domain entities have tests
- [ ] `tests/integration/mcp_tools/` -- Add integration tests for MCP tools -- Verify tools work end-to-end

**Acceptance Criteria:**
- Given a valid task creation request with title, when create_task is called, then a task is persisted with UUID v4 ID, status="pending", and proper timestamps
- Given a request without authentication token, when any MCP tool is called, then a 401 Unauthorized error is returned
- Given a request with invalid authentication token, when any MCP tool is called, then a 401 Unauthorized error is returned
- Given a task with status="completed", when update_task is called with any changes, then a 400 Bad Request error is returned with message "Cannot update completed task"
- Given a task with status="completed", when complete_task is called, then a 400 Bad Request error is returned with message "Task already completed"
- Given a task with due_date matching today's date, when list_tasks is called with due_date="today", then the task appears in results
- Given 100 tasks with various due_dates and priorities, when list_tasks is called, then results are sorted by due_date ASC, then priority DESC
- Given valid CLI command execution, when todolist-mcp generate-token is run, then a new token is generated, displayed to user, and stored in database
- Given all unit and integration tests, when pytest is run with coverage, then all tests pass with >80% coverage (SM-4)

## Spec Change Log

## Design Notes

**Architecture Pattern:** Hexagonal Architecture (Clean Architecture / Ports & Adapters)
- Domain layer: Pure Python entities and interfaces, zero external dependencies
- Application layer: Use cases that orchestrate domain logic via repository interfaces
- Infrastructure layer: Adapters that implement interfaces (SQLite, MCP, Auth)

**Key Design Decisions:**
- UUID v4 for task IDs: Prevents collisions and predictable IDs (AD-7)
- Local timezone for dates: Simplifies single-user context, no timezone offset storage (AD-8)
- SQLite + SQLAlchemy ORM: Lightweight persistence for personal use (AD-4)
- Token in database: Single-user authentication with SQLite storage (AD-5)
- Async-first: All I/O operations use async/await pattern (AD-6)

**Database Schema:**
- tasks table: id (UUID), title, description, due_date, priority, status, created_at, updated_at
- auth_tokens table: id (UUID), token (hashed), created_at, expires_at

## Verification

**Commands:**
- `python -m pytest tests/ -v` -- expected: All tests pass
- `python -c "from todolist_mcp.domain.entities import Task; print(Task(title='Test').to_dict())"` -- expected: Valid task dict with UUID
- `python -m todolist_mcp` -- expected: MCP server starts without errors

**Manual checks:**
- Verify Hexagonal Architecture layers have correct dependency flow
- Verify all FR-1 through FR-13 are implemented
- Verify authentication works for all MCP tools

## Suggested Review Order

**MCP Server Entry Point**

- FastMCP server initialization with all 6 tools registered
  [`__init__.py:16`](../../src/todolist_mcp/__init__.py#L16)

- Authentication middleware for all tool calls
  [`__init__.py:28`](../../src/todolist_mcp/__init__.py#L28)

**Use Cases Implementation**

- Create task with validation and repository integration
  [`create_task.py:15`](../../src/todolist_mcp/application/use_cases/create_task.py#L15)

- Get task with error handling for non-existent tasks
  [`get_task.py:15`](../../src/todolist_mcp/application/use_cases/get_task.py#L15)

- List tasks with advanced filtering and sorting
  [`list_tasks.py:15`](../../src/todolist_mcp/application/use_cases/list_tasks.py#L15)

- Update task with completed task protection
  [`update_task.py:20`](../../src/todolist_mcp/application/use_cases/update_task.py#L20)

- Complete task with already completed protection
  [`complete_task.py:15`](../../src/todolist_mcp/application/use_cases/complete_task.py#L15)

**Infrastructure Layer**

- SQLite repository with advanced date filtering
  [`repository.py:50`](../../src/todolist_mcp/infrastructure/sqlite_adapter/repository.py#L50)

- Token manager for authentication
  [`token_manager.py:15`](../../src/todolist_mcp/infrastructure/auth_adapter/token_manager.py#L15)

**CLI Interface**

- Token generation command
  [`cli.py:15`](../../src/todolist_mcp/cli.py#L15)

**Tests**

- Domain entity tests (9 tests)
  [`test_entities.py:1`](../../tests/unit/domain/test_entities.py#L1)

- Application use case tests (19 tests)
  [`test_create_task.py:1`](../../tests/unit/application/test_create_task.py#L1)
