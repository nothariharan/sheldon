"""Check-run decision on a fixture in the seed's vocabulary.

The fixture is not the seed. PR 7 is the demo PR: E-52 is a test run that
never executed, A-3 went stale when W2 refuted C-7, and A-4 approved an older
sha. PR 8 is clean. The check-e2e row reruns this on the real seed.
"""

import pytest

from sheldon.check import check_run_payload, decide_check
from sheldon.check.webhook import handle_event
from sheldon.db import connect
from sheldon.seed import copy_graph, load_seed

GRAPH = "test_check_run"

FIXTURE = """
CREATE (cache:File {path: 'checkout/cache.py'}),
       (session:File {path: 'checkout/session.py'}),
       (readme:File {path: 'docs/readme.md'}),
       (cache)-[:CO_CHANGED_WITH {frequency: 4}]->(session),
       (pr7:PR {number: 7, head_sha: 'h2'})-[:CHANGES]->(cache),
       (pr8:PR {number: 8, head_sha: 'k1'})-[:CHANGES]->(readme),
       (pr9:PR {number: 9, head_sha: 'm1'})-[:CHANGES]->(readme),
       (:PR {number: 10, head_sha: 'n1'})-[:CHANGES]->(readme),
       (inc12:Incident {id: 'INC-12', title: 'Checkout times out under cache TTL stampede'}),
       (inc12)-[:TOUCHED]->(session),
       (c7:Claim {id: 'C-7', kind: 'fix', status: 'refuted',
                  text: 'Raising the cache TTL fixes the checkout timeout'}),
       (inc12)-[:HAS_CAUSE]->(c7),
       (e41:Evidence {id: 'E-41', kind: 'ci_run', executed: true, sha: 'h1', exit_code: 1}),
       (c7)-[:REFUTED_BY]->(e41),
       (:Evidence {id: 'E-52', kind: 'test_run', executed: false, sha: 'h2'}),
       (e60:Evidence {id: 'E-60', kind: 'test_run', executed: true, sha: 'h2', exit_code: 0}),
       (:Evidence {id: 'E-61', kind: 'test_run', executed: true, sha: 'h1', exit_code: 0}),
       (:Evidence {id: 'E-62', kind: 'test_run', executed: true, sha: 'h2', exit_code: 1}),
       (e70:Evidence {id: 'E-70', kind: 'test_run', executed: true, sha: 'k1', exit_code: 0}),
       (e71:Evidence {id: 'E-71', kind: 'test_run', executed: true, sha: 'other', exit_code: 0}),
       (a3:Approval {id: 'A-3', status: 'stale', sha: 'h2'})-[:FOR]->(pr7),
       (a3)-[:CITES]->(e60),
       (a3)-[:RELIES_ON]->(c7),
       (a4:Approval {id: 'A-4', status: 'active', sha: 'h1'})-[:FOR]->(pr7),
       (a5:Approval {id: 'A-5', status: 'active', sha: 'k1'})-[:FOR]->(pr8),
       (a5)-[:CITES]->(e70),
       (a6:Approval {id: 'A-6', status: 'active', sha: 'm1'})-[:FOR]->(pr9),
       (a6)-[:CITES]->(e71)
"""


@pytest.fixture(scope="module")
def graph() -> str:
    db = connect()
    try:
        db.select_graph(GRAPH).delete()
    except Exception:  # noqa: BLE001 - graph may not exist yet
        pass
    db.select_graph(GRAPH).query(FIXTURE)
    yield GRAPH
    db.select_graph(GRAPH).delete()


def test_demo_pr_is_red_citing_e52_and_reports_a3_stale(graph: str) -> None:
    decision = decide_check(graph, 7, "h2", cited_evidence_ids=["E-52"])
    assert decision["conclusion"] == "failure"
    assert decision["blocked"] == [{"evidence": "E-52", "reason": "not executed", "cited_by": None}]
    assert decision["stale_approvals"] == [
        {"approval": "A-3", "reason": "marked stale"},
        {"approval": "A-4", "reason": "approved h1, head is h2"},
    ]
    assert decision["valid_approvals"] == []
    assert decision["comment"] is True
    assert [row["evidence"] for row in decision["refuted"]] == ["E-41"]


def test_cited_evidence_reasons(graph: str) -> None:
    decision = decide_check(
        graph, 7, "h2", cited_evidence_ids=["E-99", "E-61", "E-62", "E-60", "E-60"]
    )
    assert decision["blocked"] == [
        {"evidence": "E-99", "reason": "missing", "cited_by": None},
        {"evidence": "E-61", "reason": "ran on h1, head is h2", "cited_by": None},
        {"evidence": "E-62", "reason": "exit code 1", "cited_by": None},
    ]


def test_clean_pr_is_green_with_no_comment(graph: str) -> None:
    decision = decide_check(graph, 8, "k1", cited_evidence_ids=["E-70"])
    assert decision["conclusion"] == "success"
    assert decision["blocked"] == []
    assert decision["stale_approvals"] == []
    assert decision["valid_approvals"] == ["A-5"]
    assert decision["refuted"] == []
    assert decision["comment"] is False


def test_a_new_push_makes_the_approval_stale(graph: str) -> None:
    decision = decide_check(graph, 8, "k2")
    assert decision["conclusion"] == "failure"
    assert decision["stale_approvals"] == [{"approval": "A-5", "reason": "approved k1, head is k2"}]


def test_an_approval_citing_wrong_sha_evidence_blocks(graph: str) -> None:
    decision = decide_check(graph, 9, "m1")
    assert decision["conclusion"] == "failure"
    assert decision["blocked"] == [
        {"evidence": "E-71", "reason": "not an executed run on m1", "cited_by": "A-6"}
    ]
    assert decision["valid_approvals"] == []


def test_a_pr_with_no_approval_and_nothing_cited_is_silent(graph: str) -> None:
    decision = decide_check(graph, 10, "n1")
    assert decision["conclusion"] == "success"
    assert decision["comment"] is False


def test_a_pr_not_in_the_graph_is_neutral(graph: str) -> None:
    decision = decide_check(graph, 404, "z1")
    assert decision["conclusion"] == "neutral"
    assert decision["comment"] is False


def test_payload_cites_ids_and_carries_no_prose_from_a_model(graph: str) -> None:
    decision = decide_check(graph, 7, "h2", cited_evidence_ids=["E-52"])
    payload = check_run_payload(decision)
    assert payload["name"] == "sheldon"
    assert payload["head_sha"] == "h2"
    assert payload["status"] == "completed"
    assert payload["conclusion"] == "failure"
    summary = payload["output"]["summary"]
    assert "blocked: E-52 not executed" in summary
    assert "stale: A-3 marked stale" in summary
    assert "refuted: C-7 by E-41 (INC-12, via checkout/session.py)" in summary


def test_clean_payload_is_green() -> None:
    decision = {
        "pr": 8,
        "head_sha": "k1",
        "conclusion": "success",
        "blocked": [],
        "stale_approvals": [],
        "valid_approvals": ["A-5"],
        "refuted": [],
        "comment": False,
    }
    payload = check_run_payload(decision)
    assert payload["conclusion"] == "success"
    assert payload["output"]["title"] == "sheldon: clear"


# check-e2e: the demo's step 2 on the seed, through the webhook with the real
# pr-ingest. Approval A-3 going stale (step 3) needs W2, which is still a stub.

SEED = "test_check_e2e_seed"
TAKE = "test_check_e2e_take"


class _GitHub:
    def __init__(self) -> None:
        self.check_runs: list[dict] = []

    def changed_paths(self, repo: str, number: int) -> list[str]:
        del repo, number
        return ["checkout/cache.py"]

    def create_check_run(self, repo: str, payload: dict) -> None:
        del repo
        self.check_runs.append(payload)

    def create_status(self, repo: str, sha: str, payload: dict) -> None:
        raise AssertionError("check_run mode only")


@pytest.fixture()
def take() -> str:
    for key in (SEED, TAKE):
        try:
            connect().select_graph(key).delete()
        except Exception:  # noqa: BLE001 - graph may not exist yet
            pass
    copy_graph(load_seed(SEED), TAKE)
    yield TAKE
    for key in (SEED, TAKE):
        connect().select_graph(key).delete()


def _pr7(body: str) -> dict:
    return {
        "action": "edited",
        "repository": {"full_name": "demo/checkout"},
        "pull_request": {"number": 7, "head": {"sha": "b2"}, "body": body},
    }


def test_e2e_done_claim_citing_e52_gets_a_red_check(take: str) -> None:
    github = _GitHub()
    handle_event(
        "pull_request", _pr7("Done, all tests pass.\nEvidence: E-52"), github, lambda _: take
    )
    [payload] = github.check_runs
    assert payload["conclusion"] == "failure"
    assert payload["head_sha"] == "b2"
    summary = payload["output"]["summary"].splitlines()
    assert summary == [
        "blocked: E-52 not executed",
        "refuted: C-5 by E-41 (INC-12, via checkout/session.py)",
    ]


def test_e2e_citing_a_real_run_on_the_head_sha_turns_it_green(take: str) -> None:
    github = _GitHub()
    handle_event("pull_request", _pr7("Evidence: E-31"), github, lambda _: take)
    [payload] = github.check_runs
    assert payload["conclusion"] == "success"
    assert payload["output"]["summary"] == "refuted: C-5 by E-41 (INC-12, via checkout/session.py)"


def test_e2e_after_w2_refutes_c7_the_approval_is_reported_stale(take: str) -> None:
    from sheldon.belief.refute import refute_claim

    assert refute_claim(take, "C-7", ["E-60"], "ci", "ci", "CI-60")
    github = _GitHub()
    handle_event("pull_request", _pr7("Evidence: E-31"), github, lambda _: take)
    [payload] = github.check_runs
    assert payload["conclusion"] == "failure"
    assert payload["output"]["summary"].splitlines() == [
        "stale: A-3 marked stale",
        "refuted: C-5 by E-41 (INC-12, via checkout/session.py)",
        "refuted: C-7 by E-60 (INC-12, via checkout/session.py)",
    ]
