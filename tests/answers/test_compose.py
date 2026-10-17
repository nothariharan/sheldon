"""Tests for PR comment composition from traversal rows.

Contract:
- The comment text is built from traversal rows.
- An empty bundle abstains.
- No id appears that was not in the bundle.
- Does not invent ids or paths.
"""

from typing import Generator

import pytest

from sheldon.answers.compose import compose
from sheldon.db import connect
from sheldon.retrieval.recall import recall
from sheldon.seed import load_seed

GRAPH = "test_compose_graph"


def _drop(key: str) -> None:
    try:
        connect().select_graph(key).delete()
    except Exception:  # noqa: BLE001 - graph may not exist
        pass


@pytest.fixture()
def seed_graph() -> Generator[str, None, None]:
    _drop(GRAPH)
    load_seed(GRAPH)
    yield GRAPH
    _drop(GRAPH)


def test_compose_empty_bundle_abstains() -> None:
    result = compose(
        graph="any_graph",
        question="Does this PR touch refuted fixes?",
        evidence=[],
    )
    assert result["abstained"] is True
    assert result["citations"] == []
    assert result["path"] == []
    assert "abstained" in result["answer"].lower()


def test_compose_uninformative_bundle_abstains() -> None:
    uninformative = [
        {"file": "readme.md", "via": None, "incident": None, "claim": None, "evidence": None}
    ]
    result = compose(
        graph="any_graph",
        question="Any safety context?",
        evidence=uninformative,
    )
    assert result["abstained"] is True
    assert result["citations"] == []


def test_compose_with_real_recall_rows_from_seed(seed_graph: str) -> None:
    # PR 7 touches checkout/cache.py which co-changes with session.py (INC-12)
    bundle = recall(seed_graph, 7)
    assert len(bundle) > 0

    result = compose(
        graph=seed_graph,
        question="Summarize historical failure context for PR 7",
        evidence=bundle,
    )

    assert result["abstained"] is False

    # Check citations: must contain the real bundle items
    assert "INC-12" in result["citations"]
    assert "C-5" in result["citations"]
    assert "E-41" in result["citations"]

    # Check paths
    assert "checkout/cache.py" in result["path"]
    assert "checkout/session.py" in result["path"]

    # Strict invariant: No citation or path appears that was not in the bundle
    bundle_ids = {
        row.get(key)
        for row in bundle
        for key in ("incident", "claim", "evidence")
        if row.get(key)
    }
    bundle_paths = {
        row.get(key)
        for row in bundle
        for key in ("file", "via")
        if row.get(key)
    }

    for cite in result["citations"]:
        assert cite in bundle_ids

    for p in result["path"]:
        assert p in bundle_paths

    # Comment text must explain the refuted fix and cite the evidence
    answer = result["answer"]
    assert "INC-12" in answer
    assert "C-5" in answer
    assert "E-41" in answer
    assert "refuted" in answer.lower()


def test_compose_no_invented_ids_in_synthetic_bundle() -> None:
    synthetic = [
        {
            "file": "billing/stripe.py",
            "via": "billing/webhook.py",
            "incident": "INC-88",
            "title": "Webhook race under high concurrency",
            "claim": "C-101",
            "kind": "fix",
            "status": "refuted",
            "relation": "REFUTED_BY",
            "evidence": "E-909",
        }
    ]

    result = compose(
        graph="test_graph",
        question="Is billing safe?",
        evidence=synthetic,
    )

    assert result["abstained"] is False
    assert result["citations"] == ["INC-88", "C-101", "E-909"]
    assert result["path"] == ["billing/stripe.py", "billing/webhook.py"]
    assert "INC-88" in result["answer"]
    assert "C-101" in result["answer"]
    assert "E-909" in result["answer"]


def test_compose_deduplicates_repeated_findings() -> None:
    repeated = [
        {
            "file": "checkout/cache.py",
            "via": "checkout/session.py",
            "incident": "INC-12",
            "title": "Checkout timeout",
            "claim": "C-5",
            "kind": "fix",
            "status": "refuted",
            "relation": "REFUTED_BY",
            "evidence": "E-41",
        },
        {
            "file": "checkout/cache.py",
            "via": "checkout/cache.py",
            "incident": "INC-12",
            "title": "Checkout timeout",
            "claim": "C-5",
            "kind": "fix",
            "status": "refuted",
            "relation": "REFUTED_BY",
            "evidence": "E-41",
        },
    ]
    result = compose("graph", "Check repeated", repeated)
    assert result["abstained"] is False
    assert result["citations"] == ["INC-12", "C-5", "E-41"]
    assert result["answer"].count("fix C-5 was refuted by evidence E-41") == 1

