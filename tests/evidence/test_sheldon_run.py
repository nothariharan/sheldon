"""`sheldon run` records a real subprocess as executed Evidence."""

import hashlib
import shlex
import subprocess
import sys

import pytest

from sheldon.cli import main
from sheldon.db import connect

GRAPH = "test_sheldon_run"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def _head_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _run(graph: str, evidence_id: str, code: str) -> int:
    return main(
        [
            "run",
            "--graph",
            graph,
            "--id",
            evidence_id,
            "--model",
            "opus",
            "--session",
            "s1",
            "--",
            sys.executable,
            "-c",
            code,
        ]
    )


def _row(graph: str, evidence_id: str) -> list:
    rows = connect().select_graph(graph).query(
        "MATCH (e:Evidence {id: $id}) "
        "RETURN e.executed, e.exit_code, e.sha, e.output_digest, e.command",
        {"id": evidence_id},
    ).result_set
    assert len(rows) == 1
    return rows[0]


def test_a_real_subprocess_writes_one_executed_evidence_node(graph: str) -> None:
    digest = hashlib.sha256(b"ok").hexdigest()
    assert _run(graph, "E-ok", "import sys; sys.stdout.buffer.write(b'ok')") == 0
    executed, exit_code, sha, output_digest, command = _row(graph, "E-ok")
    assert executed is True
    assert exit_code == 0
    assert sha == _head_sha()
    assert output_digest == digest
    assert command == shlex.join(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'ok')"]
    )
    count = connect().select_graph(graph).query(
        "MATCH (e:Evidence) RETURN count(e)"
    ).result_set[0][0]
    assert count == 1


def test_a_failing_command_records_its_nonzero_exit_code(graph: str) -> None:
    digest = hashlib.sha256(b"no").hexdigest()
    assert _run(graph, "E-fail", "import sys; sys.stdout.buffer.write(b'no'); sys.exit(3)") == 3
    executed, exit_code, sha, output_digest, _command = _row(graph, "E-fail")
    assert executed is True
    assert exit_code == 3
    assert sha == _head_sha()
    assert output_digest == digest
