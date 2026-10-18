"""A read warns when FalkorDB is down. It does not block."""

import pytest

from sheldon.check.__main__ import check_result
from sheldon.coordination.resume import resume_result
from sheldon.retrieval.recall import recall_result


def test_a_read_warns_on_an_outage(monkeypatch: pytest.MonkeyPatch) -> None:
    def down() -> None:
        raise ConnectionError("Connection refused")

    monkeypatch.setattr("sheldon.db.connect", down)

    recalled = recall_result("g", 7)
    assert recalled.exit_code == 0
    assert recalled.data["decision"] == "warn"
    assert "Database unavailable" in recalled.text

    resumed = resume_result("g", "agent")
    assert resumed.exit_code == 0
    assert resumed.data["decision"] == "warn"
    assert "Database unavailable" in resumed.text

    checked = check_result("g", 7, "b2", [])
    assert checked.exit_code == 0
    assert checked.data["decision"] == "warn"
    assert "Database unavailable" in checked.data["output"]["summary"]
    assert "Database unavailable" in checked.text
