"""Atomic writes.

These xfail while the functions are stubs. The PR that implements the write
sets the stub flag to False and deletes the NotImplementedError. A bad
winner count then fails CI instead of hiding as an expected failure.
"""

import threading

import pytest

from sheldon.belief.refute import REFUTE_IS_STUB, refute_hypothesis
from sheldon.coordination.board import CLAIM_IS_STUB, claim_task
from sheldon.db import connect
from sheldon.schema import HypothesisStatus, TaskStatus

WORKERS = 20


def _fresh(name: str):
    db = connect()
    graph = db.select_graph(name)
    try:
        graph.delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    return db.select_graph(name)


def _claim_race() -> None:
    graph = _fresh("race_claim")
    graph.query(
        "CREATE (:Task {id: $id, status: $status, version: 0})",
        {"id": "t1", "status": TaskStatus.OPEN.value},
    )
    winners: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def worker(agent: str) -> None:
        try:
            won = claim_task("race_claim", "t1", agent, now_ms=0, ttl_ms=60_000)
        except Exception as exc:  # noqa: BLE001 - the assertion reports it
            with lock:
                errors.append(exc)
            return
        if won:
            with lock:
                winners.append(agent)

    threads = [threading.Thread(target=worker, args=(f"a{i}",)) for i in range(WORKERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    rows = graph.query("MATCH (t:Task {id: 't1'}) RETURN t.status, t.owner").result_set
    assert errors == []
    assert len(winners) == 1
    assert rows[0][0] == TaskStatus.CLAIMED.value
    assert rows[0][1] == winners[0]


def _refute_race() -> None:
    graph = _fresh("race_refute")
    graph.query(
        "CREATE (:Hypothesis {id: 'h1', status: $open, confidence: 1.0}), (:Event {id: 'e1'})",
        {"open": HypothesisStatus.OPEN.value},
    )
    results: list[bool] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def worker() -> None:
        try:
            ok = refute_hypothesis(
                "race_refute",
                "h1",
                ["e1", "missing-evidence"],
                agent_id="a",
                at_ms=0,
            )
        except Exception as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)
            return
        with lock:
            results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(WORKERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    rows = graph.query("MATCH (h:Hypothesis {id: 'h1'}) RETURN h.status").result_set
    count = graph.query("MATCH (h:Hypothesis) RETURN count(h)").result_set
    assert errors == []
    assert results == [False] * WORKERS
    assert len(rows) == 1
    assert rows[0][0] == HypothesisStatus.OPEN.value
    assert count[0][0] == 1


def test_parallel_claim_has_one_winner() -> None:
    if CLAIM_IS_STUB:
        pytest.xfail("claim_task is a stub. Set CLAIM_IS_STUB False when the write lands.")
    _claim_race()


def test_parallel_refute_with_missing_evidence_is_rejected() -> None:
    if REFUTE_IS_STUB:
        pytest.xfail("refute_hypothesis is a stub. Set REFUTE_IS_STUB False when the write lands.")
    _refute_race()
