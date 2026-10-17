"""P3. Prose answers that cite event ids and can abstain."""

COMPOSE_IS_STUB = True


def compose(graph: str, question: str, evidence: list[dict]) -> dict:
    """Return answer, citations, path, and abstained.

    Citations are event ids from ``evidence``. Do not invent ids.
    This function does not decide whether a refute lands.
    """
    del graph, question, evidence
    if COMPOSE_IS_STUB:
        raise NotImplementedError("P3: cite the bundle or abstain")
