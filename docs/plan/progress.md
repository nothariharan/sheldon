# Progress

Sun 18 Oct 2026. Main is `434c481`. Submission closes 11:59 PM IST. The last about 3 hours are for the video, the form, the README, and the fresh public push.

A row is built when the code is on main and a test exercises it. Merged since the last note: #44 (smoke runs W1, W2, and R1 on the seed), #42 (session-start hook), #43 (fail-closed for commit, push, and done), and #46 (banner, `sheldon --help`, and plain text off a terminal). Open: #47 (`sheldon` with no args on a terminal opens a prompt).

## Suite on main

```
ruff check sheldon tests
All checks passed!

pytest
151 passed, 1 error in 4.21s
ERROR tests/check/test_check_run.py::test_e2e_done_claim_citing_e52_gets_a_red_check
redis.exceptions.ResponseError: GRAPH.COPY failed, could not fork

pytest tests/test_smoke.py
2 passed in 0.09s
```

The error is in the check end-to-end fixture, before the assertion. Smoke's own `GRAPH.COPY` passed.

## Overall

16 of 29 `TASKS.md` rows are built and tested. That is 55%.

| Person | Rows | Built and tested | Left | % built |
|---|---|---|---|---|
| Akshat (aksbhaskar) | 6 | 3 | 3 | 50% |
| Hariharan (nothariharan) | 9 | 7 | 2 | 78% |
| Amaan | 7 | 3 | 4 | 43% |
| Satyansh | 7 | 3 | 4 | 43% |

Commits on main, 29 total: Hariharan 12 (41%), Akshat Bhaskar 10 (34%), Satyansh Gaur 6 (21%), Cursor Agent 1 (3%). Amaan has 0.

## Rows

| Row | State |
|---|---|
| smoke-docker | partly built. Module version, `GRAPH.COPY`, and W1, W2, and R1 on the seed are tested (#44). `UNIQUE` is not in the smoke file. |
| schema | partly built. Enums and the image pin are on main. No test applies the constraints. |
| eval-def | built and tested |
| ingest | not started (`record_event` raises). Cut for submission. |
| pr-ingest | built and tested |
| seed | built and tested |
| s0 | partly built. Keyword half is tested on a fixture. Vector half is cut for submission. |
| r1-recall | built and tested |
| w1-approve | built and tested |
| w2-cascade | built and tested. `refute_claim` is the tested write. `refute_hypothesis` is still the old sketch. |
| w3-done | built and tested |
| evidence-run | partly built. `record_run` is tested. The `sheldon run` command is not started. |
| claim-lease | built and tested. `handoff_task` is partly built: it drops `to_agent` and `note`. |
| provenance | built and tested |
| preflight | built and tested. On a database error, commit, push, and done return `block` and exit 2 (`SHELDON_FAIL_OPEN=1` keeps warn). A read returns `warn` and exit 0. |
| capsule | built and tested. The text includes `sheldon run -- pytest`. Session start restores it: `python -m sheldon.hooks.session_start` and `hooks/claude-session-start.json` (#42). |
| resume | built and tested |
| compose | built and tested. After a refute the comment cites the `REFUTED_BY` evidence. On the seed that is E-60, not E-30 (#41). |
| check-run | partly built. Decision, webhook, and seed path are tested. Not run against GitHub. This run's seed copy failed with `GRAPH.COPY could not fork`. |
| eval-count | partly built as a scripted dry run. Paired measured runs are cut for submission. |
| race-tests | built and tested. Both races pass. The old "xfail until the write lands" line was stale. |
| ci | built. The workflow runs on pull requests. |
| check-e2e | built and tested on main. This local run did not reach the assertion. |
| gate-tests | built and tested |
| provenance-tests | built and tested |
| eval-harness | partly built. Reset and the repeated-step count are tested. Paired runs are cut for submission. |
| package-name | not started. Cut for submission. |
| demo-submit | not started. `docs/plan/demo.md` is a draft. The video and the portal submission are not. |
| public-repo | not started |

## Deep-plan components

| Component | State |
|---|---|
| W1 `approve` | built and tested |
| W2 `refute_claim` | built and tested |
| W3 `claim_done` | built and tested |
| R1 recall | built and tested |
| S0 | partly built (keyword). Vector cut for submission. |
| `retrieve` / `q_star` | not started |
| evidence run | partly built. Producer only. |
| claim and lease | built and tested. Handoff partly built. |
| provenance `writes_with_provenance` | built and tested |
| retrieval | R1 built. S0 keyword built. Vector and `q_star` not in Sunday's demo. |
| check | partly built. Seed path tested. Live GitHub not started. |
| CLI | partly built. #46 added the banner, `sheldon --help`, and plain text when stdout is not a terminal. #47 is open: `sheldon` with no args on a terminal opening a prompt. `sheldon run` is built. `sheldon init` and `sheldon ingest` are not. |
| demo seed | built and tested |
| demo script | partly built. Draft only. |
| eval | partly built. Definition and dry run are tested. No paired measured runs, so no eval numbers in the pitch. |
| README pieces | not started. See the review notes below. |

## Review notes

Checked against main on this date.

| Claim | Result |
|---|---|
| The `sheldon run` command does not exist. The capsule tells agents to run it. Only `record_run` exists. | Holds. No console script and no `sheldon run` module. `sheldon/capsule.py` sets the proving command to `sheldon run -- pytest`. |
| No session-start hook restores the capsule. | Fixed by #42. `python -m sheldon.hooks.session_start` prints `capsule()` for `SHELDON_TASK`. `hooks/claude-session-start.json` is the `SessionStart` snippet (startup, resume, clear, compact). |
| Commit, push, and done do not fail closed when the database is down. | Fixed by #43 for commit, push, and done. `preflight` returns `block` and exit 2 (`test_preflight_blocks_on_db_outage`). `SHELDON_FAIL_OPEN=1` keeps warn. Reads (recall, resume, and the check summary) still warn (`test_a_read_warns_on_an_outage`). |
| The eval is a scripted dry run with no paired runs, so no eval numbers go in the pitch. | Holds. `run_paired_eval` is `simulate_retry_block`. Pass rate and token totals are not measured. |
| After the cascade, the PR comment cites E-30 as refuting C-7, but E-30 supported it. | Fixed by #41. `compose` cites the `REFUTED_BY` evidence. On the seed the comment says C-7 was refuted by E-60, not E-30 (`tests/answers/test_compose.py`). The check summary still keeps `REFUTED_BY` rows. |
| `deep.md` line 84 claims fail-closed, and line 88 overstates the W2 run. | Fixed by #43 for the fail-closed claim. Line 84 now says commit, push, and done fail closed, and reads (recall, resume, and the check summary) fail open with a warning. Line 88 was corrected earlier: the W2 statement is tested on the pinned v4.22.1 image. |
| The README is missing the data model, the Cypher list, the AI disclosure, a LICENSE file, and credit for code-graph and RepoGraph. | Holds. `README.md` has none of those. There is no `LICENSE` file. `docs/plan/deep.md` section 2.1 does credit code-graph and RepoGraph. The README does not. |

Nothing in that list is false.

## On track?

Not on track for every station in `docs/plan/deep.md`. On track for a demo of the retry block, the evidence gate, and the cascade, if the must-do list below lands before recording and the pitch has no eval numbers. Use the fallbacks already written in `docs/plan/demo.md`: run preflight by hand, run `python -m sheldon.check` if the webhook is not live, and skip the ingest step.

About 11 hours remain before the last 3 hours. Hariharan has the most finished rows. No owner cell moved. The slipping work stays with the person who owns the file. Cuts free Satyansh from paired eval runs so the comment bug and the hooks come first. Amaan has no commit on main; schema stays with him because `schema.py` is his file.

## Cuts

Left in `TASKS.md`, marked `cut for submission`, not deleted:

- ingest
- S0 vector half
- eval-count paired measured runs
- eval-harness paired runs
- package-name

## What each person does next, in order

Hariharan:

1. `sheldon run` (#32) is done.
2. README (#33) is done.
3. Wire the MCP server so a real agent session calls preflight, `sheldon run`, and `claim_done` end to end. Done (#36).
4. Store `handoff_task` `note` and `to_agent`. Done (#35).
5. Clean-clone install: `requirements.txt` pins the FalkorDB client, `requirements-dev.txt` pins pytest and ruff, and `./scripts/setup.sh` is the one command.
6. In the last window, push a fresh public repo.

Satyansh:

1. Change `compose` so a refuted claim cites the `REFUTED_BY` evidence. On the seed, E-30 supported C-7. E-60 is the refuting run.
2. `cli-ux`, after the compose fix, with Akshat ([cli-spec.md](cli-spec.md)). Satyansh: spinners, colored blocked / passed / stale lines, and the preflight, `sheldon run`, check, and MCP frames through one shared output module.
3. The session-start hook is built (`python -m sheldon.hooks.session_start`). Commit, push, and done fail closed on a database error. Reads (recall, resume, and the check summary) fail open with a warning.

Akshat:

1. Record the demo. No dry-run eval numbers, no eval table in the video.
2. Submit the form by 11:00 PM IST, including the website link.
3. `cli-ux` with Satyansh ([cli-spec.md](cli-spec.md)). #46 is merged: the banner, `sheldon --help`, and the non-TTY / `NO_COLOR` fallback. #47 is open: the interactive prompt when `sheldon` has no args on a terminal.

Amaan:

1. `website`. Landing page in [ui-spec.md](ui-spec.md), from the patterns in [ui-reference.md](ui-reference.md). Must ship by 9 PM IST: hero, the three recorded terminal replays, the static seed graph, how it works, install, and the repo link.
2. `web-ui`. The read-only seed view in the same spec, after the landing page if time remains.

The schema constraint test is cut for submission. The row stays in `TASKS.md`.
