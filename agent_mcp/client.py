"""MCP client for calling search and memory tools."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Optional

from config import settings
from agent_mcp.protocol import decode_message, encode_message

PROJECT_ROOT = Path(__file__).parent.parent


class MCPClient:
    """Call MCP tools via in-process registry or stdio subprocess."""

    def __init__(self, transport: Optional[str] = None) -> None:
        self.transport = transport or settings.mcp_transport
        self._processes: dict[str, subprocess.Popen] = {}
        self._locks: dict[str, threading.Lock] = {
            "search": threading.Lock(),
            "memory": threading.Lock(),
        }
        self._request_id = 0

    def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Optional[dict[str, Any]] = None,
    ) -> Any:
        if self.transport == "stdio":
            return self._call_tool_stdio(server, tool_name, arguments or {})
        return self._call_tool_inprocess(server, tool_name, arguments or {})

    def _call_tool_inprocess(
        self,
        server: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        if server == "search":
            from mcp_servers.search_server import search_mcp

            result = search_mcp.call_tool(tool_name, arguments)
        elif server == "memory":
            from mcp_servers.memory_server import memory_mcp

            result = memory_mcp.call_tool(tool_name, arguments)
        else:
            raise ValueError(f"Unknown MCP server: {server}")

        if result.get("isError"):
            content = result.get("content", [])
            message = content[0]["text"] if content else "MCP tool error"
            raise RuntimeError(message)

        content = result.get("content", [])
        if not content:
            return None

        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _call_tool_stdio(
        self,
        server: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        script = PROJECT_ROOT / "mcp_servers" / f"{server}_server.py"
        lock = self._locks[server]

        with lock:
            process = self._get_process(server, script)
            self._request_id += 1
            request_id = self._request_id

            initialize_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "ci-agent", "version": "1.0.0"},
                },
            }
            self._send(process, initialize_request)
            self._read_response(process, request_id)

            self._send(
                process,
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
            )

            self._request_id += 1
            call_id = self._request_id
            call_request = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
            self._send(process, call_request)
            response = self._read_response(process, call_id)

        result = response.get("result", {})
        if result.get("isError"):
            content = result.get("content", [])
            message = content[0]["text"] if content else "MCP tool error"
            raise RuntimeError(message)

        content = result.get("content", [])
        if not content:
            return None

        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _get_process(self, server: str, script: Path) -> subprocess.Popen:
        if server in self._processes and self._processes[server].poll() is None:
            return self._processes[server]

        process = subprocess.Popen(
            [sys.executable, str(script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            text=False,
        )
        self._processes[server] = process
        return process

    def _send(self, process: subprocess.Popen, message: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("MCP server stdin is not available")
        process.stdin.write(encode_message(message))
        process.stdin.flush()

    def _read_response(self, process: subprocess.Popen, request_id: int) -> dict[str, Any]:
        if process.stdout is None:
            raise RuntimeError("MCP server stdout is not available")

        while True:
            line = process.stdout.readline()
            if not line:
                stderr = ""
                if process.stderr is not None:
                    stderr = process.stderr.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"MCP server exited unexpectedly. stderr: {stderr}")

            message = decode_message(line.decode("utf-8").strip())
            if message.get("id") == request_id:
                if "error" in message:
                    error = message["error"]
                    raise RuntimeError(error.get("message", "MCP error"))
                return message

    def close(self) -> None:
        for process in self._processes.values():
            if process.poll() is None:
                process.terminate()
        self._processes.clear()


_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
