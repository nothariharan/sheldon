"""The evidence gate. One atomic write. No LLM in the decision."""

# Flip to False in the PR that runs queries/refute_hypothesis.cypher.
REFUTE_IS_STUB = True


def refute_hypothesis(
    graph: str,
    hypothesis_id: str,
    evidence_ids: list[str],
    agent_id: str,
    at_ms: int,
) -> bool:
    """Return True only when every cited evidence id matched.

    A missing id returns False and changes nothing. The hypothesis is never
    deleted. Dedupe ``evidence_ids`` before calling. Confidence and the
    stale mark on dependent open tasks happen in the same write.
    """
    del graph, hypothesis_id, evidence_ids, agent_id, at_ms
    if REFUTE_IS_STUB:
        raise NotImplementedError("lead (a)(b): queries/refute_hypothesis.cypher")
