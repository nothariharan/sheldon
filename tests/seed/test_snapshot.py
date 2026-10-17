"""The demo seed: what it contains, and that the other stations can read it.

Ids follow docs/plan/deep.md section 3 and docs/plan/demo.md. They are seed
data, not a result.
"""

import pytest

from sheldon.check import decide_check
from sheldon.db import connect
from sheldon.retrieval import recall
from sheldon.seed import copy_graph, load_seed

GRAPH = "test_seed"
COPY = "test_seed_copy"


def _drop(*keys: str) -> None:
    for key in keys:
        try:
            connect().select_graph(key).delete()
        except Exception:  # noqa: BLE001 - graph may not exist
            pass


@pytest.fixture()
def seed() -> str:
    _drop(GRAPH, COPY)
    yield load_seed(GRAPH)
    _drop(GRAPH, COPY)


def _q(graph: str, cypher: str) -> list[list]:
    return connect().select_graph(graph).query(cypher).result_set


def test_seed_has_the_refuted_fix_and_its_evidence(seed: str) -> None:
    assert seed == GRAPH
    rows = _q(
        seed,
        "MATCH (i:Incident {id: 'INC-12'})-[:HAS_CAUSE]->(c:Claim)-[:REFUTED_BY]->(e:Evidence) "
        "RETURN c.id, c.kind, c.status, e.id, e.executed",
    )
    assert rows == [["C-5", "fix", "refuted", "E-41", True]]


def test_seed_has_every_demo_id(seed: str) -> None:
    ids = {row[0] for row in _q(seed, "MATCH (n) WHERE n.id IS NOT NULL RETURN n.id")}
    assert {"INC-12", "C-5", "C-7", "E-41", "E-52", "E-60", "A-3", "T-9"} <= ids


def test_every_claim_evidence_approval_and_action_records_model_and_session(seed: str) -> None:
    missing = _q(
        seed,
        "MATCH (n) WHERE (n:Claim OR n:Evidence OR n:Approval OR n:Action) "
        "AND (n.model IS NULL OR n.session IS NULL) RETURN n.id",
    )
    assert missing == []


def test_w2_cascade_from_c7_reaches_a3_and_t9(seed: str) -> None:
    rows = _q(
        seed,
        "MATCH (:Claim {id: 'C-7'})<-[:RELIES_ON|DEPENDS_ON*1..3]-(d) "
        "WHERE d.status IN ['active', 'open', 'claimed'] RETURN d.id ORDER BY d.id",
    )
    assert rows == [["A-3"], ["T-9"]]


def test_r1_recall_finds_e41_through_the_co_changed_file(seed: str) -> None:
    refuted = [row for row in recall(seed, 7) if row["relation"] == "REFUTED_BY"]
    assert [(row["file"], row["via"], row["claim"], row["evidence"]) for row in refuted] == [
        ("checkout/cache.py", "checkout/session.py", "C-5", "E-41")
    ]


def test_check_is_red_on_e52_and_a3_is_valid_before_the_cascade(seed: str) -> None:
    decision = decide_check(seed, 7, "b2", cited_evidence_ids=["E-52"])
    assert decision["conclusion"] == "failure"
    assert decision["blocked"] == [{"evidence": "E-52", "reason": "not executed", "cited_by": None}]
    assert decision["valid_approvals"] == ["A-3"]


def test_load_seed_refuses_a_graph_that_is_not_empty(seed: str) -> None:
    with pytest.raises(ValueError, match="not empty"):
        load_seed(seed)


def test_copy_graph_resets_a_destination(seed: str) -> None:
    count = "MATCH (n) RETURN count(n)"
    copy_graph(seed, COPY)
    assert _q(COPY, count) == _q(seed, count)
    _q(COPY, "MATCH (c:Claim {id: 'C-7'}) SET c.status = 'refuted'")
    copy_graph(seed, COPY)
    assert _q(COPY, "MATCH (c:Claim {id: 'C-7'}) RETURN c.status") == [["open"]]
