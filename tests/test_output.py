"""Commands return a CommandResult and can print it as JSON or plain text."""

import io
import json
import sys

import pytest

from sheldon.cli import main as run_main
from sheldon.cli import run_result
from sheldon.coordination.resume import main as resume_main
from sheldon.coordination.resume import resume_result
from sheldon.db import connect
from sheldon.output import CommandResult, emit
from sheldon.preflight import main as preflight_main
from sheldon.preflight import preflight_result
from sheldon.retrieval.recall import main as recall_main
from sheldon.retrieval.recall import recall_result
from sheldon.seed.snapshot import load_seed

GRAPH = "test_output_json"


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


def test_emit_writes_plain_text_or_json() -> None:
    result = CommandResult(
        command="preflight",
        exit_code=2,
        data={"decision": "block"},
        text="blocked: refuted by E-41",
        stream="stderr",
    )
    err = io.StringIO()
    out = io.StringIO()
    assert emit(result, as_json=False, stdout=out, stderr=err) == 2
    assert err.getvalue().strip() == "blocked: refuted by E-41"
    assert out.getvalue() == ""

    err = io.StringIO()
    out = io.StringIO()
    assert emit(result, as_json=True, stdout=out, stderr=err) == 2
    payload = json.loads(out.getvalue())
    assert payload["command"] == "preflight"
    assert payload["exit_code"] == 2
    assert payload["text"] == "blocked: refuted by E-41"
    assert payload["data"]["decision"] == "block"
    assert err.getvalue() == ""


def test_preflight_result_blocks_and_json_flag_prints_it(graph: str) -> None:
    result = preflight_result(graph, "edit checkout/cache.py", ["checkout/cache.py"])
    assert result.command == "preflight"
    assert result.exit_code == 2
    assert result.data["decision"] == "block"
    assert "E-41" in result.data["evidence_ids"]

    out = io.StringIO()
    code = preflight_main(
        [
            "--graph",
            graph,
            "--command",
            "edit checkout/cache.py",
            "--paths",
            "checkout/cache.py",
            "--json",
        ],
        stdout=out,
        stdin=io.StringIO(""),
    )
    assert code == 2
    payload = json.loads(out.getvalue())
    assert payload["data"]["decision"] == "block"
    assert "E-41" in payload["text"]


def test_sheldon_run_result_and_json_flag(graph: str) -> None:
    code = "import sys; sys.stdout.buffer.write(b'ok')"
    result = run_result(
        graph,
        [sys.executable, "-c", code],
        evidence_id="E-json",
        model="opus",
        session="s-json",
    )
    assert result.command == "run"
    assert result.exit_code == 0
    assert result.data["id"] == "E-json"
    assert result.data["executed"] is True

    out = io.StringIO()
    code_out = run_main(
        [
            "run",
            "--json",
            "--graph",
            graph,
            "--id",
            "E-json-cli",
            "--",
            sys.executable,
            "-c",
            code,
        ],
        stdout=out,
    )
    assert code_out == 0
    payload = json.loads(out.getvalue())
    assert payload["command"] == "run"
    assert payload["data"]["id"] == "E-json-cli"
    assert payload["exit_code"] == 0


def test_resume_and_recall_results_support_json(graph: str) -> None:
    resumed = resume_result(graph, "agent-b")
    assert resumed.command == "resume"
    assert {"tried", "failed", "believed", "next"} <= set(resumed.data)

    recalled = recall_result(graph, 7)
    assert recalled.command == "recall"
    assert recalled.exit_code == 0
    assert any(row.get("evidence") == "E-41" for row in recalled.data["rows"])

    out = io.StringIO()
    assert resume_main(["--graph", graph, "--agent", "agent-b", "--json"], stdout=out) == 0
    assert json.loads(out.getvalue())["command"] == "resume"

    out = io.StringIO()
    assert recall_main(["--graph", graph, "7", "--json"], stdout=out) == 0
    body = json.loads(out.getvalue())
    assert body["command"] == "recall"
    assert any(row.get("evidence") == "E-41" for row in body["data"]["rows"])
