"""record_run writes an executed Evidence node. The model does not."""

import pytest

from sheldon.db import connect
from sheldon.evidence.run import record_run

GRAPH = "test_evidence_run"


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
    except Exception:  # noqa: BLE001 - a failed write may leave no graph
        pass


def test_record_run_writes_an_executed_evidence_node(graph: str) -> None:
    assert (
        record_run(
            graph,
            evidence_id="E-41",
            command="pytest",
            head_sha="abc",
            exit_code=0,
            model="opus",
            session="s1",
        )
        == "E-41"
    )
    rows = connect().select_graph(graph).query(
        "MATCH (e:Evidence {id: 'E-41'}) "
        "RETURN e.kind, e.command, e.sha, e.executed, e.exit_code, e.model, e.session"
    ).result_set
    assert rows == [["test_run", "pytest", "abc", True, 0, "opus", "s1"]]


def test_a_model_cannot_mint_executed_evidence_through_the_producer(graph: str) -> None:
    """The producer records a process exit. It has no flag a model can set false or true."""
    record_run(graph, "E-1", "pytest", "abc", 1, "opus", "s1")
    connect().select_graph(graph).query(
        "CREATE (:Evidence {id: 'E-minted', executed: false, sha: 'abc', "
        "kind: 'test_run', exit_code: 0, model: 'model', session: 'chat'})"
    )
    rows = connect().select_graph(graph).query(
        "MATCH (e:Evidence) RETURN e.id, e.executed ORDER BY e.id"
    ).result_set
    assert rows == [["E-1", True], ["E-minted", False]]
