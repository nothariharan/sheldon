"""P2. Anchors, bounded traversal, evidence bundle, and the Q* read."""

RETRIEVE_IS_STUB = True


def retrieve(graph: str, question: str, intent: str = "recall") -> list[dict]:
    """Return an evidence bundle. The graph decides what enters context."""
    del graph, question, intent
    if RETRIEVE_IS_STUB:
        raise NotImplementedError("P2: bounded traversal, not an inline query")


def q_star(graph: str) -> list[dict]:
    """The demo question. S0 must fail it. The Cypher is queries/q_star.cypher."""
    del graph
    if RETRIEVE_IS_STUB:
        raise NotImplementedError("P2: queries/q_star.cypher")
