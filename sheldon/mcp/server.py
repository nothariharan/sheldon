"""Tool names the host will call.

Status: built.
Hosted http is roadmap. Stdio server provides standard JSON-RPC 2.0 MCP protocol.
"""

import json
import sys
from typing import Any

from sheldon.belief.refute import refute_claim
from sheldon.coordination.board import claim_task
from sheldon.preflight import preflight
from sheldon.retrieval.recall import recall

TOOLS: tuple[str, ...] = ("preflight", "recall", "claim", "refute", "resume")

MCP_TOOL_DEFINITIONS = [
    {
        "name": "preflight",
        "description": "Preflight check before tool execution to prevent retrying refuted fixes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graph": {"type": "string", "description": "FalkorDB graph key"},
                "command": {"type": "string", "description": "Proposed action command"},
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Touched file paths",
                },
                "override": {"type": "boolean", "description": "Manual override flag"},
            },
            "required": ["graph", "command"],
        },
    },
    {
        "name": "recall",
        "description": "Recall incidents and prior evidence for PR changed files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graph": {"type": "string", "description": "FalkorDB graph key"},
                "pr": {"type": "integer", "description": "Pull request number"},
            },
            "required": ["graph", "pr"],
        },
    },
    {
        "name": "claim",
        "description": "Claim a task lease atomically.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graph": {"type": "string", "description": "FalkorDB graph key"},
                "task_id": {"type": "string", "description": "Task identifier"},
                "agent_id": {"type": "string", "description": "Claiming agent ID"},
                "now_ms": {"type": "integer", "description": "Service timestamp in ms"},
                "ttl_ms": {"type": "integer", "description": "Lease duration in ms"},
            },
            "required": ["graph", "task_id", "agent_id"],
        },
    },
    {
        "name": "refute",
        "description": "Refute claim and stale dependent approvals and tasks in one atomic write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graph": {"type": "string", "description": "FalkorDB graph key"},
                "claim_id": {"type": "string", "description": "Claim identifier to refute"},
                "evidence_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Executed refuting evidence IDs",
                },
                "agent_id": {"type": "string", "description": "Refuting agent ID"},
                "model": {"type": "string", "description": "Model identifier"},
                "session": {"type": "string", "description": "Session identifier"},
            },
            "required": ["graph", "claim_id", "evidence_ids"],
        },
    },
    {
        "name": "resume",
        "description": "Read task state, attempted actions, failed attempts, and believed claims.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graph": {"type": "string", "description": "FalkorDB graph key"},
                "agent_id": {"type": "string", "description": "Agent identifier"},
            },
            "required": ["graph", "agent_id"],
        },
    },
]


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the owning module. Do not reimplement the gate here."""
    if name not in TOOLS:
        raise ValueError(f"unknown tool {name!r}. known: {', '.join(TOOLS)}")

    graph = arguments.get("graph", "")

    if name == "preflight":
        command = arguments.get("command", "")
        paths = arguments.get("paths") or []
        override = bool(arguments.get("override", False))
        return preflight(graph, command, paths, override=override)

    if name == "recall":
        pr_number = int(arguments.get("pr", 0))
        return {"rows": recall(graph, pr_number)}

    if name == "claim":
        task_id = str(arguments.get("task_id", ""))
        agent_id = str(arguments.get("agent_id", ""))
        now_ms = int(arguments.get("now_ms", 0))
        ttl_ms = int(arguments.get("ttl_ms", 30000))
        won = claim_task(graph, task_id, agent_id, now_ms=now_ms, ttl_ms=ttl_ms)
        return {"claimed": won, "task_id": task_id, "agent_id": agent_id}

    if name == "refute":
        claim_id = str(arguments.get("claim_id", ""))
        evidence_ids = list(arguments.get("evidence_ids") or [])
        agent_id = str(arguments.get("agent_id", "mcp-agent"))
        model = str(arguments.get("model", "unknown-model"))
        session = str(arguments.get("session", "unknown-session"))
        alpha = float(arguments.get("alpha", 0.0))
        staled = refute_claim(
            graph,
            claim_id,
            evidence_ids,
            agent_id=agent_id,
            model=model,
            session=session,
            alpha=alpha,
        )
        return {"refuted": staled, "claim_id": claim_id, "evidence_ids": evidence_ids}

    if name == "resume":
        agent_id = str(arguments.get("agent_id", ""))
        from sheldon.coordination.resume import resume

        return resume(graph, agent_id)

    raise ValueError(f"unhandled tool {name!r}")


def handle_jsonrpc(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single MCP JSON-RPC 2.0 message."""
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    # Initialized notification (no response needed)
    if method == "notifications/initialized":
        return None

    if req_id is None:
        # Unknown notification, ignore
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sheldon-mcp", "version": "0.1.0"},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": MCP_TOOL_DEFINITIONS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments") or {}
        try:
            res = call_tool(tool_name, args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res)}],
                    "isError": False,
                },
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error calling tool {tool_name}: {exc}"}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def run_stdio_server() -> None:
    """Run MCP server over standard I/O (JSON Lines)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_jsonrpc(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
