"""Claim and lease.

Status: to build. These functions are not working features.
``resume`` lives in ``resume.py`` so another owner can edit it.
"""

# Flip to False in the PR that runs queries/claim_task.cypher.
# tests/test_races.py becomes a hard check when this is False.
CLAIM_IS_STUB = True


def claim_task(graph: str, task_id: str, agent_id: str, now_ms: int, ttl_ms: int) -> bool:
    """To build. Return True for the agent that won the lease."""
    del graph, task_id, agent_id, now_ms, ttl_ms
    if CLAIM_IS_STUB:
        raise NotImplementedError("P4: queries/claim_task.cypher")


def heartbeat(graph: str, task_id: str, agent_id: str, now_ms: int, ttl_ms: int) -> bool:
    """To build. Extend the lease when this agent holds it."""
    del graph, task_id, agent_id, now_ms, ttl_ms
    raise NotImplementedError("P4: queries/heartbeat.cypher")


def complete_task(graph: str, task_id: str, agent_id: str) -> bool:
    """To build. Close the task when this agent holds it."""
    del graph, task_id, agent_id
    raise NotImplementedError("P4: queries/complete_task.cypher")


def handoff_task(graph: str, task_id: str, agent_id: str, to_agent: str, note: str) -> bool:
    """To build. Pass the task when this agent holds it."""
    del graph, task_id, agent_id, to_agent, note
    raise NotImplementedError("P4: queries/handoff_task.cypher")

