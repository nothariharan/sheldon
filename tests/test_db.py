"""Shared read helper."""

import pytest

from sheldon.db import connect, read


def test_read_on_a_graph_that_does_not_exist_returns_no_rows() -> None:
    key = "test_db_missing_graph"
    try:
        connect().select_graph(key).delete()
    except Exception:  # noqa: BLE001 - expected: it should not exist
        pass
    assert read(key, "check_approvals", {"pr": 1, "sha": "x"}) == []


def test_read_still_raises_other_errors() -> None:
    key = "test_db_other_error"
    graph = connect().select_graph(key)
    graph.query("CREATE (:PR {number: 1})")
    try:
        with pytest.raises(Exception, match="read-only"):
            read(key, "create_fulltext_claim_text")
    finally:
        graph.delete()
