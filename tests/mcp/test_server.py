"""Tests for sheldon.mcp.server.

Validates:
- TOOLS constant defines the required tool names.
- call_tool dispatches to preflight, recall, claim, refute, and resume.
- Preflight via MCP blocks INC-12 TTL retry on the seed graph.
- Unknown tool invocation raises ValueError.
- Full MCP stdio JSON-RPC 2.0 lifecycle:
  - initialize handshake
  - notifications/initialized handling
  - tools/list schema discovery
  - tools/call execution and content formatting
  - JSON-RPC error responses for unknown methods
"""

import json
from collections.abc import Generator

import pytest

from sheldon.db import connect
from sheldon.mcp.server import (
    TOOLS,
    call_tool,
    handle_jsonrpc,
)
from sheldon.seed.snapshot import load_seed

SEED_GRAPH = "test_mcp_seed"


@pytest.fixture(scope="module")
def seed_graph() -> Generator[str, None, None]:
    db = connect()
    g = db.select_graph(SEED_GRAPH)
    try:
        g.delete()
    except Exception:
        pass
    load_seed(SEED_GRAPH)
    yield SEED_GRAPH
    try:
        g.delete()
    except Exception:
        pass


def test_tools_constant_has_required_tools() -> None:
    expected = {"preflight", "recall", "claim", "refute", "resume", "sheldon_run", "claim_done"}
    assert set(TOOLS) == expected


def test_call_tool_preflight_blocks_ttl_retry(seed_graph: str) -> None:
    res = call_tool(
        "preflight",
        {
            "graph": seed_graph,
            "command": "edit checkout/cache.py",
            "paths": ["checkout/cache.py"],
        },
    )
    assert res["decision"] == "block"
    assert "E-41" in res["evidence_ids"]
    assert "C-5" in res["claim_ids"]


def test_call_tool_preflight_allows_clean_action(seed_graph: str) -> None:
    res = call_tool(
        "preflight",
        {
            "graph": seed_graph,
            "command": "edit checkout/api.py",
            "paths": ["checkout/api.py"],
        },
    )
    assert res["decision"] == "ok"


def test_call_tool_recall_dispatches(seed_graph: str) -> None:
    res = call_tool(
        "recall",
        {
            "graph": seed_graph,
            "pr": 7,
        },
    )
    assert "rows" in res
    assert isinstance(res["rows"], list)


def test_call_tool_claim_dispatches(seed_graph: str) -> None:
    res = call_tool(
        "claim",
        {
            "graph": seed_graph,
            "task_id": "T-9",
            "agent_id": "agent-mcp-1",
            "now_ms": 1000,
            "ttl_ms": 30000,
        },
    )
    assert "claimed" in res
    assert res["task_id"] == "T-9"


def test_call_tool_refute_dispatches(seed_graph: str) -> None:
    res = call_tool(
        "refute",
        {
            "graph": seed_graph,
            "claim_id": "C-7",
            "evidence_ids": ["E-60"],
            "agent_id": "agent-mcp-2",
            "model": "test-model",
            "session": "test-session",
        },
    )
    assert "refuted" in res
    assert res["claim_id"] == "C-7"


def test_call_tool_resume_dispatches(seed_graph: str) -> None:
    res = call_tool(
        "resume",
        {
            "graph": seed_graph,
            "agent_id": "agent-mcp-1",
        },
    )
    assert set(res) == {"tried", "failed", "believed", "next"}
    assert "C-5" in [f["id"] for f in res["failed"]]


def test_call_tool_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown tool"):
        call_tool("unsupported_tool", {})


# ==============================================================================
# MCP Protocol Handshake & Lifecycle Tests
# ==============================================================================


def test_jsonrpc_initialize() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    resp = handle_jsonrpc(req)
    assert resp is not None
    assert resp["id"] == 1
    assert "protocolVersion" in resp["result"]
    assert "tools" in resp["result"]["capabilities"]
    assert resp["result"]["serverInfo"]["name"] == "sheldon-mcp"


def test_jsonrpc_initialized_notification() -> None:
    req = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    resp = handle_jsonrpc(req)
    assert resp is None


def test_jsonrpc_tools_list() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    resp = handle_jsonrpc(req)
    assert resp is not None
    assert resp["id"] == 2
    tools = resp["result"]["tools"]
    names = [t["name"] for t in tools]
    assert set(names) == {
        "preflight",
        "recall",
        "claim",
        "refute",
        "resume",
        "sheldon_run",
        "claim_done",
    }
    for t in tools:
        assert "inputSchema" in t
        assert t["inputSchema"]["type"] == "object"


def test_jsonrpc_tools_call_success(seed_graph: str) -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "preflight",
            "arguments": {
                "graph": seed_graph,
                "command": "edit checkout/cache.py",
                "paths": ["checkout/cache.py"],
            },
        },
    }
    resp = handle_jsonrpc(req)
    assert resp is not None
    assert resp["id"] == 3
    content = resp["result"]["content"][0]
    assert content["type"] == "text"
    parsed = json.loads(content["text"])
    assert parsed["decision"] == "block"
    assert resp["result"]["isError"] is False


def test_jsonrpc_unknown_method_error() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "unknown/method",
        "params": {},
    }
    resp = handle_jsonrpc(req)
    assert resp is not None
    assert resp["id"] == 4
    assert resp["error"]["code"] == -32601
