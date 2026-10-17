"""`sheldon run` Evidence writer.

Status: to build. It is not a working feature.
A model must not mint Evidence through the gate.
"""


def record_run(
    graph: str,
    evidence_id: str,
    command: str,
    head_sha: str,
    exit_code: int,
    model: str,
    session: str,
) -> str:
    """To build. Return the evidence id after a real process exit is recorded."""
    del graph, evidence_id, command, head_sha, exit_code, model, session
    raise NotImplementedError("to build: sheldon run")
