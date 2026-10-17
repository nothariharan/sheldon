"""Claim and lease. One winner. A non-owner cannot heartbeat or complete."""

import pytest

from sheldon.coordination.board import claim_task, complete_task, handoff_task, heartbeat
from sheldon.db import connect
from sheldon.schema import TaskStatus

GRAPH = "test_claim_lease"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - a failed write may leave no graph
        pass


def _task(graph: str, task_id: str = "T-9") -> None:
    connect().select_graph(graph).query(
        "CREATE (:Task {id: $id, status: $status, version: 0})",
        {"id": task_id, "status": TaskStatus.OPEN.value},
    )


def _row(graph: str, task_id: str = "T-9") -> list:
    return connect().select_graph(graph).query(
        "MATCH (t:Task {id: $id}) RETURN t.status, t.owner, t.lease_expires",
        {"id": task_id},
    ).result_set[0]


def test_one_agent_wins_the_open_task(graph: str) -> None:
    _task(graph)
    assert claim_task(graph, "T-9", "a", now_ms=1_000, ttl_ms=5_000) is True
    assert claim_task(graph, "T-9", "b", now_ms=1_000, ttl_ms=5_000) is False
    assert _row(graph) == [TaskStatus.CLAIMED.value, "a", 6_000]


def test_a_non_owner_cannot_heartbeat_or_complete(graph: str) -> None:
    _task(graph)
    assert claim_task(graph, "T-9", "a", now_ms=1_000, ttl_ms=5_000) is True
    assert heartbeat(graph, "T-9", "b", now_ms=2_000, ttl_ms=5_000) is False
    assert complete_task(graph, "T-9", "b") is False
    assert handoff_task(graph, "T-9", "b", "c", "note") is False
    assert _row(graph) == [TaskStatus.CLAIMED.value, "a", 6_000]


def test_the_owner_can_extend_and_complete(graph: str) -> None:
    _task(graph)
    claim_task(graph, "T-9", "a", now_ms=1_000, ttl_ms=5_000)
    assert heartbeat(graph, "T-9", "a", now_ms=2_000, ttl_ms=9_000) is True
    assert _row(graph)[2] == 11_000
    assert complete_task(graph, "T-9", "a") is True
    assert _row(graph)[0] == TaskStatus.DONE.value


def test_an_unfinished_dependency_blocks_the_claim(graph: str) -> None:
    _task(graph, "T-1")
    _task(graph, "T-9")
    connect().select_graph(graph).query(
        "MATCH (t:Task {id: 'T-9'}), (d:Task {id: 'T-1'}) CREATE (t)-[:DEPENDS_ON]->(d)"
    )
    assert claim_task(graph, "T-9", "a", now_ms=1_000, ttl_ms=5_000) is False
    assert _row(graph)[0] == TaskStatus.OPEN.value
