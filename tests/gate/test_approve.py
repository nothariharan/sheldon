"""W1. The graph refuses a bad citation and writes one FOR and two CITES."""

import pytest

from sheldon.db import connect
from sheldon.gate.approve import approve, approve_decision
from sheldon.gate.approve import main as approve_main
from sheldon.schema import ApprovalStatus

GRAPH = "test_w1_approve"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(
        "CREATE (:PR {number: 7, head_sha: 'abc'}),"
        "(:Evidence {id: 'E-1', executed: true, sha: 'abc'}),"
        "(:Evidence {id: 'E-2', executed: true, sha: 'abc'}),"
        "(:Evidence {id: 'E-off', executed: false, sha: 'abc'}),"
        "(:Evidence {id: 'E-old', executed: true, sha: 'old'})"
    )
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def _approve(
    graph: str,
    evidence_ids: list[str],
    approval_id: str = "A-1",
    relies_on: str = "",
) -> str | None:
    return approve(
        graph,
        pr_number=7,
        head_sha="abc",
        approval_id=approval_id,
        evidence_ids=evidence_ids,
        by="hari",
        actor_kind="human",
        model="opus",
        session="s1",
        relies_on=relies_on,
    )


def _counts(graph: str) -> list:
    db = connect().select_graph(graph)

    def _count(statement: str) -> int:
        return db.query(statement).result_set[0][0]

    return [
        _count("MATCH (a:Approval) RETURN count(a)"),
        _count("MATCH ()-[f:FOR]->() RETURN count(f)"),
        _count("MATCH ()-[c:CITES]->() RETURN count(c)"),
    ]


def test_valid_ids_create_one_for_and_two_cites(graph: str) -> None:
    assert _approve(graph, ["E-1", "E-2"]) == "A-1"
    assert _counts(graph) == [1, 1, 2]
    status = connect().select_graph(graph).query(
        "MATCH (a:Approval {id: 'A-1'}) RETURN a.status, a.sha, a.model, a.session"
    ).result_set
    assert status == [[ApprovalStatus.ACTIVE.value, "abc", "opus", "s1"]]


def _chain(graph: str) -> None:
    """Open claims 1, 2, and 3 RELIES_ON hops from a refuted claim, plus one open claim."""
    connect().select_graph(graph).query(
        "CREATE (root:Claim {id: 'C-root', status: 'refuted'}),"
        "(near:Claim {id: 'C-near', status: 'open'}),"
        "(mid:Claim {id: 'C-mid', status: 'open'}),"
        "(far:Claim {id: 'C-far', status: 'open'}),"
        "(ok:Claim {id: 'C-ok', status: 'open'}),"
        "(e:Evidence {id: 'E-root'}),"
        "(near)-[:RELIES_ON]->(root),"
        "(mid)-[:DEPENDS_ON]->(near),"
        "(far)-[:RELIES_ON]->(mid),"
        "(root)-[:REFUTED_BY]->(e)"
    )


def test_refuses_when_the_cited_claim_reaches_a_refuted_claim(graph: str) -> None:
    _chain(graph)
    assert _approve(graph, ["E-1"], "A-root", relies_on="C-root") is None
    assert _approve(graph, ["E-1"], "A-near", relies_on="C-near") is None
    assert _approve(graph, ["E-1"], "A-mid", relies_on="C-mid") is None
    assert _approve(graph, ["E-1"], "A-far", relies_on="C-far") is None
    assert _approve(graph, ["E-1"], "A-missing", relies_on="C-missing") is None
    assert _counts(graph) == [0, 0, 0]


def test_refusal_names_the_path_and_the_refuting_evidence(graph: str) -> None:
    _chain(graph)
    decision = approve_decision(
        graph,
        pr_number=7,
        head_sha="abc",
        approval_id="A-far",
        evidence_ids=["E-1"],
        by="hari",
        actor_kind="human",
        model="opus",
        session="s1",
        relies_on="C-far",
    )
    assert decision["id"] is None
    assert decision["claim_ids"] == ["C-far", "C-mid", "C-near", "C-root"]
    assert decision["edge_types"] == ["RELIES_ON", "DEPENDS_ON", "RELIES_ON"]
    assert decision["evidence"] == "E-root"
    assert "C-far -[:RELIES_ON]-> C-mid" in decision["reason"]
    assert "refuted by E-root" in decision["reason"]
    assert _counts(graph) == [0, 0, 0]


def test_approve_cli_json_includes_the_refusal_path(
    graph: str, capsys: pytest.CaptureFixture[str]
) -> None:
    _chain(graph)
    code = approve_main(
        [
            "--graph",
            graph,
            "--pr",
            "7",
            "--sha",
            "abc",
            "--id",
            "A-cli",
            "--evidence",
            "E-1",
            "--relies-on",
            "C-near",
            "--json",
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert "C-near" in captured.err or "C-near" in captured.out
    blob = captured.out + captured.err
    assert "E-root" in blob
    assert "RELIES_ON" in blob


def test_allows_an_approval_that_relies_on_an_open_claim(graph: str) -> None:
    _chain(graph)
    assert _approve(graph, ["E-1"], "A-ok", relies_on="C-ok") == "A-ok"
    db = connect().select_graph(graph)
    edge = db.query(
        "MATCH (:Approval {id: 'A-ok'})-[:RELIES_ON]->(c:Claim) RETURN c.id"
    ).result_set
    assert edge == [["C-ok"]]


def test_refuses_missing_unexecuted_empty_duplicate_and_wrong_sha(graph: str) -> None:
    assert _approve(graph, ["E-1", "missing"], "A-miss") is None
    assert _approve(graph, ["E-off"], "A-off") is None
    assert _approve(graph, [], "A-empty") is None
    assert _approve(graph, ["E-1", "E-1"], "A-dup") is None
    assert _approve(graph, ["E-old"], "A-old") is None
    assert _counts(graph) == [0, 0, 0]
