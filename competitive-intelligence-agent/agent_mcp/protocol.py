"""MCP JSON-RPC protocol helpers (stdio transport, newline-delimited JSON)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "competitive-intelligence-agent"
SERVER_VERSION = "1.0.0"


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


def make_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def make_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def encode_message(message: dict[str, Any]) -> bytes:
    return (json.dumps(message, ensure_ascii=True) + "\n").encode("utf-8")


def decode_message(line: str) -> dict[str, Any]:
    return json.loads(line)


def tool_result_text(payload: Any) -> dict[str, Any]:
    """Wrap a Python object as MCP tool result content."""
    if isinstance(payload, str):
        text = payload
    else:
        text = json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": text}], "isError": False}


def tool_result_error(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def parse_tool_arguments(arguments: Optional[dict[str, Any]]) -> dict[str, Any]:
    return arguments or {}
