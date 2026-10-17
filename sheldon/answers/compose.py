"""PR comment from traversal rows.

Status: to build. This function is not a working feature.
"""

COMPOSE_IS_STUB = True


def compose(graph: str, question: str, evidence: list[dict]) -> dict:
    """To build. Return answer, citations, path, and abstained.

    Citations come from ``evidence``. Do not invent ids.
    This function does not decide whether a refute lands.
    """
    del graph, question, evidence
    if COMPOSE_IS_STUB:
        raise NotImplementedError("P3: cite the bundle or abstain")
