"""Tests for coordination resume read.

Contract:
- Dict has tried, failed, believed, and next, with ids.
- Refuted claims and hypotheses are preserved and never deleted.
- Service clock (now_ms) evaluates active vs expired leases.
- Stale tasks from W2 cascade are marked stale with stale_because.
- Completed tasks are excluded from next.
"""

from typing import Generator

import pytest

from sheldon.belief.refute import refute_claim
from sheldon.coordination.board import claim_task, complete_task
from sheldon.coordination.resume import resume
from sheldon.db import connect
from sheldon.schema import TaskStatus
from sheldon.seed import load_seed

GRAPH = "test_coord_resume"


def _drop(key: str) -> None:
    try:
        connect().select_graph(key).delete()
    except Exception:  # noqa: BLE001 - graph may not exist
        pass


@pytest.fixture()
def seed_graph() -> Generator[str, None, None]:
    _drop(GRAPH)
    load_seed(GRAPH)
    yield GRAPH
    _drop(GRAPH)


def test_resume_on_empty_graph() -> None:
    _drop("test_nonexistent_resume_graph")
    state = resume("test_nonexistent_resume_graph", agent_id="agent-1")
    assert state == {
        "tried": [],
        "failed": [],
        "believed": [],
        "next": [],
    }


def test_resume_on_seed_graph(seed_graph: str) -> None:
    state = resume(seed_graph, agent_id="agent-test", now_ms=1_000)

    # Check top-level keys
    assert set(state.keys()) == {"tried", "failed", "believed", "next"}

    # Tried: includes ACT-1
    tried_ids = [t["id"] for t in state["tried"]]
    assert "ACT-1" in tried_ids
    act1 = next(t for t in state["tried"] if t["id"] == "ACT-1")
    assert act1["cmd"] == "edit checkout/cache.py"
    assert act1["claim_id"] == "C-5"

    # Failed: includes C-5 citing E-41
    failed_ids = [f["id"] for f in state["failed"]]
    assert "C-5" in failed_ids
    c5 = next(f for f in state["failed"] if f["id"] == "C-5")
    assert c5["status"] == "refuted"
    assert "TTL" in c5["text"]
    assert "E-41" in c5["evidence_ids"]

    # Believed: includes C-7 citing E-30
    believed_ids = [b["id"] for b in state["believed"]]
    assert "C-7" in believed_ids
    c7 = next(b for b in state["believed"] if b["id"] == "C-7")
    assert c7["status"] == "open"
    assert c7["confidence"] == pytest.approx(0.7)
    assert "E-30" in c7["evidence_ids"]

    # Next: includes open task T-9
    next_ids = [n["id"] for n in state["next"]]
    assert "T-9" in next_ids
    t9 = next(n for n in state["next"] if n["id"] == "T-9")
    assert t9["status"] == TaskStatus.OPEN.value
    assert t9["stale"] is False
    assert t9["claimable"] is True
    assert t9["active"] is False


def test_resume_after_w2_refute_cascade(seed_graph: str) -> None:
    # Initially C-7 is believed and T-9 is not stale
    state_before = resume(seed_graph, agent_id="agent-1", now_ms=1_000)
    assert "C-7" in [b["id"] for b in state_before["believed"]]
    t9_before = next(n for n in state_before["next"] if n["id"] == "T-9")
    assert t9_before["stale"] is False

    # Execute W2 refute cascade: C-7 refuted by E-60 stales T-9
    ok = refute_claim(
        seed_graph,
        claim_id="C-7",
        evidence_ids=["E-60"],
        agent_id="ci",
        model="ci",
        session="CI-60",
    )
    assert ok is True

    state_after = resume(seed_graph, agent_id="agent-1", now_ms=2_000)

    # Refuted claim is still present; both C-5 and C-7 are in failed
    failed_ids = [f["id"] for f in state_after["failed"]]
    assert "C-5" in failed_ids
    assert "C-7" in failed_ids
    c7_failed = next(f for f in state_after["failed"] if f["id"] == "C-7")
    assert "E-60" in c7_failed["evidence_ids"]

    # C-7 is no longer in believed
    assert "C-7" not in [b["id"] for b in state_after["believed"]]

    # T-9 is marked stale with stale_because="C-7" and is not claimable
    t9_after = next(n for n in state_after["next"] if n["id"] == "T-9")
    assert t9_after["stale"] is True
    assert t9_after["stale_because"] == "C-7"
    assert t9_after["claimable"] is False


def test_resume_active_and_expired_leases(seed_graph: str) -> None:
    # Agent-A claims T-9 with 5s lease (expires at 6000)
    assert claim_task(seed_graph, "T-9", "agent-a", now_ms=1_000, ttl_ms=5_000) is True

    # Check state for Agent-A at now_ms=2000 (active lease)
    state_a = resume(seed_graph, agent_id="agent-a", now_ms=2_000)
    t9_a = next(n for n in state_a["next"] if n["id"] == "T-9")
    assert t9_a["active"] is True
    assert t9_a["owner"] == "agent-a"
    assert t9_a["claimable"] is False

    # Check state for Agent-B at now_ms=2000 (claimed by someone else)
    state_b = resume(seed_graph, agent_id="agent-b", now_ms=2_000)
    t9_b = next(n for n in state_b["next"] if n["id"] == "T-9")
    assert t9_b["active"] is False
    assert t9_b["claimable"] is False

    # Check state for Agent-B at now_ms=7000 (lease expired at 6000 -> claimable)
    state_b_expired = resume(seed_graph, agent_id="agent-b", now_ms=7_000)
    t9_b_exp = next(n for n in state_b_expired["next"] if n["id"] == "T-9")
    assert t9_b_exp["active"] is False
    assert t9_b_exp["claimable"] is True


def test_resume_excludes_completed_tasks(seed_graph: str) -> None:
    # Agent-A claims and completes T-9
    assert claim_task(seed_graph, "T-9", "agent-a", now_ms=1_000, ttl_ms=5_000) is True
    assert complete_task(seed_graph, "T-9", "agent-a") is True

    state = resume(seed_graph, agent_id="agent-a", now_ms=2_000)
    next_ids = [n["id"] for n in state["next"]]
    assert "T-9" not in next_ids


def test_resume_task_dependencies(seed_graph: str) -> None:
    # Create dependent task T-10 that depends on T-9
    db = connect()
    db.select_graph(seed_graph).query(
        "MATCH (t9:Task {id: 'T-9'}) "
        "CREATE (t10:Task {id: 'T-10', title: 'Deploy shard', status: 'open'})-[:DEPENDS_ON]->(t9)"
    )

    state = resume(seed_graph, agent_id="agent-1", now_ms=1_000)
    t10 = next(n for n in state["next"] if n["id"] == "T-10")
    # T-9 is open (not done), so T-10 has 1 blocker and is not claimable
    assert t10["blockers"] == 1
    assert t10["claimable"] is False
