"""With/without eval.

Status: to build. These functions are not working features.
Write the definition before any count. Do not report a number from here yet.
"""

from sheldon.schema import EVAL_SEED_GRAPH


def reset_from_seed(dest_graph: str, seed_graph: str = EVAL_SEED_GRAPH) -> None:
    """To build. Copy the frozen seed onto ``dest_graph``."""
    del dest_graph, seed_graph
    raise NotImplementedError("eval: GRAPH.COPY the frozen seed, then run")


def count_repeated_failed_steps(graph: str) -> int:
    """To build. Do not return a count until docs/plan/eval-def.md exists."""
    del graph
    raise NotImplementedError(
        "eval: write the definition, then queries/repeated_failed_steps.cypher"
    )
