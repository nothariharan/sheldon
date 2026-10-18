"""W1 approval write.

Status: built. `tests/gate/test_approve.py` shows the graph refusing a bad
citation and writing one FOR plus two CITES. Python does not filter the ids.
A cited claim that is refuted, or that reaches a refuted claim within the
W2 hop window, refuses the same write. The path is a separate read.
"""

import argparse
import os
import sys

from sheldon.cypher import load_query
from sheldon.db import connect, read
from sheldon.output import CommandResult, emit
from sheldon.schema import ApprovalStatus, HypothesisStatus


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
    relies_on: str = "",
) -> str | None:
    """Return the approval id, or None when the write returns 0 rows.

    ``relies_on`` is a claim id this approval depends on. Empty means the
    approval cites evidence only. A cited claim that is refuted, or that
    reaches a refuted claim within the W2 hop window, refuses the write.
    """
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
            "cited": relies_on,
            "refuted": HypothesisStatus.REFUTED.value,
        },
    )
    if not rows:
        return None
    return str(rows[0]["id"])


def _as_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def format_path(claim_ids: list[str], edge_types: list[str], evidence: str | None) -> str:
    """Render claim ids, edge types, and the refuting evidence id."""
    pieces = [claim_ids[0]]
    for edge, claim_id in zip(edge_types, claim_ids[1:], strict=False):
        pieces.append(f"-[:{edge}]-> {claim_id}")
    body = " ".join(pieces)
    if evidence:
        return f"blocked: {body} refuted by {evidence}"
    return f"blocked: {body} refuted"


def refusal_path(graph: str, claim_id: str) -> dict[str, object]:
    """Read the shortest refuted-ancestor path. Empty when the claim is fine or missing."""
    rows = read(
        graph,
        "refuted_ancestor",
        {"id": claim_id, "refuted": HypothesisStatus.REFUTED.value},
    )
    if not rows:
        return {"claim_ids": [], "edge_types": [], "evidence": None}
    row = rows[0]
    evidence = row.get("evidence")
    return {
        "claim_ids": _as_list(row.get("claim_ids")),
        "edge_types": _as_list(row.get("edge_types")),
        "evidence": str(evidence) if evidence else None,
    }


def approve_decision(
    graph: str,
    pr_number: int,
    head_sha: str,
    approval_id: str,
    evidence_ids: list[str],
    by: str,
    actor_kind: str,
    model: str,
    session: str,
    relies_on: str = "",
) -> dict[str, object]:
    """Approve, then explain a refuted-ancestor refusal.

    ``id`` is the approval id, or None when the write returns 0 rows.
    A refuted ancestor adds ``claim_ids``, ``edge_types``, ``evidence``, and
    ``reason``. The write stays the decision. This read does not change it.
    """
    approval = approve(
        graph,
        pr_number,
        head_sha,
        approval_id,
        evidence_ids,
        by,
        actor_kind,
        model,
        session,
        relies_on=relies_on,
    )
    if approval is not None:
        return {
            "id": approval,
            "claim_ids": [],
            "edge_types": [],
            "evidence": None,
            "reason": "",
        }
    empty: dict[str, object] = {"claim_ids": [], "edge_types": [], "evidence": None}
    path = refusal_path(graph, relies_on) if relies_on else empty
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
    """CLI for one approval. Exit 2 when the write returns no row."""
    parser = argparse.ArgumentParser(description="Approve a PR against the graph")
    parser.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon:demo"))
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--evidence", action="append", default=None)
    parser.add_argument("--relies-on", default="")
    parser.add_argument("--by", default="cli")
    parser.add_argument("--actor-kind", default="human")
    parser.add_argument("--model", default="")
    parser.add_argument("--session", default="")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    decision = approve_decision(
        args.graph,
        pr_number=args.pr,
        head_sha=args.sha,
        approval_id=args.id,
        evidence_ids=list(args.evidence or []),
        by=args.by,
        actor_kind=args.actor_kind,
        model=args.model,
        session=args.session,
        relies_on=args.relies_on,
    )
    refused = decision["id"] is None
    text = str(decision["reason"]) if refused else f"approved {decision['id']}"
    result = CommandResult(
        command="approve",
        exit_code=2 if refused else 0,
        data=decision,
        text=text,
        stream="stderr" if refused else "stdout",
    )
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    sys.exit(main())
