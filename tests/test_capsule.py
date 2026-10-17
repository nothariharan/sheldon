"""Tests for session capsule context injection.

Contract:
- The returned text includes a do-not from a refuted attempt and the proving command.
- Truncation respects max_chars and never cuts an evidence ID mid-string.
- Stale tasks from W2 cascade display an explicit warning.
"""

from typing import Generator

import pytest

from sheldon.belief.refute import refute_claim
from sheldon.capsule import capsule
from sheldon.db import connect
from sheldon.seed import load_seed

GRAPH = "test_capsule_graph"


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


def test_capsule_returns_do_not_and_proving_command(seed_graph: str) -> None:
    text = capsule(seed_graph, "T-9")

    # Proving command present
    assert "sheldon run -- pytest" in text
    assert "## Proving Command" in text

    # Do-not directive from refuted attempt ACT-1 / C-5 / E-41
    assert "## Do-Not Directives" in text
    assert "DO NOT run `edit checkout/cache.py`" in text
    assert "TTL" in text
    assert "E-41" in text


def test_capsule_reflects_w2_refute_cascade(seed_graph: str) -> None:
    # Refute C-7 with E-60, which stales T-9
    ok = refute_claim(
        seed_graph,
        claim_id="C-7",
        evidence_ids=["E-60"],
        agent_id="ci",
        model="ci",
        session="CI-60",
    )
    assert ok is True

    text = capsule(seed_graph, "T-9")

    # Warning for stale task present
    assert "stale" in text.lower()
    assert "C-7" in text

    # Both refuted attempts cited
    assert "E-41" in text
    assert "E-60" in text
    assert "sheldon run -- pytest" in text


def test_capsule_custom_proving_command(seed_graph: str) -> None:
    db = connect()
    custom_cmd = "sheldon run -- pytest tests/test_session.py -v"
    db.select_graph(seed_graph).query(
        "MATCH (t:Task {id: 'T-9'}) SET t.proving_command = $cmd",
        {"cmd": custom_cmd},
    )

    text = capsule(seed_graph, "T-9")
    assert custom_cmd in text


def test_capsule_budget_preserves_whole_evidence_ids(seed_graph: str) -> None:
    # Set a small budget that accommodates the header + proving command, but not all bullets
    small_budget = 240
    text = capsule(seed_graph, "T-9", max_chars=small_budget)

    assert len(text) <= small_budget
    assert "sheldon run -- pytest" in text
    # Evidence IDs are either completely included or completely omitted, never sliced (e.g. "E-")
    if "E-" in text:
        assert "E-41" in text


def test_capsule_missing_task_raises_key_error(seed_graph: str) -> None:
    with pytest.raises(KeyError, match="task 'T-999' not found"):
        capsule(seed_graph, "T-999")
