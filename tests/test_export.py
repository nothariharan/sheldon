"""Export writes the seed and the three demo moments for the web UI."""

import json
from pathlib import Path

import pytest

from sheldon.db import connect
from sheldon.export import export_document, serve_document, write_fixtures
from sheldon.seed.snapshot import load_seed

GRAPH = "test_web_export"
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "web" / "fixtures"
IDS = {"INC-12", "C-5", "C-7", "E-41", "E-30", "E-60", "A-3", "T-9"}


@pytest.fixture()
def graph() -> str:
    db = connect()
    for name in (GRAPH, GRAPH + "_moments"):
        try:
            db.select_graph(name).delete()
        except Exception:  # noqa: BLE001 - graph may not exist yet
            pass
    load_seed(GRAPH)
    yield GRAPH
    for name in (GRAPH, GRAPH + "_moments"):
        try:
            db.select_graph(name).delete()
        except Exception:  # noqa: BLE001
            pass


def test_export_document_has_the_seed_and_the_three_moments(graph: str) -> None:
    document = export_document(graph)
    assert document["schema"] == "sheldon.export.v1"
    keys = {node["key"] for node in document["nodes"]}
    assert IDS <= keys
    assert any(edge["type"] == "REFUTED_BY" and edge["to"] == "E-41" for edge in document["edges"])

    retry = document["moments"]["retry_block"]
    assert retry["exit_code"] == 2
    assert "blocked: refuted by E-41" in retry["stderr"]
    assert "INC-12" in retry["stderr"]

    gate = document["moments"]["evidence_gate"]
    assert gate["exit_code"] == 1
    assert "blocked: E-52 not executed" in gate["stdout"]

    cascade = document["moments"]["stale_cascade"]
    assert cascade["exit_code"] == 1
    assert "stale: A-3 marked stale" in cascade["stdout"]
    assert "refuted: C-7 by E-60" in cascade["stdout"]


def test_write_fixtures_and_the_checked_in_transcripts(graph: str, tmp_path: Path) -> None:
    document = export_document(graph)
    write_fixtures(document, tmp_path)
    assert json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))["schema"] == (
        "sheldon.export.v1"
    )
    retry_text = (tmp_path / "retry-block.txt").read_text(encoding="utf-8")
    gate_text = (tmp_path / "evidence-gate.txt").read_text(encoding="utf-8")
    cascade_text = (tmp_path / "stale-cascade.txt").read_text(encoding="utf-8")
    assert "blocked: refuted by E-41" in retry_text
    assert "blocked: E-52 not executed" in gate_text
    assert "stale: A-3 marked stale" in cascade_text

    checked = (FIXTURES / "retry-block.txt").read_text(encoding="utf-8")
    assert "blocked: refuted by E-41" in checked
    assert "E-60" in (FIXTURES / "stale-cascade.txt").read_text(encoding="utf-8")


def test_read_only_endpoint_returns_the_document(graph: str) -> None:
    document = export_document(graph)
    url = serve_document(document, port=0)
    import urllib.request

    with urllib.request.urlopen(url, timeout=5) as response:
        assert response.status == 200
        body = json.loads(response.read().decode("utf-8"))
    assert body["schema"] == "sheldon.export.v1"
