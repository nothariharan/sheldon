"""W3. A done claim lands only with a passing executed test run on this sha."""

import pytest

from sheldon.db import connect
from sheldon.gate.done import claim_done, done_decision
from sheldon.gate.done import main as done_main

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


def _ancestor_chain(graph: str) -> None:
    connect().select_graph(graph).query(
        "CREATE (root:Claim {id: 'C-root', kind: 'done', status: 'refuted'}),"
        "(near:Claim {id: 'C-near', kind: 'done', status: 'open'}),"
        "(mid:Claim {id: 'C-mid', kind: 'done', status: 'open'}),"
        "(far:Claim {id: 'C-far', kind: 'done', status: 'open'}),"
        "(ev:Evidence {id: 'E-root'}),"
        "(near)-[:RELIES_ON]->(root),"
        "(mid)-[:DEPENDS_ON]->(near),"
        "(far)-[:RELIES_ON]->(mid),"
        "(root)-[:REFUTED_BY]->(ev)"
    )


def test_refuses_when_the_done_claim_reaches_a_refuted_claim(graph: str) -> None:
    _ancestor_chain(graph)
    for claim_id in ("C-root", "C-near", "C-mid", "C-far"):
        assert claim_done(graph, claim_id, "abc", ["E-pass"], model="opus", session="s1") is None
    assert _approvals(graph) == 0


def test_done_refusal_names_the_path_and_the_refuting_evidence(graph: str) -> None:
    _ancestor_chain(graph)
    decision = done_decision(graph, "C-far", "abc", ["E-pass"], model="opus", session="s1")
    assert decision["id"] is None
    assert decision["claim_ids"] == ["C-far", "C-mid", "C-near", "C-root"]
    assert decision["edge_types"] == ["RELIES_ON", "DEPENDS_ON", "RELIES_ON"]
    assert decision["evidence"] == "E-root"
    assert "C-far -[:RELIES_ON]-> C-mid" in decision["reason"]
    assert "refuted by E-root" in decision["reason"]
    assert _approvals(graph) == 0


def test_done_cli_json_includes_the_refusal_path(
    graph: str, capsys: pytest.CaptureFixture[str]
) -> None:
    _ancestor_chain(graph)
    code = done_main(
        [
            "--graph",
            graph,
            "--claim",
            "C-near",
            "--sha",
            "abc",
            "--evidence",
            "E-pass",
            "--json",
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    blob = captured.out + captured.err
    assert "C-near" in blob
    assert "E-root" in blob
    assert "RELIES_ON" in blob


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
