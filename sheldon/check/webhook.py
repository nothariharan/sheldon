"""GitHub webhook for the PR check.

Status: wired and tested with a fake GitHub client, with both a fake and the
real pr-ingest. Not yet run against GitHub.

The flow for a pull_request event: pr-ingest writes the PR's changed files,
``decide_check`` reads the graph, and the result is posted as a check run
(GitHub App token) or a commit status (any token that can write statuses).
"""

import hashlib
import hmac
import json
import re
from collections.abc import Callable
from typing import Protocol

from sheldon.check.app import CHECK_NAME, check_run_payload, decide_check
from sheldon.pr import ingest_pull_request

# Actions that change the head sha or the PR body that carries cited ids.
PR_ACTIONS = frozenset({"opened", "reopened", "synchronize", "edited"})

# Only an explicit "Evidence:" line counts as citing. Ids mentioned in prose,
# such as "refuted by E-41", are not claims the PR makes.
_EVIDENCE_LINE = re.compile(r"^\s*evidence\s*:(.*)$", re.IGNORECASE | re.MULTILINE)
_EVIDENCE_ID = re.compile(r"\bE-\d+\b")

# GitHub rejects a commit status description over 140 characters.
_STATUS_DESCRIPTION_MAX = 140
_STATUS_STATE = {"success": "success", "failure": "failure", "neutral": "pending"}


class GitHub(Protocol):
    def changed_paths(self, repo: str, number: int) -> list[str]: ...

    def create_check_run(self, repo: str, payload: dict) -> None: ...

    def create_status(self, repo: str, sha: str, payload: dict) -> None: ...


def repo_graph(full_name: str) -> str:
    """One graph key per repo, as docs/plan/deep.md section 3 names it."""
    return f"sheldon:{full_name}"


def verify_signature(secret: bytes, body: bytes, header: str | None) -> bool:
    """Check ``X-Hub-Signature-256`` against the raw request body."""
    if not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


def cited_evidence_ids(body: str | None) -> list[str]:
    """Evidence ids from ``Evidence:`` lines in the PR body, deduped, in order."""
    ids: list[str] = []
    for line in _EVIDENCE_LINE.findall(body or ""):
        ids.extend(_EVIDENCE_ID.findall(line))
    return list(dict.fromkeys(ids))


def status_payload(decision: dict) -> dict:
    """Commit status body for tokens that cannot create check runs."""
    summary = check_run_payload({"head_sha": None, **decision})["output"]
    first_line = summary["summary"].splitlines()[0] if decision["conclusion"] == "failure" else ""
    return {
        "state": _STATUS_STATE[decision["conclusion"]],
        "context": CHECK_NAME,
        "description": (first_line or summary["title"])[:_STATUS_DESCRIPTION_MAX],
    }


def handle_event(
    event: str,
    payload: dict,
    github: GitHub,
    graph_for_repo: Callable[[str], str] = repo_graph,
    ingest: Callable[[str, int, str, list[str]], int] = ingest_pull_request,
    mode: str = "check_run",
) -> dict | None:
    """Ingest, decide, and post for one pull_request event. Other events return None."""
    if event != "pull_request" or payload.get("action") not in PR_ACTIONS:
        return None
    repo = payload["repository"]["full_name"]
    pr = payload["pull_request"]
    number, head_sha = pr["number"], pr["head"]["sha"]
    graph = graph_for_repo(repo)

    ingest(graph, number, head_sha, github.changed_paths(repo, number))
    decision = decide_check(graph, number, head_sha, cited_evidence_ids(pr.get("body")))
    if mode == "status":
        github.create_status(repo, head_sha, status_payload(decision))
    else:
        github.create_check_run(repo, check_run_payload(decision))
    return decision


def make_app(
    secret: bytes,
    github: GitHub,
    graph_for_repo: Callable[[str], str] = repo_graph,
    ingest: Callable[[str, int, str, list[str]], int] = ingest_pull_request,
    mode: str = "check_run",
):
    """WSGI app for POST /webhook. A bad signature is 401 and touches nothing."""

    def app(environ, start_response):
        def reply(status: str, body: dict):
            start_response(status, [("Content-Type", "application/json")])
            return [json.dumps(body).encode()]

        if environ.get("REQUEST_METHOD") != "POST" or environ.get("PATH_INFO") != "/webhook":
            return reply("404 Not Found", {"error": "POST /webhook"})
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length)
        if not verify_signature(secret, body, environ.get("HTTP_X_HUB_SIGNATURE_256")):
            return reply("401 Unauthorized", {"error": "bad signature"})

        event = environ.get("HTTP_X_GITHUB_EVENT", "")
        decision = handle_event(
            event, json.loads(body or b"{}"), github, graph_for_repo, ingest, mode
        )
        if decision is None:
            return reply("200 OK", {"ignored": event})
        return reply("200 OK", {"conclusion": decision["conclusion"]})

    return app
