"""Run every arm on every trap scenario.

Reset each check from one frozen ``GRAPH.COPY``. Time the check, not the copy.
"""

import argparse
import json
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from eval.traps import mem0_arm
from eval.traps.arms import Arm, NoMemory, SearchOnlyBaseline, SheldonArm
from sheldon.cypher import load_query
from sheldon.db import connect
from sheldon.schema import FALKORDB_IMAGE
from sheldon.seed.snapshot import copy_graph, load_seed

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCENARIOS = HERE / "scenarios.json"
HELDOUT = HERE / "heldout" / "scenarios.json"
RESULTS = HERE / "results.md"
COMMAND = "python -m eval.traps"

BASE_GRAPH = "trap_base"
FROZEN_GRAPH = "trap_frozen"
RUN_GRAPH = "trap_run"
HEAD_SHA = "b2"

# Append an arm here. It must implement Arm.name and Arm.blocks.
ARMS: tuple[Arm, ...] = (NoMemory(), SearchOnlyBaseline(), SheldonArm())
# Optional real-tool arms join only when their package is installed
# (requirements-eval.txt), so CI and the base suite run without them.
if mem0_arm.available():
    ARMS += (mem0_arm.Mem0Arm(),)


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


def _false_block_subject(name: str) -> str:
    if name == "sheldon":
        return "Sheldon"
    if name == "no-memory":
        return "No-memory"
    if name == "search-only baseline":
        return "Search-only baseline"
    return name


def _false_block_line(
    scenarios: list[dict[str, Any]],
    decisions: dict[str, dict[str, bool]],
) -> str:
    lines = []
    for arm in ARMS:
        wrong = [
            scenario
            for scenario in scenarios
            if scenario["expected"] == "allow" and decisions[arm.name][scenario["id"]]
        ]
        subject = _false_block_subject(arm.name)
        if not wrong:
            lines.append(f"{subject} wrongly blocked good actions: none.")
            continue
        parts = [f"{scenario['id']} ({scenario['text']})" for scenario in wrong]
        lines.append(f"{subject} wrongly blocked good actions: " + "; ".join(parts) + ".")
    return "\n".join(lines)


def _counts(rows: list[dict[str, Any]]) -> tuple:
    return tuple(
        (row["name"], row["bad_blocked"], row["bad_total"], row["good_wrong"], row["good_total"])
        for row in rows
    )


def _verdict(blocked: bool) -> str:
    return "block" if blocked else "allow"


def _scenario_table(
    scenarios: list[dict[str, Any]],
    decisions: dict[str, dict[str, bool]],
) -> str:
    header = "| id | category | expected | " + " | ".join(arm.name for arm in ARMS) + " |"
    rule = "| --- | --- | --- | " + " | ".join("---" for _ in ARMS) + " |"
    lines = [header, rule]
    for scenario in scenarios:
        sid = scenario["id"]
        cells = " | ".join(_verdict(decisions[arm.name][sid]) for arm in ARMS)
        lines.append(
            f"| {sid} | {scenario['family']} | {scenario['expected']} | {cells} |"
        )
    return "\n".join(lines)


def _miss_lines(
    scenarios: list[dict[str, Any]],
    decisions: dict[str, dict[str, bool]],
    traces: dict[str, dict[str, str]],
) -> list[str]:
    lines = []
    for scenario in scenarios:
        for arm in ARMS:
            got = _verdict(decisions[arm.name][scenario["id"]])
            if got == scenario["expected"]:
                continue
            reason = traces[arm.name][scenario["id"]]
            lines.append(
                f"- {scenario['id']} {arm.name}: expected {scenario['expected']}, "
                f"got {got}. {reason}"
            )
    if not lines:
        return ["None."]
    return lines


def score_set(frozen: str, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    """Score ``scenarios`` on a fresh copy per check. Time the check, not the copy."""
    bad_total = sum(1 for scenario in scenarios if scenario["expected"] == "block")
    good_total = sum(1 for scenario in scenarios if scenario["expected"] == "allow")
    rows: list[dict[str, Any]] = []
    decisions: dict[str, dict[str, bool]] = {}
    traces: dict[str, dict[str, str]] = {}
    for arm in ARMS:
        bad_blocked = 0
        good_wrong = 0
        samples_ms: list[float] = []
        decisions[arm.name] = {}
        traces[arm.name] = {}
        for scenario in scenarios:
            copy_graph(frozen, RUN_GRAPH)
            t0 = perf_counter()
            blocked = arm.blocks(RUN_GRAPH, scenario)
            samples_ms.append((perf_counter() - t0) * 1000)
            decisions[arm.name][scenario["id"]] = blocked
            traces[arm.name][scenario["id"]] = getattr(arm, "trace", "")
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
    return {
        "rows": rows,
        "decisions": decisions,
        "traces": traces,
        "table": format_table(rows),
        "scenarios_table": _scenario_table(scenarios, decisions),
        "misses": _miss_lines(scenarios, decisions, traces),
        "false_blocks": _false_block_line(scenarios, decisions),
        "n": len(scenarios),
    }


def run_suite(write_path: Path | None = RESULTS) -> dict[str, Any]:
    """Score dev and held-out separately. ``write_path`` None skips ``results.md``."""
    dev_scenarios = load_scenarios(SCENARIOS)
    held_scenarios = load_scenarios(HELDOUT)
    frozen = ensure_frozen()
    dev = score_set(frozen, dev_scenarios)
    held = score_set(frozen, held_scenarios)
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
            "## Dev",
            "",
            dev["table"],
            "",
            dev["false_blocks"],
            "",
            "### Dev scenarios",
            "",
            dev["scenarios_table"],
            "",
            "### Dev misses",
            "",
            *dev["misses"],
            "",
            "## Held-out",
            "",
            held["table"],
            "",
            held["false_blocks"],
            "",
            "### Held-out scenarios",
            "",
            held["scenarios_table"],
            "",
            "### Held-out misses",
            "",
            *held["misses"],
            "",
        ]
    )
    if write_path is not None:
        write_path.write_text(body, encoding="utf-8")
    return {
        "dev": dev,
        "heldout": held,
        "counts": {"dev": _counts(dev["rows"]), "heldout": _counts(held["rows"])},
        "decisions": {"dev": dev["decisions"], "heldout": held["decisions"]},
        "markdown": body,
        "date": date,
        "sha": sha,
        "image": FALKORDB_IMAGE,
        "command": COMMAND,
    }


def main(argv: list[str] | None = None) -> int:
    """Print the tables. ``--out PATH`` chooses the report file.

    The default path is ``eval/traps/results.md``. The suite test passes a
    temporary path so that file stays the committed run.
    """
    parser = argparse.ArgumentParser(prog="python -m eval.traps")
    parser.add_argument("--out", default=str(RESULTS))
    args = parser.parse_args(argv)
    report = run_suite(write_path=Path(args.out))
    print("## Dev")
    print()
    print(report["dev"]["table"])
    print()
    print(report["dev"]["false_blocks"])
    print()
    print("## Held-out")
    print()
    print(report["heldout"]["table"])
    print()
    print(report["heldout"]["false_blocks"])
    return 0
