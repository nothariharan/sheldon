"""R1 recall through GRAPH.RO_QUERY."""

import pytest

from sheldon.db import read
from sheldon.retrieval import recall


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



def test_read_refuses_a_write(graph: str) -> None:
    with pytest.raises(Exception, match="read-only"):
        read(graph, "create_fulltext_claim_text")
