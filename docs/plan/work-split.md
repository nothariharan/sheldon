# Work split

Proposed, Akshat to confirm. Written Sat 17 Oct 2026. Submission closes Sun 18 Oct 2026, 11:59 PM IST: repo plus a demo video.

## Who does what

Owners are proposed. Akshat confirms them. The owner of a unit owns its tests. Detail is in [`TASKS.md`](../../TASKS.md). How to run a test is in [`TESTING.md`](../../TESTING.md).

| Person (proposed) | Units | Test files they own | First pickup |
|---|---|---|---|
| Akshat (lead) | S0, R1 recall, check run, CI workflow. Demo and submission are guesses. | `tests/retrieval/`, `tests/check/test_check_run.py`, `.github/workflows/ci.yml` | Confirm the split. Then S0. Then the check-run skeleton. |
| Hariharan | W1, W3, W2, `sheldon run`, claim and lease, provenance. Public repo is a guess. | `tests/gate/`, `tests/belief/test_refute.py`, `tests/evidence/`, `tests/coordination/test_claim.py`, `tests/test_provenance.py` | W1, W3, and W2 wiring, plus provenance. The queries ran. The functions are to build. |
| Amaan | Docker smoke test, schema, ingest, pr-ingest, seed, race tests. Package name is a guess. | `tests/test_smoke.py`, `tests/test_races.py`, `tests/schema/`, `tests/memory/`, `tests/pr/`, `tests/seed/` | `smoke-docker`, then schema and seed. |
| Satyansh | Eval definition, with/without eval harness, preflight, capsule, resume, compose. | `tests/eval/` (at least 3 runs per arm, pass rate and tokens), `tests/test_preflight.py`, `tests/mcp/`, `tests/test_capsule.py`, `tests/coordination/test_resume.py`, `tests/answers/` | `eval-def` tonight, before any count. Then the preflight skeleton. |

Core rows follow the build plan. Where a task had no owner yet, the name is a guess and the `TASKS.md` cell says so.

## Ground rules

Scope freeze: p0–p4 plus the eval, plus pr-ingest, the GitHub App check, provenance on the gate, and MCP preflight. If time runs short, cut UI polish first, then the under-the-hood demo step. Do not cut the gate, the cascade, the retry block, or the eval.

Eval freeze: Sun 1:00 PM IST (proposed). After that, only bug fixes go into the code the eval runs on.

Engine pin: `falkordb/falkordb:v4.22.1`. Never `latest`.

One branch per `TASKS.md` row (`area/short-name`). PR into `main`. Merge on green CI.

Roadmap, not by Sunday: model allowlist, escalate-on-stall, staged harness, pre-commit and Stop hooks, falkordblite parity, hosted MCP, wiring the `sameAction` UDF, diff-scope evidence, base-fail/head-pass plus a test-file hash.

## Who

**Akshat** (lead) — S0 baseline, R1 recall, GitHub App webhook to the check run. Demo script, recording, slides, and the portal submission are guesses on top of that.

**Hariharan** — W1 and W3 evidence gate, W2 cascade, claim and lease, provenance, `sheldon run`. Public-repo push is a guess: it has to be a fresh repo, because this history still contains notes that should not ship.

**Amaan** — Docker smoke test first, then schema, constraints, ingest, pr-ingest, the seed, and the frozen `GRAPH.COPY` snapshot. Claiming the `sheldon-ai` package name is a guess.

**Satyansh** — `sheldon-mcp`, preflight retry block, capsule re-inject, resume, compose, and the with/without eval.

## Order (IST)

| When | Akshat | Hariharan | Amaan | Satyansh |
|---|---|---|---|---|
| Tonight, Sat 7:30 PM – 2 AM | Confirm the split. S0. Check-run skeleton. | W1/W3 gate, W2 cascade, provenance field. | Docker smoke test, schema, seed. | Eval definition. Preflight skeleton. |
| Sun 8 AM – 1 PM | R1 wired into the check run. Check run green on the seed. | `sheldon run`, claim, lease, gate tests. | pr-ingest and the frozen snapshot. | PreToolUse retry block, capsule, resume. |
| Sun 1 PM | Eval freeze. Dry-run the five demo steps before any eval run. | | | |
| Sun 1 – 9 PM | Demo script, slides, recording 6–9 PM. | Bug fixes. README sections for the gate and cascade. | Engine bugs. Install path in the README. | Eval runs 1–5 PM. Numbers to Akshat by 6 PM. |
| Sun 9 – 11:59 PM | Final video. Submit by 11 PM. | Push a clean main to a fresh public repo after the scan. | Fresh clone and install test on that repo. | Numbers in the video match the eval table. |

Critical path: Docker smoke test, then schema and seed, then W1/W2/W3 plus preflight by Sun 1 PM, then the eval, then the recording, then the scan and the public repo. If the gate and preflight are not green by Sun 1 PM, cut the under-the-hood demo step, not the eval. If the eval cannot reach 3 runs per arm, the numbers slide says "to be measured" and angle 3 stays "safer at the same quality".

## Pre-ship checks

Research checks only. Humans own every build task, the push, and the submission.

| Check | Done when |
|---|---|
| Re-open every quote used on slides, README, or the video | The wording and date match the live source, or the quote is cut |
| Recheck every paper id and number used in public | The number is in the paper and means what we say |
| Fact-check the plan pages, README, and slides | Every claim matches its source, or it is cut |
| Scan the repo and submission text before publish | The scan is clean, then Hariharan pushes a fresh public repo |
