"""Tests for MCP protocol and tool servers."""

import json

from agent_mcp.client import MCPClient
from agent_mcp.server import MCPServer
from mcp_servers.memory_server import memory_mcp
from mcp_servers.search_server import search_mcp


def test_search_mcp_lists_tools():
    tools = search_mcp.list_tools()
    tool_names = {tool["name"] for tool in tools}
    assert "search_web_tool" in tool_names
    assert "search_news_tool" in tool_names
    assert "search_github_tool" in tool_names
    assert "search_jobs_tool" in tool_names


def test_memory_mcp_lists_tools():
    tools = memory_mcp.list_tools()
    tool_names = {tool["name"] for tool in tools}
    assert "get_previous_findings" in tool_names
    assert "persist_research_run" in tool_names
    assert "list_research_runs" in tool_names


def test_search_mcp_call_web_tool():
    result = search_mcp.call_tool("search_web_tool", {"query": "Snowflake pricing", "max_results": 2})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert isinstance(payload, list)
    assert len(payload) <= 2


def test_mcp_client_inprocess_search():
    client = MCPClient(transport="inprocess")
    payload = client.call_tool(
        "search",
        "search_web_tool",
        {"query": "Databricks AI", "max_results": 2},
    )
    assert isinstance(payload, list)
    assert len(payload) <= 2


def test_mcp_initialize_handshake():
    server = MCPServer("test-server")

    @server.tool()
    def echo(message: str) -> str:
        return message

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        }
    )
    assert response is not None
    assert response["result"]["serverInfo"]["name"] == "test-server"


def test_mcp_tool_call_via_server_handler():
    response = search_mcp.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_web_tool",
                "arguments": {"query": "Snowflake pricing", "max_results": 1},
            },
        }
    )
    assert response is not None
    assert response["result"]["isError"] is False
    payload = json.loads(response["result"]["content"][0]["text"])
    assert isinstance(payload, list)
    assert len(payload) <= 1
