"""W1 approval write.

Status: the W1 query ran on v4.22.1. This function is to build.
It is not a working feature.
"""


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
    """To build. Return the approval id, or None when the write returns 0 rows."""
    del (
        graph,
        pr_number,
        head_sha,
        approval_id,
        evidence_ids,
        by,
        actor_kind,
        model,
        session,
    )
    raise NotImplementedError("to build: W1 approval")
