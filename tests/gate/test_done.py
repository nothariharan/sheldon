"""W3. A done claim lands only with a passing executed test run on this sha."""

import pytest

from sheldon.db import connect
from sheldon.gate.done import claim_done

GRAPH = "test_w3_done"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(
        "CREATE (:Claim {id: 'C-1', kind: 'done', status: 'open'}),"
        "(:Evidence {id: 'E-pass', kind: 'test_run', executed: true, sha: 'abc', exit_code: 0}),"
        "(:Evidence {id: 'E-fail', kind: 'test_run', executed: true, sha: 'abc', exit_code: 1}),"
        "(:Evidence {id: 'E-off', kind: 'test_run', executed: false, sha: 'abc', exit_code: 0}),"
        "(:Evidence {id: 'E-old', kind: 'test_run', executed: true, sha: 'old', exit_code: 0}),"
        "(:Evidence {id: 'E-note', kind: 'note', executed: true, sha: 'abc', exit_code: 0})"
    )
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def _done(graph: str, evidence_ids: list[str]) -> str | None:
    return claim_done(graph, "C-1", "abc", evidence_ids, model="opus", session="s1")


def _approvals(graph: str) -> int:
    return connect().select_graph(graph).query(
        "MATCH (a:Approval) RETURN count(a)"
    ).result_set[0][0]


def test_no_passing_run_returns_no_approval(graph: str) -> None:
    assert _done(graph, ["E-fail"]) is None
    assert _done(graph, ["E-off"]) is None
    assert _done(graph, ["E-old"]) is None
    assert _done(graph, ["E-note"]) is None
    assert _done(graph, ["missing"]) is None
    assert _done(graph, []) is None
    assert _approvals(graph) == 0


def test_a_repeated_evidence_id_is_accepted(graph: str) -> None:
    assert _done(graph, ["E-pass", "E-pass"]) is not None
    assert _approvals(graph) == 1


def test_a_second_call_does_not_write_another_approval(graph: str) -> None:
    first = _done(graph, ["E-pass"])
    _done(graph, ["E-pass"])
    assert first is not None
    count = connect().select_graph(graph).query(
        "MATCH (a:Approval {id: $id}) RETURN count(a)",
        {"id": first},
    ).result_set[0][0]
    assert count == 1


def test_a_passing_run_on_the_head_writes_an_approval(graph: str) -> None:
    approval = _done(graph, ["E-pass"])
    assert approval is not None
    rows = connect().select_graph(graph).query(
        "MATCH (a:Approval)-[:FOR]->(c:Claim {id: 'C-1'}) "
        "MATCH (a)-[:CITES]->(e:Evidence) "
        "RETURN a.id, e.id"
    ).result_set
    assert rows == [[approval, "E-pass"]]


def test_done_blocks_when_the_database_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    from sheldon.gate.closed import DatabaseBlocked

    monkeypatch.delenv("SHELDON_FAIL_OPEN", raising=False)

    def boom() -> None:
        raise ConnectionError("Connection refused")

    monkeypatch.setattr("sheldon.gate.done.connect", boom)
    with pytest.raises(DatabaseBlocked, match="done blocked"):
        claim_done("g", "C-1", "sha", ["E-1"], "m", "s")


def test_done_escape_hatch_lets_the_driver_error_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHELDON_FAIL_OPEN", "1")

    def boom() -> None:
        raise ConnectionError("Connection refused")

    monkeypatch.setattr("sheldon.gate.done.connect", boom)
    with pytest.raises(ConnectionError, match="Connection refused"):
        claim_done("g", "C-1", "sha", ["E-1"], "m", "s")
