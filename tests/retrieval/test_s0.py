"""S0 keyword baseline. It finds the text and misses the evidence R1 returns."""

from sheldon.retrieval import recall, s0
from sheldon.retrieval.s0 import DEMO_QUESTION, keyword_terms


def test_s0_finds_the_text_but_misses_the_evidence(graph: str) -> None:
    hits = s0(graph, DEMO_QUESTION)
    assert {hit["id"] for hit in hits} >= {"INC-12", "C-7"}
    assert all(set(hit) == {"label", "id", "text", "score"} for hit in hits)
    assert "E-41" not in repr(hits)
    assert [row["evidence"] for row in recall(graph, 101) if row["claim"] == "C-7"] == ["E-41"]



def test_s0_with_nothing_searchable_returns_nothing(graph: str) -> None:
    assert s0(graph, "is it? a, to") == []



def test_keyword_terms() -> None:
    assert keyword_terms("Has the cache-TTL fix (for checkout/cache.py) been tried?") == (
        "cache|ttl|fix|checkout|tried"
    )
    assert keyword_terms("") == ""
