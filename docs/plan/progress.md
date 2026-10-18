# Progress

Sun 18 Oct 2026. Main is `ec328d9`. Submission closes 11:59 PM IST. The last about 3 hours are for the video, the form, the README, and the fresh public push.

A row is built when the code is on main and a test exercises it. Merged since the last note: #44 (smoke runs W1, W2, and R1 on the seed), #42 (session-start hook), #43 (fail-closed for commit, push, and done), #46 (banner, `sheldon --help`, and plain text off a terminal), #47 (`sheldon` with no args on a terminal opens a prompt), #48 (status lines), #49 (cli-ux colors, frames, and the spinner), and #50 (the spinner tests patch the spinner `sheldon run` calls).

## Suite on main

```
ruff check sheldon tests eval
All checks passed!

pytest
200 passed in 51.63s

pytest tests/test_smoke.py
3 passed in 0.12s
```

Run on `ec328d9` plus this change, against `falkordb/falkordb:v4.22.1`. The trap suite is inside that pytest run.

## Overall

21 of 33 `TASKS.md` rows are built and tested. That is 64%. Counted on `ec328d9` plus this change (`eval-traps` is built). A row counts as built only when this note says built, not partly built.

| Person | Rows | Built and tested | Left | % built |
|---|---|---|---|---|
| Akshat (aksbhaskar) | 7 | 4 | 3 | 57% |
| Hariharan (nothariharan) | 9 | 8 | 1 | 89% |
| Amaan | 9 | 3 | 6 | 33% |
| Satyansh | 9 | 7 | 2 | 78% |

`cli-ux` is shared, so it is counted under Akshat and under Satyansh. That is why the person rows sum to 34.

Commits on main, 50 total, counted on `ec328d9`: Hariharan 28 (56%), Akshat Bhaskar 14 (28%), Satyansh Gaur 7 (14%), Cursor Agent 1 (2%). Amaan has 0.

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
| evidence-run | built and tested. `sheldon run -- <cmd>` (console script `sheldon = sheldon.cli:console_main`) records the real exit code, sha, and output digest (#32). |
| claim-lease | built and tested. `handoff_task` stores `to_agent` and `note` (#35). |
| provenance | built and tested |
| preflight | built and tested. On a database error, commit, push, and done return `block` and exit 2 (`SHELDON_FAIL_OPEN=1` keeps warn). A read returns `warn` and exit 0. |
| capsule | built and tested. The text includes `sheldon run -- pytest`. Session start restores it: `python -m sheldon.hooks.session_start` and `hooks/claude-session-start.json` (#42). |
| resume | built and tested |
| compose | built and tested. After a refute the comment cites the `REFUTED_BY` evidence. On the seed that is E-60, not E-30 (#41). |
| check-run | partly built. Decision, webhook, and seed path are tested. Not run against GitHub. |
| eval-count | partly built as a scripted dry run. Paired measured runs are cut for submission. |
| race-tests | built and tested. Both races pass. The old "xfail until the write lands" line was stale. |
| ci | built. The workflow runs on pull requests. |
| check-e2e | built and tested on main. |
| gate-tests | built and tested |
| provenance-tests | built and tested |
| eval-harness | partly built. Reset and the repeated-step count are tested. Paired runs are cut for submission. |
| eval-traps | built and tested. `python -m eval.traps` on the 21 scenarios in `eval/traps/scenarios.json`. The table is in the README. The test does not assert scores. |
| package-name | not started. Cut for submission. |
| demo-submit | not started. `docs/plan/demo.md` is a draft. The video and the portal submission are not. |
| public-repo | not started |
| website | not started |
| web-ui | not started |
| cli-ux | built and tested. Banner, help, prompt, plain fallback (#46, #47), ANSI colors, frames, spinner with rich. |

## Deep-plan components

| Component | State |
|---|---|
| W1 `approve` | built and tested |
| W2 `refute_claim` | built and tested |
| W3 `claim_done` | built and tested |
| R1 recall | built and tested |
| S0 | partly built (keyword). Vector cut for submission. |
| `retrieve` / `q_star` | not started |
| evidence run | built and tested. `sheldon run` (#32). |
| claim and lease | built and tested, including handoff (#35). |
| provenance `writes_with_provenance` | built and tested |
| retrieval | R1 built. S0 keyword built. Vector and `q_star` not in Sunday's demo. |
| check | partly built. Seed path tested. Live GitHub not started. |
| CLI | partly built. #46 added the banner, `sheldon --help`, and plain text when stdout is not a terminal. #47 is merged: on a terminal, `sheldon` with no args opens a prompt for preflight, run, check, and help. Off a terminal, no args is still a usage error. `sheldon run` is built. `sheldon init` and `sheldon ingest` are not. |
| demo seed | built and tested |
| demo script | partly built. Draft only. |
| eval | partly built. Definition and dry run are tested. Paired pass rate and token totals are not measured. The trap-suite table is in the README. |
| README pieces | built. Data model, Cypher list, AI disclosure, credits, and `LICENSE` are on main (#33). |

## Review notes

Checked against main on this date.

| Claim | Result |
|---|---|
| The `sheldon run` command does not exist. The capsule tells agents to run it. Only `record_run` exists. | Fixed by #32. `pyproject.toml` has `sheldon = "sheldon.cli:console_main"`, and `sheldon run -- pytest` records one executed Evidence node. |
| No session-start hook restores the capsule. | Fixed by #42. `python -m sheldon.hooks.session_start` prints `capsule()` for `SHELDON_TASK`. `hooks/claude-session-start.json` is the `SessionStart` snippet (startup, resume, clear, compact). |
| Commit, push, and done do not fail closed when the database is down. | Fixed by #43 for commit, push, and done. `preflight` returns `block` and exit 2 (`test_preflight_blocks_on_db_outage`). `SHELDON_FAIL_OPEN=1` keeps warn. Reads (recall, resume, and the check summary) still warn (`test_a_read_warns_on_an_outage`). |
| The eval is a scripted dry run with no paired runs, so no eval numbers go in the pitch. | Paired pass rate and token totals are still unmeasured. `run_paired_eval` is `simulate_retry_block`. The README benchmark is the trap-suite table from `python -m eval.traps`. |
| After the cascade, the PR comment cites E-30 as refuting C-7, but E-30 supported it. | Fixed by #41. `compose` cites the `REFUTED_BY` evidence. On the seed the comment says C-7 was refuted by E-60, not E-30 (`tests/answers/test_compose.py`). The check summary still keeps `REFUTED_BY` rows. |
| `deep.md` line 84 claims fail-closed, and line 88 overstates the W2 run. | Fixed by #43 for the fail-closed claim. Line 84 now says commit, push, and done fail closed, and reads (recall, resume, and the check summary) fail open with a warning. Line 88 was corrected earlier: the W2 statement is tested on the pinned v4.22.1 image. |
| The README is missing the data model, the Cypher list, the AI disclosure, a LICENSE file, and credit for code-graph and RepoGraph. | Fixed by #33. README has Graph data model, Cypher files, AI disclosure, and Credits sections, and `LICENSE` is in the repo root. |

Rows marked Fixed were true at 10 AM and are fixed on main. Rows marked Holds are still true.

## On track?

Not every station in `docs/plan/deep.md` is built. The retry block (`sheldon/preflight.py`), the evidence gate (W1 and W3), and the cascade (`refute_claim`) are built and tested. Ingest, the S0 vector half, paired eval runs, and a live GitHub App are not. The README benchmark is the trap-suite table. Paired pass rate and token totals are not in it. Use the fallbacks in `docs/plan/demo.md` when a step is not recorded: run preflight by hand, run `python -m sheldon.check` if the webhook is not live, and skip the ingest step.

Hariharan has the most built rows (8 of 9). Amaan has no commit on main; schema stays with him because `schema.py` is his file. Satyansh's compose citation and the session-start hook are on main. Paired eval runs stay cut. The trap suite is this change.

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
5. Clean-clone install is on main: `requirements.txt` pins the FalkorDB client, `requirements-dev.txt` pins pytest and ruff, and `./scripts/setup.sh` is the one command (#34).
6. In the last window, push a fresh public repo.

Satyansh:

1. `compose` cites the `REFUTED_BY` evidence (E-60 on the seed). Done (#41).
2. `cli-ux` colors, frames, and the spinner are built (#49). The spinner stays off for `--json`, and when stdout or stderr is not a terminal.
3. The session-start hook is built (`python -m sheldon.hooks.session_start`). Commit, push, and done fail closed on a database error. Reads (recall, resume, and the check summary) fail open with a warning.

Akshat:

1. Record the demo. No dry-run eval numbers, no eval table in the video.
2. Submit the form by 11:00 PM IST, including the website link.
3. `cli-ux` with Satyansh ([cli-spec.md](cli-spec.md)). #46 is merged: the banner, `sheldon --help`, and the non-TTY / `NO_COLOR` fallback. #47 is merged: the interactive prompt when `sheldon` has no args on a terminal.

Amaan:

1. `website`. Landing page in [ui-spec.md](ui-spec.md), from the patterns in [ui-reference.md](ui-reference.md). Must ship by 9 PM IST: hero, the three recorded terminal replays, the static seed graph, how it works, install, and the repo link.
2. `web-ui`. The read-only seed view in the same spec, after the landing page if time remains.

The schema constraint test is cut for submission. The row stays in `TASKS.md`.
