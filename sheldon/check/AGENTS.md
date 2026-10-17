# check

Akshat. Status: `decide_check` and `check_run_payload` are wired and tested on a fixture in `tests/check/test_check_run.py`. The GitHub App webhook and the HTTP post are to build. Neither has run on the seed (check-e2e row).

## Contract

`decide_check(graph, pr_number, head_sha, cited_evidence_ids=None)` reads the graph and returns `conclusion` (`success`, `failure`, or `neutral`), `blocked`, `stale_approvals`, `valid_approvals`, `refuted`, and `comment`. `check_run_payload` turns that into a GitHub Checks API body. Every line in it is built from ids in the decision. No LLM decides or writes the check.

- `failure`: a cited evidence id is missing, not executed, ran on another sha, or exited non-zero. Or an approval cites evidence that is not an executed run on this sha. Or the PR has approvals and none is `active` on this sha.
- `success`: none of the above. A PR with no approval and nothing cited passes, so the check is silent by default.
- `neutral`: the PR is not in the graph yet (pr-ingest has not run).
- `refuted` holds R1 rows with `REFUTED_BY`. They turn `comment` on and do not fail the check.

## Gotchas

- Reads go through `sheldon.db.read` and `sheldon.retrieval.recall`. Do not copy R1 into this folder.
- This folder reads approvals. It never writes one. W1 (`sheldon.gate.approve`) is the only approval writer.
- Approval status strings are `schema.ApprovalStatus`.
- Not built: dismissed `Finding` fingerprints, so a dismissed finding is not suppressed yet.
