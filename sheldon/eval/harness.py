"""With/without eval.

Status: reset and repeated-step count built; paired runs to build.
Reset runs from frozen seed and count repeated failed steps.
simulate_retry_block is a scripted dry run where repeated step counts come
from the graph; pass and token values are not measured.
"""

from typing import Any

from sheldon.cypher import load_query
from sheldon.db import connect, read
from sheldon.preflight import preflight
from sheldon.schema import EVAL_SEED_GRAPH, HypothesisStatus
from sheldon.seed import load_seed


def _record_eval_action(
    graph: str,
    action_id: str,
    cmd: str,
    fingerprint: str,
    session: str,
    db: Any = None,
) -> None:
    client = db or connect()
    client.select_graph(graph).query(
        load_query("record_eval_action"),
        {
            "id": action_id,
            "cmd": cmd,
            "fingerprint": fingerprint,
            "session": session,
        },
    )


def reset_from_seed(dest_graph: str, seed_graph: str = EVAL_SEED_GRAPH, db: Any = None) -> None:
    """Copy the frozen seed onto ``dest_graph`` using GRAPH.COPY.

    Deletes ``dest_graph`` first because GRAPH.COPY requires the destination not to exist.
    Initializes ``seed_graph`` from demo seed if not already present.
    """
    client = db or connect()
    try:
        rows = read(seed_graph, "count_nodes", db=client)
        if not rows or not rows[0].get("nodes"):
            load_seed(seed_graph)
    except Exception:
        load_seed(seed_graph)

    try:
        client.select_graph(dest_graph).delete()
    except Exception:
        pass

    client.execute_command("GRAPH.COPY", seed_graph, dest_graph)


def count_repeated_failed_steps(graph: str, db: Any = None) -> int:
    """Return the count of repeated failed steps in ``graph``.

    Counts actions that match a prior attempt on a refuted claim backed by executed
    failing evidence, per the operational definition in docs/plan/eval-def.md.
    """
    rows = read(
        graph,
        "repeated_failed_steps",
        {"refuted": HypothesisStatus.REFUTED.value},
        db=db,
    )
    if not rows:
        return 0
    return int(rows[0].get("repeated_failed_steps", 0))


def format_eval_table(report: dict[str, Any]) -> str:
    """Format evaluation run metrics into a markdown comparison table."""
    s0 = report["s0"]
    s3 = report["s3"]
    wording = report["wording"]

    header = (
        "| Arm | Runs | Repeated Failed Steps (Mean [Min, Max]) | Quality Framing |"
    )
    s0_steps = (
        f"{s0['repeated_steps_mean']:.1f} "
        f"[{s0['repeated_steps_min']}, {s0['repeated_steps_max']}]"
    )
    s3_steps = (
        f"{s3['repeated_steps_mean']:.1f} "
        f"[{s3['repeated_steps_min']}, {s3['repeated_steps_max']}]"
    )

    lines = [
        "Scripted dry run: pass and token values are not measured; "
        "repeated step counts come from the graph.",
        "",
        header,
        "|---|---|---|---|",
        (
            f"| **S0 (Baseline)** | {len(s0['runs'])} | "
            f"{s0_steps} | Baseline |"
        ),
        (
            f"| **S3 (Sheldon Full)** | {len(s3['runs'])} | "
            f"{s3_steps} | {wording} |"
        ),
    ]
    return "\n".join(lines)


def simulate_retry_block(
    seed_graph: str = EVAL_SEED_GRAPH,
    runs_per_arm: int = 3,
    n_tasks: int = 1,
    db: Any = None,
) -> dict[str, Any]:
    """Execute dry-run simulation of retry block across at least 3 runs per arm.

    Arms:
    - S0: Baseline memory without PreToolUse retry block. Retries historically refuted fixes.
    - S3: Sheldon system with PreToolUse retry block intercepting refuted actions.

    Repeated failed step counts are measured directly from the graph via
    ``count_repeated_failed_steps``. Pass rates and token totals are left out
    until real agent runs are wired.
    """
    if runs_per_arm < 3:
        raise ValueError(
            f"Evaluation protocol requires at least 3 runs per arm, got {runs_per_arm}"
        )

    client = db or connect()

    # Pre-seed frozen seed graph
    try:
        rows = read(seed_graph, "count_nodes", db=client)
        if not rows or not rows[0].get("nodes"):
            load_seed(seed_graph)
    except Exception:
        load_seed(seed_graph)

    s0_results: list[dict[str, Any]] = []
    s3_results: list[dict[str, Any]] = []

    # Execute Arm S0 (Baseline)
    for r in range(1, runs_per_arm + 1):
        graph_key = f"eval_s0_run_{r}"
        reset_from_seed(graph_key, seed_graph=seed_graph, db=client)

        # In S0 baseline, agent executes proposed fix 'edit checkout/cache.py' (repeats ACT-1)
        action_id = f"ACT-S0-{r}"
        cmd = "edit checkout/cache.py"
        _record_eval_action(
            graph_key,
            action_id=action_id,
            cmd=cmd,
            fingerprint=cmd,
            session=f"S0-session-{r}",
            db=client,
        )

        repeated_count = count_repeated_failed_steps(graph_key, db=client)
        s0_results.append({
            "run": r,
            "repeated_failed_steps": repeated_count,
        })
        try:
            client.select_graph(graph_key).delete()
        except Exception:
            pass

    # Execute Arm S3 (Sheldon Full)
    for r in range(1, runs_per_arm + 1):
        graph_key = f"eval_s3_run_{r}"
        reset_from_seed(graph_key, seed_graph=seed_graph, db=client)

        # In S3, PreToolUse preflight checks candidate command
        decision = preflight(
            graph_key,
            command="edit checkout/cache.py",
            paths=["checkout/cache.py"],
            db=client,
        )

        # Preflight returns block citing E-41; repeated failed step is intercepted and prevented
        if decision.get("decision") != "block":
            raise AssertionError(f"Expected preflight block in S3 run {r}, got {decision}")

        repeated_count = count_repeated_failed_steps(graph_key, db=client)
        s3_results.append({
            "run": r,
            "repeated_failed_steps": repeated_count,
        })
        try:
            client.select_graph(graph_key).delete()
        except Exception:
            pass

    def _stats(runs: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(runs)
        repeated_list = [x["repeated_failed_steps"] for x in runs]

        return {
            "runs": runs,
            "repeated_steps_mean": sum(repeated_list) / n,
            "repeated_steps_min": min(repeated_list),
            "repeated_steps_max": max(repeated_list),
        }

    s0_stats = _stats(s0_results)
    s3_stats = _stats(s3_results)

    # Wording stays 'safer at the same quality' unless margin beats a 1-task gap (1 / n_tasks).
    # Since pass rates are unmeasured in dry run, quality framing stays default.
    wording = "safer at the same quality"

    report = {
        "runs_per_arm": runs_per_arm,
        "n_tasks": n_tasks,
        "s0": s0_stats,
        "s3": s3_stats,
        "wording": wording,
    }
    report["table"] = format_eval_table(report)
    return report


# Aliases for backwards compatibility and script callers
run_paired_eval = simulate_retry_block
dry_run_paired_eval = simulate_retry_block

