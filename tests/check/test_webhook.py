"""Webhook: signature, cited ids, and one pull_request event end to end.

GitHub is a fake that records what would be posted. pr-ingest is a fake that
writes PR -[:CHANGES]-> File the way Amaan's row will, so the decision runs on
a graph the webhook itself updated.
"""

import hashlib
import hmac
import io
import json

import pytest

from sheldon.check.webhook import (
    cited_evidence_ids,
    handle_event,
    make_app,
    status_payload,
    verify_signature,
)
from sheldon.db import connect

GRAPH = "test_check_webhook"
SECRET = b"test-secret"

FIXTURE = """
CREATE (:File {path: 'docs/readme.md'}),
       (e70:Evidence {id: 'E-70', kind: 'test_run', executed: true, sha: 'k1', exit_code: 0}),
       (:Evidence {id: 'E-52', kind: 'test_run', executed: false, sha: 'k1'}),
       (a5:Approval {id: 'A-5', status: 'active', sha: 'k1'})-[:CITES]->(e70)
"""


class FakeGitHub:
    def __init__(self, paths: list[str]) -> None:
        self.paths = paths
        self.check_runs: list[tuple[str, dict]] = []
        self.statuses: list[tuple[str, str, dict]] = []

    def changed_paths(self, repo: str, number: int) -> list[str]:
        del repo, number
        return self.paths

    def create_check_run(self, repo: str, payload: dict) -> None:
        self.check_runs.append((repo, payload))

    def create_status(self, repo: str, sha: str, payload: dict) -> None:
        self.statuses.append((repo, sha, payload))


def fake_ingest(graph: str, number: int, head_sha: str, changed_paths: list[str]) -> int:
    target = connect().select_graph(graph)
    target.query(
        "MERGE (pr:PR {number: $n}) SET pr.head_sha = $sha "
        "WITH pr UNWIND $paths AS path MERGE (f:File {path: path}) MERGE (pr)-[:CHANGES]->(f)",
        {"n": number, "sha": head_sha, "paths": changed_paths},
    )
    target.query(
        "MATCH (pr:PR {number: $n}), (a:Approval {id: 'A-5'}) MERGE (a)-[:FOR]->(pr)",
        {"n": number},
    )
    return len(changed_paths)


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


def _event(action: str, sha: str, body: str = "") -> dict:
    return {
        "action": action,
        "repository": {"full_name": "team/demo"},
        "pull_request": {"number": 8, "head": {"sha": sha}, "body": body},
    }


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()


def test_verify_signature() -> None:
    body = b'{"zen": "ok"}'
    assert verify_signature(SECRET, body, _sign(body))
    assert not verify_signature(SECRET, body, _sign(b"other"))
    assert not verify_signature(SECRET, body, None)
    assert not verify_signature(SECRET, body, "sha1=abc")


def test_cited_evidence_ids_reads_only_the_evidence_line() -> None:
    body = "Fixes the TTL bug. Refuted earlier by E-41.\n\nEvidence: E-52, E-60 E-52\n"
    assert cited_evidence_ids(body) == ["E-52", "E-60"]
    assert cited_evidence_ids("evidence:E-7") == ["E-7"]
    assert cited_evidence_ids("no ids here, only E-41 in prose") == []
    assert cited_evidence_ids(None) == []


def test_synchronize_ingests_decides_and_posts_a_check_run(graph: str) -> None:
    github = FakeGitHub(["docs/readme.md"])
    decision = handle_event(
        "pull_request",
        _event("synchronize", "k1", "Evidence: E-70"),
        github,
        graph_for_repo=lambda repo: graph,
        ingest=fake_ingest,
    )
    assert decision["conclusion"] == "success"
    assert github.check_runs == [
        (
            "team/demo",
            {
                "name": "sheldon",
                "head_sha": "k1",
                "status": "completed",
                "conclusion": "success",
                "output": {
                    "title": "sheldon: clear",
                    "summary": "No refuted fix, stale approval, or unproven evidence.",
                },
            },
        )
    ]


def test_an_unexecuted_cited_run_turns_the_check_red(graph: str) -> None:
    github = FakeGitHub(["docs/readme.md"])
    decision = handle_event(
        "pull_request",
        _event("edited", "k1", "Done, all tests pass.\nEvidence: E-52"),
        github,
        graph_for_repo=lambda repo: graph,
        ingest=fake_ingest,
    )
    assert decision["conclusion"] == "failure"
    assert "blocked: E-52 not executed" in github.check_runs[0][1]["output"]["summary"]


def test_status_mode_posts_a_commit_status(graph: str) -> None:
    github = FakeGitHub(["docs/readme.md"])
    handle_event(
        "pull_request",
        _event("opened", "k2"),
        github,
        graph_for_repo=lambda repo: graph,
        ingest=fake_ingest,
        mode="status",
    )
    assert github.check_runs == []
    assert github.statuses == [
        (
            "team/demo",
            "k2",
            {
                "state": "failure",
                "context": "sheldon",
                "description": "stale: A-5 approved k1, head is k2",
            },
        )
    ]


def test_other_events_and_actions_are_ignored(graph: str) -> None:
    github = FakeGitHub([])
    hooks = {"graph_for_repo": lambda repo: graph, "ingest": fake_ingest}
    assert handle_event("ping", {"zen": "hi"}, github, **hooks) is None
    assert handle_event("pull_request", _event("closed", "k1"), github, **hooks) is None
    assert github.check_runs == []


def test_status_payload_maps_neutral_to_pending() -> None:
    payload = status_payload(
        {
            "conclusion": "neutral",
            "blocked": [],
            "stale_approvals": [],
            "refuted": [],
        }
    )
    assert payload == {
        "state": "pending",
        "context": "sheldon",
        "description": "sheldon: PR not in the graph yet",
    }


def _call(app, body: bytes, signature: str | None, event: str = "pull_request"):
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/webhook",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "HTTP_X_GITHUB_EVENT": event,
    }
    if signature is not None:
        environ["HTTP_X_HUB_SIGNATURE_256"] = signature
    status: list[str] = []
    out = b"".join(app(environ, lambda s, headers: status.append(s)))
    return status[0], out


def test_wsgi_app_rejects_a_bad_signature_and_accepts_a_good_one(graph: str) -> None:
    github = FakeGitHub(["docs/readme.md"])
    app = make_app(SECRET, github, graph_for_repo=lambda repo: graph, ingest=fake_ingest)
    body = json.dumps(_event("synchronize", "k1", "Evidence: E-70")).encode()

    status, _ = _call(app, body, _sign(b"tampered"))
    assert status.startswith("401")
    assert github.check_runs == []

    status, out = _call(app, body, _sign(body))
    assert status.startswith("200")
    assert json.loads(out) == {"conclusion": "success"}
    assert len(github.check_runs) == 1

    status, out = _call(app, b"{}", _sign(b"{}"), event="ping")
    assert status.startswith("200")
    assert json.loads(out) == {"ignored": "ping"}
