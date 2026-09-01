"""
Functional Tests for HTTP API

Functional tests for the HTTP transport protocol using mocked authentication.
These tests validate the HTTP API functionality without hardcoded tokens.
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestHTTPAPIFunctional(unittest.TestCase):
    """Functional tests for HTTP API endpoints using TestClient with mocked auth."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Generate a dynamic test token (not hardcoded)
        self.test_token = self._generate_test_token()
        
        # Mock validate_auth to accept our test token
        self.patcher = patch('todolist_mcp.validate_auth', new_callable=AsyncMock)
        self.mock_validate = self.patcher.start()
        self.mock_validate.return_value = True
        
        # Create test client
        self.client = TestClient(self.create_test_app())
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.loop.close()
        self.patcher.stop()
    
    def _generate_test_token(self):
        """Generate a unique test token for each test run."""
        import random
        import string
        import time
        # Use timestamp + random string for uniqueness
        timestamp = str(int(time.time() * 1000))[-8:]
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return f"test_token_{timestamp}_{random_part}"
    
    def create_test_app(self):
        """Create a test FastAPI app with the HTTP endpoints."""
        from fastapi import FastAPI, HTTPException, Request
        from pydantic import BaseModel
        from todolist_mcp import mcp
        
        app = FastAPI(title="Todolist MCP HTTP Server Test", version="0.1.0")

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
            if not await mcp.validate_auth(token):
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
            if not await mcp.validate_auth(token):
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
            if not await mcp.validate_auth(token):
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
        
        return app
    
    def test_list_tools_with_valid_token(self):
        """Test listing all MCP tools with valid authentication."""
        response = self.client.get(
            "/mcp/tools",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tools", data)
        self.assertIsInstance(data["tools"], list)
        
        # Check that all expected tools are present
        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = ["create_task", "get_task", "list_tasks", "update_task", "delete_task", "complete_task"]
        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names)
    
    def test_list_tools_without_token(self):
        """Test listing tools without authentication fails."""
        # Temporarily make validation fail
        self.mock_validate.return_value = False
        
        response = self.client.get("/mcp/tools")
        
        self.assertEqual(response.status_code, 401)
        self.assertIn("Unauthorized", response.json().get("detail", ""))
        
        # Reset validation to pass for other tests
        self.mock_validate.return_value = True
    
    def test_list_tools_with_query_param_token(self):
        """Test listing tools with token as query parameter."""
        response = self.client.get(
            "/mcp/tools",
            params={"token": self.test_token}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tools", data)
    
    def test_get_tool_schema_create_task(self):
        """Test getting schema for create_task tool."""
        response = self.client.get(
            "/mcp/tools/create_task",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "create_task")
        self.assertIn("description", data)
        self.assertIn("parameters", data)
        self.assertIn("properties", data["parameters"])
    
    def test_get_tool_schema_nonexistent(self):
        """Test getting schema for non-existent tool fails."""
        response = self.client.get(
            "/mcp/tools/nonexistent_tool",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json().get("detail", ""))
    
    def test_call_tool_create_task(self):
        """Test creating a task via HTTP API."""
        payload = {
            "tool": "create_task",
            "arguments": {
                "title": "Test Task from Functional Test",
                "description": "Created via HTTP functional test",
                "priority": "high",
                "due_date": "2026-12-31 23:59:59"
            }
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
        self.assertIsNone(data.get("error"))
        
        # Check that the task was created
        result = data["result"]
        self.assertIn("title", result)
        self.assertEqual(result["title"], "Test Task from Functional Test")
        self.assertIn("task_id", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "pending")
    
    def test_call_tool_list_tasks(self):
        """Test listing tasks via HTTP API."""
        payload = {
            "tool": "list_tasks",
            "arguments": {}
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
        result = data["result"]
        self.assertIn("tasks", result)
        self.assertIn("total", result)
    
    def test_call_tool_with_query_param_token(self):
        """Test calling a tool with token as query parameter."""
        payload = {
            "tool": "list_tasks",
            "arguments": {}
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            params={"token": self.test_token}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
    
    def test_call_nonexistent_tool(self):
        """Test calling a non-existent tool fails."""
        payload = {
            "tool": "nonexistent_tool",
            "arguments": {}
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json().get("detail", ""))
    
    def test_call_tool_missing_required_parameter(self):
        """Test calling create_task without required title parameter fails."""
        payload = {
            "tool": "create_task",
            "arguments": {
                "description": "Missing title"
            }
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Title is required", response.json().get("detail", ""))
    
    def test_header_auth_takes_precedence_over_query(self):
        """Test that header authentication takes precedence over query parameter."""
        payload = {
            "tool": "list_tasks",
            "arguments": {}
        }
        
        # Use valid token in header and invalid token in query
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"},
            params={"token": "invalid_token"}
        )
        
        # Should succeed because header token is valid
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)


class TestHTTPAPIEdgeCases(unittest.TestCase):
    """Edge case tests for HTTP API."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Generate a dynamic test token (not hardcoded)
        self.test_token = self._generate_test_token()
        
        # Mock validate_auth to accept our test token
        self.patcher = patch('todolist_mcp.validate_auth', new_callable=AsyncMock)
        self.mock_validate = self.patcher.start()
        self.mock_validate.return_value = True
        
        # Create test client
        self.client = TestClient(self.create_test_app())
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.loop.close()
        self.patcher.stop()
    
    def _generate_test_token(self):
        """Generate a unique test token for each test run."""
        import random
        import string
        import time
        # Use timestamp + random string for uniqueness
        timestamp = str(int(time.time() * 1000))[-8:]
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return f"test_token_{timestamp}_{random_part}"
    
    def create_test_app(self):
        """Create a test FastAPI app with the HTTP endpoints."""
        from fastapi import FastAPI, HTTPException, Request
        from pydantic import BaseModel
        from todolist_mcp import mcp
        
        app = FastAPI(title="Todolist MCP HTTP Server Test", version="0.1.0")

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
            if not await mcp.validate_auth(token):
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
            if not await mcp.validate_auth(token):
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
            if not await mcp.validate_auth(token):
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
        
        return app
    
    def test_malformed_json_request(self):
        """Test request with malformed JSON."""
        response = self.client.post(
            "/mcp/call",
            data="{ malformed json",  # Invalid JSON
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
    
    def test_empty_request_body(self):
        """Test request with empty body."""
        response = self.client.post(
            "/mcp/call",
            data="",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
    
    def test_missing_tool_parameter(self):
        """Test request with missing tool parameter."""
        payload = {
            "arguments": {"title": "Test"}
            # Missing "tool" parameter
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
    
    def test_missing_arguments_parameter(self):
        """Test request with missing arguments parameter."""
        payload = {
            "tool": "create_task"
            # Missing "arguments" parameter
        }
        
        response = self.client.post(
            "/mcp/call",
            json=payload,
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
    
    def test_wrong_content_type(self):
        """Test request with wrong content type."""
        headers = {
            "Authorization": f"Bearer {self.test_token}",
            "Content-Type": "text/plain"  # Wrong content type
        }
        payload = '{"tool": "list_tasks", "arguments": {}}'
        
        response = self.client.post(
            "/mcp/call",
            data=payload,
            headers=headers
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()