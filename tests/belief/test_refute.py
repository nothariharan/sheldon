"""W2. One write refutes C-7 and stales A-3 and T-9. Nothing is deleted."""

import pytest

from sheldon.belief.refute import refute_claim
from sheldon.db import connect
from sheldon.schema import ApprovalStatus, HypothesisStatus, TaskStatus

GRAPH = "test_w2_cascade"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(
        "CREATE (c:Claim {id: 'C-7', status: 'open', confidence: 1.0}),"
        "(e:Evidence {id: 'E-41', executed: true}),"
        "(bad:Evidence {id: 'E-bad', executed: false}),"
        "(a:Approval {id: 'A-3', status: 'active'})-[:RELIES_ON]->(c),"
        "(t:Task {id: 'T-9', status: 'open'})-[:DEPENDS_ON]->(c),"
        "(t2:Task {id: 'T-2', status: 'claimed'})-[:DEPENDS_ON]->(t),"
        "(other:Claim {id: 'C-8', status: 'open'})-[:RELIES_ON]->(c)"
    )
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def _nodes(graph: str) -> int:
    return connect().select_graph(graph).query("MATCH (n) RETURN count(n)").result_set[0][0]


def test_one_call_refutes_c7_and_stales_a3_and_t9(graph: str) -> None:
    before = _nodes(graph)
    assert refute_claim(graph, "C-7", ["E-41"], agent_id="a", model="opus", session="s1") is True
    rows = connect().select_graph(graph).query(
        "MATCH (n) WHERE n.id IN ['C-7', 'A-3', 'T-9', 'T-2', 'C-8'] "
        "RETURN n.id, n.status ORDER BY n.id"
    ).result_set
    assert rows == [
        ["A-3", ApprovalStatus.STALE.value],
        ["C-7", HypothesisStatus.REFUTED.value],
        ["C-8", HypothesisStatus.OPEN.value],
        ["T-2", ApprovalStatus.STALE.value],
        ["T-9", ApprovalStatus.STALE.value],
    ]
    assert _nodes(graph) >= before


def test_missing_or_unexecuted_evidence_changes_nothing(graph: str) -> None:
    assert refute_claim(graph, "C-7", ["E-41", "missing"], "a", "opus", "s1") is False
    assert refute_claim(graph, "C-7", ["E-bad"], "a", "opus", "s1") is False
    assert refute_claim(graph, "C-7", [], "a", "opus", "s1") is False
    rows = connect().select_graph(graph).query(
        "MATCH (n) WHERE n.id IN ['C-7', 'A-3', 'T-9'] RETURN n.id, n.status ORDER BY n.id"
    ).result_set
    assert rows == [
        ["A-3", ApprovalStatus.ACTIVE.value],
        ["C-7", "open"],
        ["T-9", TaskStatus.OPEN.value],
    ]
