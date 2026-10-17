# check

Akshat. Status: `decide_check`, `check_run_payload`, and the webhook are wired and tested with fakes in `tests/check/`. pr-ingest is wired, so a live event now ingests for real. Nothing here has run on the seed or against GitHub (check-e2e row).

## Contract

`decide_check(graph, pr_number, head_sha, cited_evidence_ids=None)` reads the graph and returns `conclusion` (`success`, `failure`, or `neutral`), `blocked`, `stale_approvals`, `valid_approvals`, `refuted`, and `comment`. `check_run_payload` turns that into a GitHub Checks API body. Every line in it is built from ids in the decision. No LLM decides or writes the check.

- `failure`: a cited evidence id is missing, not executed, ran on another sha, or exited non-zero. Or an approval cites evidence that is not an executed run on this sha. Or the PR has approvals and none is `active` on this sha.
- `success`: none of the above. A PR with no approval and nothing cited passes, so the check is silent by default.
- `neutral`: the PR is not in the graph yet (pr-ingest has not run).
- `refuted` holds R1 rows with `REFUTED_BY`. They turn `comment` on and do not fail the check.

## From a terminal

`python -m sheldon.check --repo owner/name <pr> <head-sha> --evidence E-52` prints what the check would post, with no GitHub involved. `--json` prints the check-run payload. The exit code is 1 when the check fails. This is the demo's fallback when the webhook is not live.

## Webhook

`python -m sheldon.check.server` serves `POST /webhook`. Set `SHELDON_WEBHOOK_SECRET`, `GITHUB_TOKEN`, and optionally `SHELDON_CHECK_MODE` and `SHELDON_PORT`. On a `pull_request` event (opened, reopened, synchronize, edited) it verifies `X-Hub-Signature-256`, calls pr-ingest with the PR's changed files, runs `decide_check`, and posts the result.

- `SHELDON_CHECK_MODE=check_run` (default) needs a GitHub App installation token. A personal access token cannot create check runs.
- `SHELDON_CHECK_MODE=status` posts a commit status instead, which any token with status write access can do. `neutral` maps to `pending`.
- Cited ids come only from `Evidence:` lines in the PR body (`Evidence: E-52, E-60`). An id mentioned in prose is not a citation.
- The graph key is `sheldon:<owner>/<repo>` (`repo_graph`), from `docs/plan/deep.md` section 3.

## Gotchas

- Reads go through `sheldon.db.read` and `sheldon.retrieval.recall`. Do not copy R1 into this folder.
- This folder reads approvals. It never writes one. W1 (`sheldon.gate.approve`) is the only approval writer.
- Approval status strings are `schema.ApprovalStatus`.
- Not built: dismissed `Finding` fingerprints, so a dismissed finding is not suppressed yet.
