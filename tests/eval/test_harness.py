"""Tests for evaluation harness and repeated failed step counter.

Contracts:
- reset_from_seed resets destination graph using GRAPH.COPY.
- count_repeated_failed_steps accurately identifies actions repeating historically refuted fixes.
- run_paired_eval executes at least 3 runs per arm, collecting pass rate, tokens, spread,
  and formatting the markdown comparison table.
- Wording stays 'safer at the same quality' unless margin beats 1-task gap.
"""

from typing import Generator

import pytest

from sheldon.db import connect, read
from sheldon.eval.harness import (
    count_repeated_failed_steps,
    reset_from_seed,
    run_paired_eval,
)
from sheldon.seed import load_seed

SEED_KEY = "test_eval_frozen_seed"
RUN_KEY = "test_eval_run_graph"


def _drop(key: str) -> None:
    try:
        connect().select_graph(key).delete()
    except Exception:  # noqa: BLE001 - graph may not exist
        pass


@pytest.fixture()
def seeded_env() -> Generator[str, None, None]:
    _drop(SEED_KEY)
    _drop(RUN_KEY)
    load_seed(SEED_KEY)
    yield SEED_KEY
    _drop(SEED_KEY)
    _drop(RUN_KEY)


def test_reset_from_seed_copies_graph_round_trip(seeded_env: str) -> None:
    db = connect()
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)

    seed_nodes = read(seeded_env, "count_nodes")[0]["nodes"]
    run_nodes = read(RUN_KEY, "count_nodes")[0]["nodes"]

    assert seed_nodes > 0
    assert run_nodes == seed_nodes

    # Modifying run graph and resetting restores exact original state
    db.select_graph(RUN_KEY).query("CREATE (:ExtraNode {test: true})")
    assert read(RUN_KEY, "count_nodes")[0]["nodes"] == seed_nodes + 1

    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    assert read(RUN_KEY, "count_nodes")[0]["nodes"] == seed_nodes


def test_count_repeated_failed_steps_clean_seed(seeded_env: str) -> None:
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    # The seed contains initial failed attempt ACT-1, which is not yet repeated
    count = count_repeated_failed_steps(RUN_KEY)
    assert count == 0


def test_count_repeated_failed_steps_detects_retried_actions(seeded_env: str) -> None:
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    db = connect()

    # Create ACT-2 repeating ACT-1's command 'edit checkout/cache.py' (refuted by E-41)
    db.select_graph(RUN_KEY).query(
        "CREATE (:Action {id: 'ACT-2', cmd: 'edit checkout/cache.py', "
        "fingerprint: 'edit checkout/cache.py'})"
    )
    assert count_repeated_failed_steps(RUN_KEY) == 1

    # Create ACT-3 repeating the same fix again
    db.select_graph(RUN_KEY).query(
        "CREATE (:Action {id: 'ACT-3', cmd: 'edit checkout/cache.py', "
        "fingerprint: 'edit checkout/cache.py'})"
    )
    assert count_repeated_failed_steps(RUN_KEY) == 2


def test_count_repeated_failed_steps_supports_hypothesis_label(seeded_env: str) -> None:
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    db = connect()

    # Create a refuted Hypothesis node rather than Claim
    db.select_graph(RUN_KEY).query(
        """
        CREATE (e_fail:Evidence {id: 'E-hypo-fail', kind: 'test_run',
                                 executed: true, exit_code: 1}),
               (h:Hypothesis {id: 'H-hypo', status: 'refuted'})-[:REFUTED_BY]->(e_fail),
               (act_prior:Action {id: 'ACT-hypo-prior', cmd: 'hypo cmd', fingerprint: 'hypo cmd'})
                 -[:ATTEMPTED_FIX_FOR]->(h),
               (act_retry:Action {id: 'ACT-hypo-retry', cmd: 'hypo cmd', fingerprint: 'hypo cmd'})
        """
    )
    assert count_repeated_failed_steps(RUN_KEY) == 1


def test_count_repeated_failed_steps_ignores_legitimate_alternatives(seeded_env: str) -> None:
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    db = connect()

    # Legitimate alternative action touching cache.py but different command
    db.select_graph(RUN_KEY).query(
        "CREATE (:Action {id: 'ACT-alt', cmd: 'refactor checkout/cache.py', "
        "fingerprint: 'refactor checkout/cache.py'})"
    )
    assert count_repeated_failed_steps(RUN_KEY) == 0


def test_count_repeated_failed_steps_ignores_unrefuted_or_unexecuted(seeded_env: str) -> None:
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    db = connect()

    # Action repeating an open (unrefuted) claim C-7
    db.select_graph(RUN_KEY).query(
        """
        CREATE (act:Action {id: 'ACT-open-repeat', cmd: 'shard session lock',
                            fingerprint: 'shard session lock'})
        """
    )
    assert count_repeated_failed_steps(RUN_KEY) == 0

    # Action linked to unexecuted evidence (E-52 has executed: false)
    db.select_graph(RUN_KEY).query(
        """
        MATCH (e52:Evidence {id: 'E-52'})
        CREATE (c_unexec:Claim {id: 'C-unexec', status: 'refuted'})-[:REFUTED_BY]->(e52),
               (act_unexec:Action {id: 'ACT-unexec', fingerprint: 'unexec fix'})
                 -[:ATTEMPTED_FIX_FOR]->(c_unexec),
               (act_repeat:Action {id: 'ACT-unexec-repeat', fingerprint: 'unexec fix'})
        """
    )
    assert count_repeated_failed_steps(RUN_KEY) == 0


def test_count_repeated_failed_steps_ignores_passing_evidence(seeded_env: str) -> None:
    reset_from_seed(RUN_KEY, seed_graph=seeded_env)
    db = connect()

    # Claim refuted by passing evidence (exit_code: 0) is invalid per definition
    db.select_graph(RUN_KEY).query(
        """
        CREATE (e_pass:Evidence {id: 'E-pass', kind: 'test_run', executed: true, exit_code: 0}),
               (c_pass:Claim {id: 'C-pass', status: 'refuted'})-[:REFUTED_BY]->(e_pass),
               (act_orig:Action {id: 'ACT-orig', fingerprint: 'pass fix'})
                 -[:ATTEMPTED_FIX_FOR]->(c_pass),
               (act_rep:Action {id: 'ACT-rep', fingerprint: 'pass fix'})
        """
    )
    assert count_repeated_failed_steps(RUN_KEY) == 0


def test_run_paired_eval_enforces_minimum_3_runs() -> None:
    with pytest.raises(ValueError, match="at least 3 runs per arm"):
        run_paired_eval(runs_per_arm=2)


def test_run_paired_eval_executes_protocol_and_formats_table(seeded_env: str) -> None:
    report = run_paired_eval(seed_graph=seeded_env, runs_per_arm=3)

    assert report["runs_per_arm"] == 3
    assert "s0" in report
    assert "s3" in report
    assert "table" in report

    s0 = report["s0"]
    s3 = report["s3"]

    # S0 baseline repeats the refuted step; S3 blocks it
    assert s0["repeated_steps_mean"] > 0
    assert s0["repeated_steps_min"] >= 1
    assert s3["repeated_steps_mean"] == 0.0
    assert s3["repeated_steps_min"] == 0
    assert s3["repeated_steps_max"] == 0

    # Pass rates
    assert s0["pass_rate"] == 0.0
    assert s3["pass_rate"] == 1.0

    # Wording strictly follows constraint: "safer at the same quality"
    assert report["wording"] == "safer at the same quality"

    # Formatted table checks
    table = report["table"]
    assert "| Arm | Runs | Pass Rate | Repeated Failed Steps" in table
    assert "S0 (Baseline)" in table
    assert "S3 (Sheldon Full)" in table
    assert "safer at the same quality" in table
