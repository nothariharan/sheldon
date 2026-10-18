"""Run every arm on every trap scenario.

Reset each check from one frozen ``GRAPH.COPY``. Time the check, not the copy.
"""

import json
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from eval.traps.arms import Arm, NoMemory, SearchOnlyBaseline, SheldonArm
from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.schema import FALKORDB_IMAGE
from sheldon.seed.snapshot import copy_graph, load_seed

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCENARIOS = HERE / "scenarios.json"
RESULTS = HERE / "results.md"
COMMAND = "python -m eval.traps"

BASE_GRAPH = "trap_base"
FROZEN_GRAPH = "trap_frozen"
RUN_GRAPH = "trap_run"
HEAD_SHA = "b2"

# Append an arm here. It must implement Arm.name and Arm.blocks.
ARMS: tuple[Arm, ...] = (NoMemory(), SearchOnlyBaseline(), SheldonArm())


def load_scenarios(path: Path = SCENARIOS) -> list[dict[str, Any]]:
    """Read the scenario file. Expected verdicts live in the file, not here."""
    scenarios = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError(f"{path} must be a non-empty list")
    for scenario in scenarios:
        if scenario.get("expected") not in {"block", "allow"}:
            raise ValueError(f"{scenario.get('id')} expected must be block or allow")
        if "text" not in scenario or "action" not in scenario:
            raise ValueError(f"{scenario.get('id')} needs text and action")
    return scenarios


def _drop(key: str) -> None:
    try:
        connect().select_graph(key).delete()
    except Exception:  # noqa: BLE001 - the key may not exist yet
        pass


def ensure_frozen() -> str:
    """Rebuild the frozen graph: demo seed, trap overlay, then GRAPH.COPY."""
    _drop(BASE_GRAPH)
    _drop(FROZEN_GRAPH)
    load_seed(BASE_GRAPH, head_sha=HEAD_SHA)
    connect().select_graph(BASE_GRAPH).query(load_query("trap_overlay"))
    copy_graph(BASE_GRAPH, FROZEN_GRAPH)
    return FROZEN_GRAPH


def _main_sha() -> str:
    for ref in ("origin/main", "main"):
        try:
            return subprocess.check_output(
                ["git", "rev-parse", ref],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return "unknown"


def format_table(rows: list[dict[str, Any]]) -> str:
    """Markdown table. Callers copy this string; they do not rebuild it."""
    lines = [
        "| Arm | Bad blocked | Good wrongly blocked | Median ms |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['bad_blocked']}/{row['bad_total']} | "
            f"{row['good_wrong']}/{row['good_total']} | {row['median_ms']:.2f} |"
        )
    return "\n".join(lines)


def _false_block_line(
    scenarios: list[dict[str, Any]],
    decisions: dict[str, dict[str, bool]],
) -> str:
    wrong = [
        scenario
        for scenario in scenarios
        if scenario["expected"] == "allow" and decisions["sheldon"][scenario["id"]]
    ]
    if not wrong:
        return "Sheldon wrongly blocked good actions: none."
    parts = [f"{scenario['id']} ({scenario['text']})" for scenario in wrong]
    return "Sheldon wrongly blocked good actions: " + "; ".join(parts) + "."


def run_suite(write_path: Path | None = RESULTS) -> dict[str, Any]:
    """Score every arm. ``write_path`` None skips ``results.md``."""
    scenarios = load_scenarios()
    frozen = ensure_frozen()
    bad_total = sum(1 for scenario in scenarios if scenario["expected"] == "block")
    good_total = sum(1 for scenario in scenarios if scenario["expected"] == "allow")
    rows: list[dict[str, Any]] = []
    decisions: dict[str, dict[str, bool]] = {}

    for arm in ARMS:
        bad_blocked = 0
        good_wrong = 0
        samples_ms: list[float] = []
        decisions[arm.name] = {}
        for scenario in scenarios:
            copy_graph(frozen, RUN_GRAPH)
            t0 = perf_counter()
            blocked = arm.blocks(RUN_GRAPH, scenario)
            samples_ms.append((perf_counter() - t0) * 1000)
            decisions[arm.name][scenario["id"]] = blocked
            if scenario["expected"] == "block" and blocked:
                bad_blocked += 1
            elif scenario["expected"] == "allow" and blocked:
                good_wrong += 1
        rows.append(
            {
                "name": arm.name,
                "bad_blocked": bad_blocked,
                "bad_total": bad_total,
                "good_wrong": good_wrong,
                "good_total": good_total,
                "median_ms": statistics.median(samples_ms),
            }
        )

    table = format_table(rows)
    false_blocks = _false_block_line(scenarios, decisions)
    date = datetime.now(timezone.utc).date().isoformat()
    sha = _main_sha()
    body = "\n".join(
        [
            "# Trap suite",
            "",
            f"Date: {date}",
            f"Main sha: {sha}",
            f"Image: {FALKORDB_IMAGE}",
            f"Command: `{COMMAND}`",
            "",
            table,
            "",
            false_blocks,
            "",
        ]
    )
    if write_path is not None:
        write_path.write_text(body, encoding="utf-8")
    counts = tuple(
        (row["name"], row["bad_blocked"], row["bad_total"], row["good_wrong"], row["good_total"])
        for row in rows
    )
    return {
        "rows": rows,
        "counts": counts,
        "decisions": decisions,
        "table": table,
        "false_blocks": false_blocks,
        "markdown": body,
        "date": date,
        "sha": sha,
        "image": FALKORDB_IMAGE,
        "command": COMMAND,
        "n": len(scenarios),
    }


def main() -> int:
    report = run_suite()
    print(report["table"])
    print()
    print(report["false_blocks"])
    return 0
