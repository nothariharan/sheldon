"""SessionStart prints the capsule for the task in this session."""

import io
import json
from pathlib import Path

import pytest

from sheldon.capsule import capsule
from sheldon.db import connect
from sheldon.hooks.session_start import main, session_start
from sheldon.seed.snapshot import load_seed

GRAPH = "test_session_hook"
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    load_seed(GRAPH)
    yield GRAPH
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001
        pass


def test_session_start_returns_the_capsule(graph: str) -> None:
    text = session_start(graph, "T-9")
    assert text == capsule(graph, "T-9")
    assert "sheldon run -- pytest" in text
    assert "E-41" in text


def test_cli_prints_the_capsule(graph: str) -> None:
    out = io.StringIO()
    code = main(["--graph", graph, "--task", "T-9"], stdout=out)
    assert code == 0
    assert out.getvalue() == capsule(graph, "T-9")


def test_install_snippet_is_a_session_start_hook() -> None:
    snippet = json.loads((ROOT / "hooks" / "claude-session-start.json").read_text(encoding="utf-8"))
    command = snippet["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "sheldon.hooks.session_start" in command
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "SHELDON_TASK" in readme
    assert "hooks/claude-session-start.json" in readme
