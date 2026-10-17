"""W2 refute plus stale cascade.

Status: built. `refute_claim` runs the statement in `queries/refute_claim.cypher`.
`refute_hypothesis` runs the older sketch. The race test covers that sketch.
"""

from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.schema import ApprovalStatus, HypothesisStatus, TaskStatus

# The race test is a hard check while this is False.
REFUTE_IS_STUB = False


def _write(graph: str, name: str, params: dict) -> list[dict]:
    result = connect().select_graph(graph).query(load_query(name), params)
    rows = result.result_set or []
    if not rows:
        return []
    columns = [column for _, column in result.header]
    return [dict(zip(columns, row)) for row in rows]


def refute_hypothesis(
    graph: str,
    hypothesis_id: str,
    evidence_ids: list[str],
    agent_id: str,
    at_ms: int,
) -> bool:
    """Return True when every cited evidence id matched.

    A missing id returns False and changes nothing. Nothing is deleted.
    """
    rows = _write(
        graph,
        "refute_hypothesis",
        {
            "hypothesis_id": hypothesis_id,
            "evidence_ids": evidence_ids,
            "refuted": HypothesisStatus.REFUTED.value,
            "confidence": None,
            "agent_id": agent_id,
            "at_ms": at_ms,
            "open": TaskStatus.OPEN.value,
        },
    )
    return len(rows) == 1


def refute_claim(
    graph: str,
    claim_id: str,
    evidence_ids: list[str],
    agent_id: str,
    model: str,
    session: str,
    alpha: float = 0.0,
) -> bool:
    """Return True when executed evidence refuted the claim and staled dependents."""
    rows = _write(
        graph,
        "refute_claim",
        {
            "cid": claim_id,
            "ids": evidence_ids,
            "refuted": HypothesisStatus.REFUTED.value,
            "alpha": alpha,
            "agent": agent_id,
            "model": model,
            "session": session,
            "stale": ApprovalStatus.STALE.value,
            "live": [
                ApprovalStatus.ACTIVE.value,
                TaskStatus.OPEN.value,
                TaskStatus.CLAIMED.value,
            ],
        },
    )
    return len(rows) == 1
