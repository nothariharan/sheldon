"""PR check decision.

Status: to build. It is not a working feature.
R1's query ran. This webhook and check run have not.
"""


def decide_check(graph: str, pr_number: int, head_sha: str) -> dict:
    """To build. Return conclusion, evidence id, and whether to comment."""
    del graph, pr_number, head_sha
    raise NotImplementedError("to build: check run")
