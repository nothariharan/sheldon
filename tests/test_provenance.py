"""Provenance read against the demo seed."""

import pytest

from sheldon.db import connect
from sheldon.provenance import writes_with_provenance
from sheldon.seed import load_seed

GRAPH = "test_provenance"


@pytest.fixture()
def graph() -> str:
    try:
        connect().select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    yield load_seed(GRAPH)
    try:
        connect().select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def test_every_seed_write_returns_model_and_session(graph: str) -> None:
    rows = writes_with_provenance(graph)
    assert rows
    assert all(row["model"] and row["session"] for row in rows)
    assert {row["label"] for row in rows} <= {"Claim", "Evidence", "Approval", "Action"}
    ids = {row["id"] for row in rows}
    assert {"C-5", "C-7", "E-41", "E-52", "A-3", "ACT-1"} <= ids
    assert "T-9" not in ids
