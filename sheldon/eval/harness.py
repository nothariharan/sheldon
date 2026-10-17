"""Repeated-failed-steps count. Each run resets from one frozen copy."""

from sheldon.schema import EVAL_SEED_GRAPH


def reset_from_seed(dest_graph: str, seed_graph: str = EVAL_SEED_GRAPH) -> None:
    """Copy the frozen seed to ``dest_graph``.

    ``GRAPH.COPY`` errors if the destination exists. Delete the destination
    first when re-running. Do not use the copy as a branch-and-merge sandbox.
    """
    del dest_graph, seed_graph
    raise NotImplementedError("eval: GRAPH.COPY the frozen seed, then run")


def count_repeated_failed_steps(graph: str) -> int:
    """Raw count. The definition has to be written before this returns a real number."""
    del graph
    raise NotImplementedError(
        "eval: write the definition, then queries/repeated_failed_steps.cypher"
    )
