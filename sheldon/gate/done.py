"""W3 done/fixed claim.

Status: built. `tests/gate/test_done.py` shows a done claim returning no
approval unless it cites a passing executed test run on that sha.
"""

from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.evidence.run import TEST_RUN
from sheldon.gate.closed import raise_if_closed
from sheldon.schema import ApprovalStatus

# Claim kind from the plan. The test_run kind lives on the producer.
DONE = "done"


def _write(graph: str, name: str, params: dict) -> list[dict]:
    result = connect().select_graph(graph).query(load_query(name), params)
    rows = result.result_set or []
    if not rows:
        return []
    columns = [column for _, column in result.header]
    return [dict(zip(columns, row)) for row in rows]


def claim_done(
    graph: str,
    claim_id: str,
    head_sha: str,
    evidence_ids: list[str],
    model: str,
    session: str,
) -> str | None:
    """Return the approval id, or None when no passing executed run is cited."""
    try:
        rows = _write(
            graph,
            "claim_done",
            {
                "cid": claim_id,
                "done_kind": DONE,
                "ids": list(dict.fromkeys(evidence_ids)),
                "sha": head_sha,
                "test_run": TEST_RUN,
                "aid": f"A-{claim_id}",
                "status": ApprovalStatus.ACTIVE.value,
                "model": model,
                "session": session,
            },
        )
    except (ConnectionError, OSError) as exc:
        raise_if_closed("done", exc)
    if not rows:
        return None
    return str(rows[0]["id"])
