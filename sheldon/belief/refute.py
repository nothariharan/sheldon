"""W2 refute plus stale cascade.

Status: the W2 query ran on v4.22.1. This function is to build.
It is not a working feature.
"""

# Flip to False in the PR that runs queries/refute_hypothesis.cypher.
REFUTE_IS_STUB = True


def refute_hypothesis(
    graph: str,
    hypothesis_id: str,
    evidence_ids: list[str],
    agent_id: str,
    at_ms: int,
) -> bool:
    """To build. Return True when every cited evidence id matched.

    A missing id returns False and changes nothing. Nothing is deleted.
    """
    del graph, hypothesis_id, evidence_ids, agent_id, at_ms
    if REFUTE_IS_STUB:
        raise NotImplementedError("lead (a)(b): queries/refute_hypothesis.cypher")
