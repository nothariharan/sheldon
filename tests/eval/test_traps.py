"""The trap suite finishes, prints a table, and repeats the same counts.

Scores are not asserted. Two runs must match each other on the counts.
The scenario files are frozen: a hash mismatch fails this module.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

from eval.traps.runner import HELDOUT, SCENARIOS, ensure_frozen, load_scenarios, run_suite
from sheldon.db import connect
from sheldon.schema import FALKORDB_IMAGE

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "eval" / "traps" / "FROZEN"


def _benchmark_rows(readme: str, heading: str) -> list[str]:
    body = readme.split(heading, 1)[1]
    stop = "### Held-out" if heading == "### Dev" else "\n## "
    body = body.split(stop, 1)[0]
    rows = []
    for line in body.splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| ---") or line.startswith("| Arm"):
            continue
        rows.append(line)
    return rows


def test_readme_benchmark_rows_match_the_committed_run() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    results = (ROOT / "eval" / "traps" / "results.md").read_text(encoding="utf-8")
    for heading in ("### Dev", "### Held-out"):
        rows = _benchmark_rows(readme, heading)
        arms = [row.split("|")[1].strip() for row in rows]
        assert arms.count("sheldon") == 1
        for row in rows:
            assert row in results


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


def test_scenario_files_match_the_frozen_hashes() -> None:
    lines = [line for line in FROZEN.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 2
    seen = set()
    for line in lines:
        digest, rel = line.split()
        seen.add(rel)
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual == digest
    assert "eval/traps/scenarios.json" in seen
    assert "eval/traps/heldout/scenarios.json" in seen


def test_heldout_file_has_the_required_mix() -> None:
    scenarios = load_scenarios(HELDOUT)
    assert len(scenarios) == 10
    by: dict[str, list[dict]] = {}
    for scenario in scenarios:
        by.setdefault(scenario["family"], []).append(scenario)
    for family in ("exact", "reworded", "done", "hop", "good"):
        assert by.get(family)
    assert len(by["good"]) >= 3
    bad = [scenario for scenario in scenarios if scenario["family"] != "good"]
    assert all(scenario["expected"] == "block" for scenario in bad)
    assert all(scenario["expected"] == "allow" for scenario in by["good"])
    dev_ids = {scenario["id"] for scenario in load_scenarios(SCENARIOS)}
    assert dev_ids.isdisjoint({scenario["id"] for scenario in scenarios})


def test_suite_completes_and_writes_the_table(tmp_path: Path) -> None:
    results = ROOT / "eval" / "traps" / "results.md"
    before = results.read_bytes()
    out = tmp_path / "results.md"
    proc = subprocess.run(
        [sys.executable, "-m", "eval.traps", "--out", str(out)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    for label in (
        "## Dev",
        "## Held-out",
        "| Arm |",
        "no-memory",
        "search-only baseline",
        "sheldon",
    ):
        assert label in proc.stdout
    body = out.read_text(encoding="utf-8")
    assert FALKORDB_IMAGE in body
    assert "python -m eval.traps" in body
    assert "| Arm |" in body
    assert "Main sha:" in body
    assert "### Dev scenarios" in body
    assert "| a1 |" in body
    assert "### Held-out scenarios" in body
    assert "| h-exact-1 |" in body
    assert "### Dev misses" in body
    assert results.read_bytes() == before
    assert results.read_text(encoding="utf-8") == before.decode("utf-8")


def test_two_runs_report_identical_counts() -> None:
    first = run_suite(write_path=None)
    second = run_suite(write_path=None)
    assert first["counts"] == second["counts"]
    assert first["decisions"] == second["decisions"]
