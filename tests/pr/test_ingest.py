"""pr-ingest writes PR -[:CHANGES]-> File for one head sha."""

import pytest

from sheldon.db import connect
from sheldon.pr import ingest_pull_request
from sheldon.retrieval import recall

GRAPH = "test_pr_ingest"


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    # A File that history ingest already wrote. pr-ingest must reuse it, not duplicate it.
    db.select_graph(GRAPH).query("CREATE (:File {path: 'checkout/cache.py', language: 'python'})")
    yield GRAPH
    db.select_graph(GRAPH).delete()


def _rows(graph: str) -> list[list]:
    return (
        connect()
        .select_graph(graph)
        .query(
            "MATCH (pr:PR)-[c:CHANGES]->(f:File) "
            "RETURN pr.number, pr.head_sha, f.path, c.sha ORDER BY f.path"
        )
        .result_set
    )


def test_writes_changes_for_the_head_sha(graph: str) -> None:
    assert ingest_pull_request(graph, 7, "a1", ["checkout/cache.py", "docs/readme.md"]) == 2
    assert _rows(graph) == [
        [7, "a1", "checkout/cache.py", "a1"],
        [7, "a1", "docs/readme.md", "a1"],
    ]


def test_reuses_an_existing_file_node(graph: str) -> None:
    ingest_pull_request(graph, 7, "a1", ["checkout/cache.py"])
    files = connect().select_graph(graph).query(
        "MATCH (f:File {path: 'checkout/cache.py'}) RETURN count(f), f.language"
    ).result_set
    assert files == [[1, "python"]]


def test_a_new_push_replaces_the_changed_file_set(graph: str) -> None:
    ingest_pull_request(graph, 7, "a1", ["checkout/cache.py", "docs/readme.md"])
    assert ingest_pull_request(graph, 7, "b2", ["checkout/cache.py", "checkout/api.py"]) == 2
    assert _rows(graph) == [
        [7, "b2", "checkout/api.py", "b2"],
        [7, "b2", "checkout/cache.py", "b2"],
    ]
    prs = connect().select_graph(graph).query("MATCH (pr:PR) RETURN count(pr)").result_set
    assert prs == [[1]]
    # The File node for a path the PR no longer touches stays. Only the edge goes.
    readme = connect().select_graph(graph).query(
        "MATCH (f:File {path: 'docs/readme.md'}) RETURN count(f)"
    ).result_set
    assert readme == [[1]]


def test_a_pr_with_no_changed_files(graph: str) -> None:
    assert ingest_pull_request(graph, 9, "c3", []) == 0
    prs = connect().select_graph(graph).query(
        "MATCH (pr:PR {number: 9}) RETURN pr.head_sha"
    ).result_set
    assert prs == [["c3"]]


def test_recall_reads_what_ingest_wrote(graph: str) -> None:
    connect().select_graph(graph).query(
        "MATCH (f:File {path: 'checkout/cache.py'}) "
        "CREATE (i:Incident {id: 'INC-12', title: 't'})-[:TOUCHED]->(f), "
        "(i)-[:HAS_CAUSE]->(:Claim {id: 'C-5', kind: 'fix', status: 'refuted'})"
    )
    ingest_pull_request(graph, 7, "a1", ["checkout/cache.py"])
    assert [row["incident"] for row in recall(graph, 7)] == ["INC-12"]
