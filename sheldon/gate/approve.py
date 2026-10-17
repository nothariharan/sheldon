"""W1 approval write.

Status: built. `tests/gate/test_approve.py` shows the graph refusing a bad
citation and writing one FOR plus two CITES. Python does not filter the ids.
"""

from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.schema import ApprovalStatus


def _write(graph: str, name: str, params: dict) -> list[dict]:
    result = connect().select_graph(graph).query(load_query(name), params)
    rows = result.result_set or []
    if not rows:
        return []
    columns = [column for _, column in result.header]
    return [dict(zip(columns, row)) for row in rows]


def approve(
    graph: str,
    pr_number: int,
    head_sha: str,
    approval_id: str,
    evidence_ids: list[str],
    by: str,
    actor_kind: str,
    model: str,
    session: str,
) -> str | None:
    """Return the approval id, or None when the write returns 0 rows."""
    rows = _write(
        graph,
        "approve_pr",
        {
            "pr": pr_number,
            "sha": head_sha,
            "ids": evidence_ids,
            "aid": approval_id,
            "by": by,
            "kind": actor_kind,
            "model": model,
            "session": session,
            "status": ApprovalStatus.ACTIVE.value,
        },
    )
    if not rows:
        return None
    return str(rows[0]["id"])
