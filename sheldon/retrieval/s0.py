"""Plain keyword baseline. No traversal.

Status: keyword half wired. ``s0`` runs ``queries/s0_keyword.cypher`` over
Incident titles and Claim text. The vector half waits on ``EMBEDDING_DIM``.
It is the baseline the demo compares R1 against, not a feature to ship.
"""

import re

from sheldon.cypher import load_query
from sheldon.db import connect, read

S0_INDEX_QUERIES = ("create_fulltext_incident_title", "create_fulltext_claim_text")

# Seed vocabulary. Ids in this sentence are seed data, not a result.
DEMO_QUESTION = (
    "This PR changes checkout/cache.py. Has a cache TTL fix for checkout been "
    "tried before, and which evidence refuted it?"
)

_STOPWORDS = frozenset(
    "the and for has have been was were this that which what with from before".split()
)


def keyword_terms(question: str) -> str:
    """Turn a question into a RediSearch OR query. Empty when nothing is searchable.

    A raw question returns no rows: terms are ANDed and punctuation breaks the
    parser. Words shorter than 3 characters and common stopwords are dropped.
    """
    words = re.findall(r"[a-z0-9]+", question.lower())
    terms = dict.fromkeys(w for w in words if len(w) >= 3 and w not in _STOPWORDS)
    return "|".join(terms)


def create_s0_indexes(graph: str) -> None:
    """Create the full-text indexes S0 reads. Safe to call when they exist."""
    target = connect().select_graph(graph)
    for name in S0_INDEX_QUERIES:
        try:
            target.query(load_query(name))
        except Exception as exc:  # noqa: BLE001 - only "already indexed" is expected
            if "already indexed" not in str(exc):
                raise


def s0(graph: str, question: str) -> list[dict]:
    """Return label, id, text, and score hits, best first. No graph walk.

    The hits are stored text only. There is no evidence id and no path, which
    is what the demo shows next to R1.
    """
    terms = keyword_terms(question)
    if not terms:
        return []
    hits = read(graph, "s0_keyword", {"terms": terms})
    return sorted(hits, key=lambda hit: hit["score"], reverse=True)
