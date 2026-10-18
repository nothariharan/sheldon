"""One scripted agent session over MCP, on the real seed graph."""

import json
import os
from collections.abc import Generator

import pytest

from sheldon.db import connect
from sheldon.mcp.server import handle_jsonrpc
from sheldon.schema import ApprovalStatus
from sheldon.seed.snapshot import load_seed

GRAPH = "test_mcp_e2e"
CHILD = "SHELDON_MCP_E2E_CHILD"


@pytest.fixture()
def seed_graph() -> Generator[str, None, None]:
    if os.environ.get(CHILD) == "1":
        pytest.skip("child pytest started by sheldon_run")
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    load_seed(GRAPH)
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def _tool(name: str, arguments: dict, req_id: int) -> dict:
    response = handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    assert response is not None
    assert response["result"]["isError"] is False
    return json.loads(response["result"]["content"][0]["text"])


def test_a_scripted_session_blocks_then_records_a_run_then_claims_done(seed_graph: str) -> None:
    blocked = _tool(
        "preflight",
        {
            "graph": seed_graph,
            "command": "edit checkout/cache.py",
            "paths": ["checkout/cache.py"],
        },
        1,
    )
    assert blocked["decision"] == "block"
    assert "E-41" in blocked["evidence_ids"]

    connect().select_graph(seed_graph).query(
        "CREATE (:Claim {id: $id, kind: $kind, status: $status})",
        {"id": "C-done", "kind": "done", "status": "open"},
    )

    held = {key: os.environ.pop(key) for key in list(os.environ) if key.startswith("PYTEST_")}
    os.environ[CHILD] = "1"
    try:
        recorded = _tool(
            "sheldon_run",
            {
                "graph": seed_graph,
                "cmd": ["pytest"],
                "model": "opus",
                "session": "s-e2e",
            },
            2,
        )
    finally:
        os.environ.pop(CHILD, None)
        os.environ.update(held)

    assert recorded["exit_code"] == 0
    evidence_id = recorded["id"]
    executed, exit_code, command = connect().select_graph(seed_graph).query(
        "MATCH (e:Evidence {id: $id}) RETURN e.executed, e.exit_code, e.command",
        {"id": evidence_id},
    ).result_set[0]
    assert executed is True
    assert exit_code == 0
    assert command == "pytest"

    claimed = _tool(
        "claim_done",
        {
            "graph": seed_graph,
            "claim_id": "C-done",
            "head_sha": recorded["sha"],
            "evidence_ids": [evidence_id],
            "model": "opus",
            "session": "s-e2e",
        },
        3,
    )
    assert claimed["approval_id"] == "A-C-done"
    approval_id, status = connect().select_graph(seed_graph).query(
        "MATCH (a:Approval {id: $aid})-[:FOR]->(:Claim {id: 'C-done'}) "
        "MATCH (a)-[:CITES]->(:Evidence {id: $eid}) "
        "RETURN a.id, a.status",
        {"aid": "A-C-done", "eid": evidence_id},
    ).result_set[0]
    assert approval_id == "A-C-done"
    assert status == ApprovalStatus.ACTIVE.value
