"""R1 recall and the S0 baseline on a small fixture in the seed's vocabulary.

The fixture is not the seed. Ids follow the plan's demo (INC-12, C-7, E-41)
so the S0-vs-R1 comparison reads the same way it will on the real seed.
"""

import pytest

from sheldon.db import connect, read
from sheldon.retrieval import recall, s0
from sheldon.retrieval.s0 import DEMO_QUESTION, create_s0_indexes, keyword_terms

GRAPH = "test_retrieval"

# checkout/cache.py co-changes with checkout/session.py, which INC-12 touched.
# billing/invoice.py is two hops out, so R1 must not reach INC-20.
FIXTURE = """
CREATE (cache:File {path: 'checkout/cache.py'}),
       (session:File {path: 'checkout/session.py'}),
       (invoice:File {path: 'billing/invoice.py'}),
       (readme:File {path: 'docs/readme.md'}),
       (cache)-[:CO_CHANGED_WITH {frequency: 4}]->(session),
       (session)-[:CO_CHANGED_WITH {frequency: 2}]->(invoice),
       (:PR {number: 101, head_sha: 'abc'})-[:CHANGES]->(cache),
       (:PR {number: 102, head_sha: 'def'})-[:CHANGES]->(readme),
       (inc12:Incident {id: 'INC-12', title: 'Checkout times out under cache TTL stampede'}),
       (inc20:Incident {id: 'INC-20', title: 'Invoice totals off by one cent'}),
       (inc12)-[:TOUCHED]->(session),
       (inc20)-[:TOUCHED]->(invoice),
       (c7:Claim {id: 'C-7', kind: 'fix', status: 'refuted',
                  text: 'Raising the cache TTL fixes the checkout timeout'}),
       (c8:Claim {id: 'C-8', kind: 'root_cause', status: 'open',
                  text: 'Session lock contention causes the checkout timeout'}),
       (c9:Claim {id: 'C-9', kind: 'root_cause', status: 'open',
                  text: 'Rounding in invoice totals'}),
       (inc12)-[:HAS_CAUSE]->(c7),
       (inc12)-[:HAS_CAUSE]->(c8),
       (inc20)-[:HAS_CAUSE]->(c9),
       (c7)-[:REFUTED_BY]->(:Evidence {id: 'E-41', kind: 'ci_run', executed: true, exit_code: 1})
"""


@pytest.fixture(scope="module")
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(FIXTURE)
    create_s0_indexes(GRAPH)
    create_s0_indexes(GRAPH)  # second call must not raise
    yield GRAPH
    db.select_graph(GRAPH).delete()


def test_recall_finds_the_refuting_evidence_through_a_co_changed_file(graph: str) -> None:
    rows = recall(graph, 101)
    refuted = [row for row in rows if row["relation"] == "REFUTED_BY"]
    assert refuted == [
        {
            "file": "checkout/cache.py",
            "via": "checkout/session.py",
            "incident": "INC-12",
            "title": "Checkout times out under cache TTL stampede",
            "claim": "C-7",
            "kind": "fix",
            "status": "refuted",
            "relation": "REFUTED_BY",
            "evidence": "E-41",
        }
    ]


def test_recall_keeps_a_claim_with_no_evidence(graph: str) -> None:
    rows = recall(graph, 101)
    c8 = [row for row in rows if row["claim"] == "C-8"]
    assert len(c8) == 1
    assert c8[0]["relation"] is None
    assert c8[0]["evidence"] is None


def test_recall_stops_at_one_hop(graph: str) -> None:
    assert "INC-20" not in {row["incident"] for row in recall(graph, 101)}


def test_recall_on_a_clean_pr_is_empty(graph: str) -> None:
    assert recall(graph, 102) == []
    assert recall(graph, 999) == []


def test_s0_finds_the_text_but_misses_the_evidence(graph: str) -> None:
    hits = s0(graph, DEMO_QUESTION)
    assert {hit["id"] for hit in hits} >= {"INC-12", "C-7"}
    assert all(set(hit) == {"label", "id", "text", "score"} for hit in hits)
    assert "E-41" not in repr(hits)
    assert [row["evidence"] for row in recall(graph, 101) if row["claim"] == "C-7"] == ["E-41"]


def test_s0_with_nothing_searchable_returns_nothing(graph: str) -> None:
    assert s0(graph, "is it? a, to") == []


def test_read_refuses_a_write(graph: str) -> None:
    with pytest.raises(Exception, match="read-only"):
        read(graph, "create_fulltext_claim_text")


def test_keyword_terms() -> None:
    assert keyword_terms("Has the cache-TTL fix (for checkout/cache.py) been tried?") == (
        "cache|ttl|fix|checkout|tried"
    )
    assert keyword_terms("") == ""
