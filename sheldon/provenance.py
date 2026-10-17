"""Model and session on writes.

Status: built. `tests/test_provenance.py` shows the read returning model
and session for Claim, Evidence, Approval, and Action. It is a graph read.
"""

from sheldon.db import read


def writes_with_provenance(graph: str) -> list[dict]:
    """Each row has the node id, label, model, and session."""
    return read(graph, "writes_with_provenance")
