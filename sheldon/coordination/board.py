"""P4. Task board on the same graph as the memory.

Claim, heartbeat, complete, and handoff are each one conditional write.
``resume`` is a read. The refute gate lives in sheldon.belief, not here.
"""

# Flip to False in the PR that runs queries/claim_task.cypher.
# tests/test_races.py becomes a hard check when this is False.
CLAIM_IS_STUB = True


def claim_task(graph: str, task_id: str, agent_id: str, now_ms: int, ttl_ms: int) -> bool:
    """Return True only for the agent that won the lease."""
    del graph, task_id, agent_id, now_ms, ttl_ms
    if CLAIM_IS_STUB:
        raise NotImplementedError("P4: queries/claim_task.cypher")


def heartbeat(graph: str, task_id: str, agent_id: str, now_ms: int, ttl_ms: int) -> bool:
    """Extend the lease only when this agent holds it."""
    del graph, task_id, agent_id, now_ms, ttl_ms
    raise NotImplementedError("P4: queries/heartbeat.cypher")


def complete_task(graph: str, task_id: str, agent_id: str) -> bool:
    del graph, task_id, agent_id
    raise NotImplementedError("P4: queries/complete_task.cypher")


def handoff_task(graph: str, task_id: str, agent_id: str, to_agent: str, note: str) -> bool:
    del graph, task_id, agent_id, to_agent, note
    raise NotImplementedError("P4: queries/handoff_task.cypher")


def resume(graph: str, agent_id: str) -> dict:
    """Tried, failed, believed, next. Each item cites event ids."""
    del graph, agent_id
    raise NotImplementedError("P4: queries/resume_state.cypher")
