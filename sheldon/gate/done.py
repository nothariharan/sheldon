"""W3 done/fixed claim.

Status: built. `tests/gate/test_done.py` shows a done claim returning no
approval unless it cites a passing executed test run on that sha. The same
write refuses when the claim is refuted or reaches a refuted claim within
the W2 hop window. The path is a separate read.
"""

import argparse
import os
import sys

from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.evidence.run import TEST_RUN
from sheldon.gate.approve import format_path, refusal_path
from sheldon.gate.closed import raise_if_closed
from sheldon.output import CommandResult, emit
from sheldon.schema import ApprovalStatus, HypothesisStatus

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
    """Return the approval id, or None when the write returns 0 rows."""
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
                "refuted": HypothesisStatus.REFUTED.value,
            },
        )
    except (ConnectionError, OSError) as exc:
        raise_if_closed("done", exc)
    if not rows:
        return None
    return str(rows[0]["id"])


def done_decision(
    graph: str,
    claim_id: str,
    head_sha: str,
    evidence_ids: list[str],
    model: str,
    session: str,
) -> dict[str, object]:
    """Mark a claim done, then explain a refuted-ancestor refusal."""
    approval = claim_done(graph, claim_id, head_sha, evidence_ids, model, session)
    if approval is not None:
        return {
            "id": approval,
            "claim_ids": [],
            "edge_types": [],
            "evidence": None,
            "reason": "",
        }
    path = refusal_path(graph, claim_id)
    claim_ids = path["claim_ids"]
    edge_types = path["edge_types"]
    evidence = path["evidence"]
    reason = "refused"
    if isinstance(claim_ids, list) and claim_ids:
        reason = format_path(
            [str(item) for item in claim_ids],
            [str(item) for item in edge_types] if isinstance(edge_types, list) else [],
            str(evidence) if evidence else None,
        )
    return {
        "id": None,
        "claim_ids": claim_ids,
        "edge_types": edge_types,
        "evidence": evidence,
        "reason": reason,
    }


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    """CLI for one done claim. Exit 2 when the write returns no row."""
    parser = argparse.ArgumentParser(description="Mark a claim done against the graph")
    parser.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon:demo"))
    parser.add_argument("--claim", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--evidence", action="append", default=None)
    parser.add_argument("--model", default="")
    parser.add_argument("--session", default="")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    decision = done_decision(
        args.graph,
        claim_id=args.claim,
        head_sha=args.sha,
        evidence_ids=list(args.evidence or []),
        model=args.model,
        session=args.session,
    )
    refused = decision["id"] is None
    text = str(decision["reason"]) if refused else f"done {decision['id']}"
    result = CommandResult(
        command="claim_done",
        exit_code=2 if refused else 0,
        data=decision,
        text=text,
        stream="stderr" if refused else "stdout",
    )
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    sys.exit(main())
