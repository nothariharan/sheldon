"""Run the PR check from a terminal: ``python -m sheldon.check``.

Prints what the check run would post, without GitHub. This is the demo's
fallback when the webhook is not live (docs/plan/demo.md, step 2).

    python -m sheldon.check --repo owner/name 8 <head-sha> --evidence E-52
    python -m sheldon.check --graph sheldon:owner/name 8 <head-sha> --json

Exit code is 1 when the check fails, else 0.
"""

import argparse
import sys

from sheldon.check.app import check_run_payload, decide_check
from sheldon.check.webhook import repo_graph
from sheldon.output import CommandResult, emit


def check_result(
    graph: str,
    pr: int,
    head_sha: str,
    evidence: list[str],
) -> CommandResult:
    """Return the check decision. ``data`` is the check-run payload."""
    decision = decide_check(graph, pr, head_sha, evidence)
    payload = check_run_payload(decision)
    title, conclusion = payload["output"]["title"], payload["conclusion"]
    text = f"{title} ({conclusion}) PR {pr} at {head_sha}\n{payload['output']['summary']}"
    return CommandResult(
        command="check",
        exit_code=1 if decision["conclusion"] == "failure" else 0,
        data=payload,
        text=text,
        json_style="payload",
    )


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sheldon.check", description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--repo", help="owner/name. Uses the graph key sheldon:<owner>/<name>")
    target.add_argument("--graph", help="FalkorDB graph key")
    parser.add_argument("pr", type=int, help="pull request number")
    parser.add_argument("head_sha", help="head commit sha to check")
    parser.add_argument("--evidence", nargs="*", default=[], help="evidence ids the PR cites")
    parser.add_argument("--json", action="store_true", help="print the check-run payload")
    args = parser.parse_args(argv)

    graph = args.graph or repo_graph(args.repo)
    result = check_result(graph, args.pr, args.head_sha, args.evidence)
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    sys.exit(main())
