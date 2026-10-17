"""record_run writes an executed Evidence node. Raw writes are not blocked."""

import inspect

import pytest

from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.evidence import run as producer
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


def test_only_record_run_produces_executed_evidence(graph: str) -> None:
    """The producer API has one writer, and it stores executed true as a literal."""
    writers = [
        name
        for name, obj in vars(producer).items()
        if inspect.isfunction(obj)
        and obj.__module__ == producer.__name__
        and not name.startswith("_")
    ]
    assert writers == ["record_run"]
    assert "executed" not in inspect.signature(record_run).parameters
    statement = load_query("record_run")
    assert "executed: true" in statement
    assert "$executed" not in statement

    assert record_run(graph, "E-1", "pytest", "abc", 0, "opus", "s1") == "E-1"
    rows = connect().select_graph(graph).query(
        "MATCH (e:Evidence) WHERE e.executed = true RETURN e.id"
    ).result_set
    assert rows == [["E-1"]]
