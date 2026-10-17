"""W3 done/fixed claim.

Status: to build. It is not a working feature. W1's query ran; this shape has not.
"""


def claim_done(
    graph: str,
    claim_id: str,
    head_sha: str,
    evidence_ids: list[str],
    model: str,
    session: str,
) -> str | None:
    """To build. Return the claim id, or None when no passing executed run is cited."""
    del graph, claim_id, head_sha, evidence_ids, model, session
    raise NotImplementedError("to build: W3 done claim")
