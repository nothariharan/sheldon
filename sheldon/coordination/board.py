"""Claim and lease.

Status: built. `tests/coordination/test_claim.py` and the claim race show
one winner, and a non-owner cannot heartbeat or complete.
``resume`` lives in ``resume.py`` so another owner can edit it.
"""

from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.schema import TaskStatus

# tests/test_races.py is a hard check while this is False.
CLAIM_IS_STUB = False


def _write(graph: str, name: str, params: dict) -> list[dict]:
    result = connect().select_graph(graph).query(load_query(name), params)
    rows = result.result_set or []
    if not rows:
        return []
    columns = [column for _, column in result.header]
    return [dict(zip(columns, row)) for row in rows]


def claim_task(graph: str, task_id: str, agent_id: str, now_ms: int, ttl_ms: int) -> bool:
    """Return True for the agent that won the lease."""
    rows = _write(
        graph,
        "claim_task",
        {
            "task_id": task_id,
            "agent_id": agent_id,
            "now": now_ms,
            "ttl": ttl_ms,
            "open": TaskStatus.OPEN.value,
            "claimed": TaskStatus.CLAIMED.value,
            "done": TaskStatus.DONE.value,
        },
    )
    return len(rows) == 1


def heartbeat(graph: str, task_id: str, agent_id: str, now_ms: int, ttl_ms: int) -> bool:
    """Extend the lease when this agent holds it."""
    rows = _write(
        graph,
        "heartbeat",
        {
            "task_id": task_id,
            "agent_id": agent_id,
            "now": now_ms,
            "ttl": ttl_ms,
            "claimed": TaskStatus.CLAIMED.value,
        },
    )
    return len(rows) == 1


def complete_task(graph: str, task_id: str, agent_id: str) -> bool:
    """Close the task when this agent holds it."""
    rows = _write(
        graph,
        "complete_task",
        {
            "task_id": task_id,
            "agent_id": agent_id,
            "claimed": TaskStatus.CLAIMED.value,
            "done": TaskStatus.DONE.value,
        },
    )
    return len(rows) == 1


def handoff_task(graph: str, task_id: str, agent_id: str, to_agent: str, note: str) -> bool:
    """Pass the task when this agent holds it. The note is not stored yet."""
    del to_agent, note
    rows = _write(
        graph,
        "handoff_task",
        {
            "task_id": task_id,
            "agent_id": agent_id,
            "open": TaskStatus.OPEN.value,
        },
    )
    return len(rows) == 1
