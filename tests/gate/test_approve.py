"""W1. The graph refuses a bad citation and writes one FOR and two CITES."""

import pytest

from sheldon.db import connect
from sheldon.gate.approve import approve
from sheldon.schema import ApprovalStatus

GRAPH = "test_w1_approve"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(
        "CREATE (:PR {number: 7, head_sha: 'abc'}),"
        "(:Evidence {id: 'E-1', executed: true, sha: 'abc'}),"
        "(:Evidence {id: 'E-2', executed: true, sha: 'abc'}),"
        "(:Evidence {id: 'E-off', executed: false, sha: 'abc'}),"
        "(:Evidence {id: 'E-old', executed: true, sha: 'old'})"
    )
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def _approve(graph: str, evidence_ids: list[str], approval_id: str = "A-1") -> str | None:
    return approve(
        graph,
        pr_number=7,
        head_sha="abc",
        approval_id=approval_id,
        evidence_ids=evidence_ids,
        by="hari",
        actor_kind="human",
        model="opus",
        session="s1",
    )


def _counts(graph: str) -> list:
    db = connect().select_graph(graph)

    def _count(statement: str) -> int:
        return db.query(statement).result_set[0][0]

    return [
        _count("MATCH (a:Approval) RETURN count(a)"),
        _count("MATCH ()-[f:FOR]->() RETURN count(f)"),
        _count("MATCH ()-[c:CITES]->() RETURN count(c)"),
    ]


def test_valid_ids_create_one_for_and_two_cites(graph: str) -> None:
    assert _approve(graph, ["E-1", "E-2"]) == "A-1"
    assert _counts(graph) == [1, 1, 2]
    status = connect().select_graph(graph).query(
        "MATCH (a:Approval {id: 'A-1'}) RETURN a.status, a.sha, a.model, a.session"
    ).result_set
    assert status == [[ApprovalStatus.ACTIVE.value, "abc", "opus", "s1"]]


def test_refuses_missing_unexecuted_empty_duplicate_and_wrong_sha(graph: str) -> None:
    assert _approve(graph, ["E-1", "missing"], "A-miss") is None
    assert _approve(graph, ["E-off"], "A-off") is None
    assert _approve(graph, [], "A-empty") is None
    assert _approve(graph, ["E-1", "E-1"], "A-dup") is None
    assert _approve(graph, ["E-old"], "A-old") is None
    assert _counts(graph) == [0, 0, 0]
