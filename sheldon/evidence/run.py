"""`sheldon run` Evidence writer.

Status: built. `tests/evidence/test_run.py` shows a real exit is stored
with executed true. This module does not decide the gate.
"""

from sheldon.cypher import load_query
from sheldon.db import connect

# Plan name for a run of the suite. Not a second copy of a schema enum.
TEST_RUN = "test_run"


def _write(graph: str, name: str, params: dict) -> list[dict]:
    result = connect().select_graph(graph).query(load_query(name), params)
    rows = result.result_set or []
    if not rows:
        return []
    columns = [column for _, column in result.header]
    return [dict(zip(columns, row)) for row in rows]


def record_run(
    graph: str,
    evidence_id: str,
    command: str,
    head_sha: str,
    exit_code: int,
    model: str,
    session: str,
) -> str:
    """Return the evidence id after a real process exit is recorded."""
    rows = _write(
        graph,
        "record_run",
        {
            "id": evidence_id,
            "kind": TEST_RUN,
            "command": command,
            "sha": head_sha,
            "exit_code": exit_code,
            "model": model,
            "session": session,
        },
    )
    if not rows:
        raise RuntimeError(f"evidence {evidence_id} was not written")
    return str(rows[0]["id"])
