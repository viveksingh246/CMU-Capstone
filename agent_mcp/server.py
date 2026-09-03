"""Minimal MCP server implementation for stdio transport."""

from __future__ import annotations

import inspect
import sys
import traceback
from typing import Any, Callable, Optional

from agent_mcp.protocol import (
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    ToolDefinition,
    decode_message,
    encode_message,
    make_error,
    make_response,
    parse_tool_arguments,
    tool_result_error,
    tool_result_text,
)


class MCPServer:
    """Register tools and serve them over MCP stdio transport."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._tools: dict[str, Callable[..., Any]] = {}
        self._tool_defs: dict[str, ToolDefinition] = {}

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or func.__name__
            tool_description = description or (func.__doc__ or "").strip().split("\n")[0]
            schema = _build_input_schema(func)
            self._tools[tool_name] = func
            self._tool_defs[tool_name] = ToolDefinition(
                name=tool_name,
                description=tool_description,
                input_schema=schema,
            )
            return func

        return decorator

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self._tool_defs.values()
        ]

    def call_tool(self, name: str, arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if name not in self._tools:
            return tool_result_error(f"Unknown tool: {name}")

        func = self._tools[name]
        args = parse_tool_arguments(arguments)
        try:
            result = func(**_filter_kwargs(func, args))
            return tool_result_text(result)
        except Exception as exc:
            return tool_result_error(f"{type(exc).__name__}: {exc}")

    def handle_request(self, message: dict[str, Any]) -> Optional[dict[str, Any]]:
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            return make_response(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": self.name, "version": SERVER_VERSION},
                },
            )

        if method == "notifications/initialized":
            return None

        if method == "ping":
            return make_response(request_id, {})

        if method == "tools/list":
            return make_response(request_id, {"tools": self.list_tools()})

        if method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments")
            return make_response(request_id, self.call_tool(name, arguments))

        if request_id is not None:
            return make_error(request_id, -32601, f"Method not found: {method}")
        return None

    def run_stdio(self) -> None:
        """Run the MCP server reading/writing newline-delimited JSON on stdio."""
        stdin = sys.stdin.buffer
        stdout = sys.stdout.buffer

        while True:
            line = stdin.readline()
            if not line:
                break

            try:
                message = decode_message(line.decode("utf-8").strip())
                response = self.handle_request(message)
                if response is not None:
                    stdout.write(encode_message(response))
                    stdout.flush()
            except Exception:
                traceback.print_exc(file=sys.stderr)


def _build_input_schema(func: Callable[..., Any]) -> dict[str, Any]:
    sig = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in {"self", "cls"}:
            continue

        annotation = param.annotation
        json_type = "string"
        if annotation in (int, "int"):
            json_type = "integer"
        elif annotation in (float, "float"):
            json_type = "number"
        elif annotation in (bool, "bool"):
            json_type = "boolean"
        elif annotation in (dict, "dict"):
            json_type = "object"
        elif annotation in (list, "list"):
            json_type = "array"

        properties[param_name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _filter_kwargs(func: Callable[..., Any], arguments: dict[str, Any]) -> dict[str, Any]:
    sig = inspect.signature(func)
    allowed = {
        name
        for name, param in sig.parameters.items()
        if name not in {"self", "cls"}
    }
    return {key: value for key, value in arguments.items() if key in allowed}
