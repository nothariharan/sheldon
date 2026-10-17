"""PR check decision.

Status: the decision and the check-run payload are wired and tested on a
fixture. The GitHub App webhook that calls them, and the HTTP call that posts
the payload, are to build. The decision is graph reads and Python. No LLM.
"""

from sheldon.db import read
from sheldon.retrieval import recall
from sheldon.schema import ApprovalStatus

CHECK_NAME = "sheldon"


def _cited_reason(row: dict, head_sha: str) -> str | None:
    if not row["found"]:
        return "missing"
    if row["executed"] is not True:
        return "not executed"
    if row["sha"] != head_sha:
        return f"ran on {row['sha']}, head is {head_sha}"
    if row["exit_code"] != 0:
        return f"exit code {row['exit_code']}"
    return None


def decide_check(
    graph: str,
    pr_number: int,
    head_sha: str,
    cited_evidence_ids: list[str] | None = None,
) -> dict:
    """Return the check decision for one PR head.

    ``cited_evidence_ids`` are the ids an agent cited on the PR, such as the
    evidence behind a "done, all tests pass" claim. Each must be an executed
    run on ``head_sha`` that exited 0.

    The check fails when a cited id does not hold, when an approval cites
    evidence that is not an executed run on this sha, or when the PR has
    approvals but none is active on this sha. A PR with no approval and
    nothing cited passes: the check is silent by default. A PR that is not in
    the graph yet is ``neutral``.

    Rows from R1 where a claim on a touched file was refuted go in
    ``refuted`` and turn on ``comment``. They inform. They do not fail the check.
    """
    decision = {
        "pr": pr_number,
        "head_sha": head_sha,
        "conclusion": "neutral",
        "blocked": [],
        "stale_approvals": [],
        "valid_approvals": [],
        "refuted": [],
        "comment": False,
    }
    approvals = read(graph, "check_approvals", {"pr": pr_number, "sha": head_sha})
    if not approvals:
        return decision

    ids = list(dict.fromkeys(cited_evidence_ids or []))
    if ids:
        for row in read(graph, "check_cited_evidence", {"ids": ids}):
            reason = _cited_reason(row, head_sha)
            if reason:
                decision["blocked"].append(
                    {"evidence": row["evidence"], "reason": reason, "cited_by": None}
                )

    for row in approvals:
        approval = row["approval"]
        if approval is None:
            continue
        if row["status"] != ApprovalStatus.ACTIVE:
            decision["stale_approvals"].append({"approval": approval, "reason": "marked stale"})
        elif row["sha"] != head_sha:
            decision["stale_approvals"].append(
                {"approval": approval, "reason": f"approved {row['sha']}, head is {head_sha}"}
            )
        elif row["bad_evidence"]:
            for evidence in row["bad_evidence"]:
                decision["blocked"].append(
                    {
                        "evidence": evidence,
                        "reason": f"not an executed run on {head_sha}",
                        "cited_by": approval,
                    }
                )
        else:
            decision["valid_approvals"].append(approval)

    decision["refuted"] = [
        row for row in recall(graph, pr_number) if row["relation"] == "REFUTED_BY"
    ]
    unapproved = bool(decision["stale_approvals"]) and not decision["valid_approvals"]
    failed = bool(decision["blocked"]) or unapproved
    decision["conclusion"] = "failure" if failed else "success"
    decision["comment"] = failed or bool(decision["refuted"])
    return decision


def check_run_payload(decision: dict) -> dict:
    """Body for the GitHub Checks API, built only from the decision's ids."""
    lines = [
        f"blocked: {item['evidence']} {item['reason']}"
        + (f" (cited by {item['cited_by']})" if item["cited_by"] else "")
        for item in decision["blocked"]
    ]
    lines += [f"stale: {item['approval']} {item['reason']}" for item in decision["stale_approvals"]]
    lines += [
        f"refuted: {row['claim']} by {row['evidence']} ({row['incident']}, via {row['via']})"
        for row in decision["refuted"]
    ]
    titles = {
        "failure": "sheldon: blocked",
        "success": "sheldon: clear",
        "neutral": "sheldon: PR not in the graph yet",
    }
    return {
        "name": CHECK_NAME,
        "head_sha": decision["head_sha"],
        "status": "completed",
        "conclusion": decision["conclusion"],
        "output": {
            "title": titles[decision["conclusion"]],
            "summary": "\n".join(lines) or "No refuted fix, stale approval, or unproven evidence.",
        },
    }
