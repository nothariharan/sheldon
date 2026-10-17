"""Older retrieval stubs.

Status: to build. These functions are not working features.
The PR-time read that ran is R1 in ``recall.py``, not ``q_star``.
"""

RETRIEVE_IS_STUB = True


def retrieve(graph: str, question: str, intent: str = "recall") -> list[dict]:
    """To build. Return rows the graph selected."""
    del graph, question, intent
    if RETRIEVE_IS_STUB:
        raise NotImplementedError("P2: bounded traversal, not an inline query")


def q_star(graph: str) -> list[dict]:
    """To build. Not the R1 demo read."""
    del graph
    if RETRIEVE_IS_STUB:
        raise NotImplementedError("P2: queries/q_star.cypher")
