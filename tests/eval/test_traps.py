"""The trap suite finishes, prints a table, and repeats the same counts.

Scores are not asserted. Two runs must match each other on the counts.
"""

import subprocess
import sys
from pathlib import Path

from eval.traps.runner import ensure_frozen, load_scenarios, run_suite
from sheldon.db import connect
from sheldon.schema import FALKORDB_IMAGE

ROOT = Path(__file__).resolve().parents[2]


def test_scenario_file_has_the_required_mix() -> None:
    scenarios = load_scenarios()
    by: dict[str, list[dict]] = {}
    for scenario in scenarios:
        by.setdefault(scenario["family"], []).append(scenario)
    assert len(by["exact"]) == 4
    assert len(by["reworded"]) == 4
    assert len(by["done"]) == 3
    assert len(by["hop"]) == 3
    assert len(by["good"]) >= 6
    assert {scenario["hops"] for scenario in by["hop"]} == {1, 2, 3}
    bad = [scenario for scenario in scenarios if scenario["family"] != "good"]
    assert all(scenario["expected"] == "block" for scenario in bad)
    assert all(scenario["expected"] == "allow" for scenario in by["good"])


def test_overlay_hops_are_one_two_and_three() -> None:
    frozen = ensure_frozen()
    graph = connect().select_graph(frozen)
    one = graph.query(
        "MATCH (:Claim {id: 'C-21'})-[:RELIES_ON]->(:Claim {id: 'C-20', status: 'refuted'}) "
        "RETURN 1"
    ).result_set
    two = graph.query(
        "MATCH (:Claim {id: 'C-22'})-[:RELIES_ON]->(:Claim)-[:RELIES_ON]->"
        "(:Claim {id: 'C-20', status: 'refuted'}) RETURN 1"
    ).result_set
    three = graph.query(
        "MATCH (:Claim {id: 'C-23'})-[:RELIES_ON]->()-[:RELIES_ON]->()-[:RELIES_ON]->"
        "(:Claim {id: 'C-20', status: 'refuted'}) RETURN 1"
    ).result_set
    assert one and two and three


def test_suite_completes_and_writes_the_table() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "eval.traps"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    for label in ("| Arm |", "no-memory", "search-only baseline", "sheldon"):
        assert label in proc.stdout
    body = (ROOT / "eval" / "traps" / "results.md").read_text(encoding="utf-8")
    assert FALKORDB_IMAGE in body
    assert "python -m eval.traps" in body
    assert "| Arm |" in body
    assert "Main sha:" in body


def test_two_runs_report_identical_counts() -> None:
    first = run_suite(write_path=None)
    second = run_suite(write_path=None)
    assert first["counts"] == second["counts"]
    assert first["decisions"] == second["decisions"]
