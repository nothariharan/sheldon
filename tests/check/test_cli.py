"""`python -m sheldon.check` prints the same lines the PR check posts."""

import json

import pytest

from sheldon.check.__main__ import main
from sheldon.db import connect

GRAPH = "test_check_cli"

FIXTURE = """
CREATE (readme:File {path: 'docs/readme.md'}),
       (pr:PR {number: 8, head_sha: 'k1'})-[:CHANGES]->(readme),
       (e70:Evidence {id: 'E-70', kind: 'test_run', executed: true, sha: 'k1', exit_code: 0}),
       (:Evidence {id: 'E-52', kind: 'test_run', executed: false, sha: 'k1'}),
       (a5:Approval {id: 'A-5', status: 'active', sha: 'k1'})-[:FOR]->(pr),
       (a5)-[:CITES]->(e70)
"""


@pytest.fixture(scope="module")
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(FIXTURE)
    yield GRAPH
    db.select_graph(GRAPH).delete()


def test_red_check_prints_the_blocked_line_and_exits_1(graph: str, capsys) -> None:
    code = main(["--graph", graph, "8", "k1", "--evidence", "E-52"])
    out = capsys.readouterr().out
    assert code == 1
    assert out.splitlines()[0] == "sheldon: blocked (failure) PR 8 at k1"
    assert "blocked: E-52 not executed" in out


def test_green_check_exits_0(graph: str, capsys) -> None:
    code = main(["--graph", graph, "8", "k1", "--evidence", "E-70"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.splitlines()[0] == "sheldon: clear (success) PR 8 at k1"


def test_json_prints_the_check_run_payload(graph: str, capsys) -> None:
    code = main(["--graph", graph, "8", "k2", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["conclusion"] == "failure"
    assert payload["head_sha"] == "k2"
    assert "stale: A-5 approved k1, head is k2" in payload["output"]["summary"]


def test_repo_flag_uses_the_repo_graph_key(capsys) -> None:
    code = main(["--repo", "team/not-ingested", "1", "z1"])
    assert code == 0
    assert "PR not in the graph yet (neutral)" in capsys.readouterr().out


def test_graph_or_repo_is_required() -> None:
    with pytest.raises(SystemExit):
        main(["8", "k1"])
