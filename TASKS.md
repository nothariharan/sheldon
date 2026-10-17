# Tasks

Proposed split, Akshat to confirm. One owner per row. One branch per row: `area/short-name`. Edit the files in that row and leave the other rows' files alone.

The owner of a unit owns its tests. The Tests column names the file that branch must add or turn green. How to run them is [`TESTING.md`](TESTING.md).

Suite rows (`race-tests`, `ci`, `check-e2e`, `gate-tests`, `provenance-tests`, `eval-harness`) name those files again so the harnesses are easy to find. Same owner as the unit. Same branch as the unit, except `race-tests` and `ci`, which are their own branches.

Scope is the [plan](docs/plan/README.md). Do not add roadmap rows (model allowlist, Stop hooks, hosted MCP, `sameAction` wiring, diff-scope evidence, falkordblite parity).

Status words: **ran** is only W1, W2, and R1, and even those queries are not wired through a working function. **To build** is Sunday's scope. A stub is not a working feature. `ci` already runs on pull requests. That is the existing job, not a product station.

## Order and deadlines

Times are IST. Submission closes Sun 18 Oct 2026, 11:59 PM IST.

- Amaan's smoke test, schema, and seed go first. Everyone else builds on them.
- Satyansh writes `eval-def` before any count is quoted.
- Akshat shows the demo question failing on plain memory (S0) before treating R1 as the demo read.
- W1, W2, W3, and preflight are green by Sun 18 Oct 1:00 PM, then the eval runs. Recording is Sun 6–9 PM. The public repo is a fresh repo, Sun evening.

| ID | Owner (proposed) | Status | Files | Tests (owner) | Depends on | Done when |
|---|---|---|---|---|---|---|
| smoke-docker | Amaan | to build | `tests/test_smoke.py` | `tests/test_smoke.py` (Amaan) | none | On `falkordb/falkordb:v4.22.1` the script checks module `42201`, `GRAPH.COPY`, `timestamp()`, `UNIQUE` on `Claim.id` after an exact-match index, and the W1, W2, and R1 cases in `docs/plan/deep.md`. The module and `GRAPH.COPY` checks already run. The rest of this row is to build. The image tag is unchanged. |
| schema | Amaan | to build | `sheldon/schema.py`, `queries/create_index_*.cypher` | `tests/schema/test_constraints.py` (Amaan) | smoke-docker | Applying the constraints rejects a duplicate `Claim.id` `CREATE`. The exact-match index exists first. |
| eval-def | Satyansh | to build | `docs/plan/eval-def.md` | `tests/eval/test_eval_def.py` (Satyansh) | none | The file defines a repeated failed step MAST-style (step repetition, FM-1.3, arXiv 2503.13657): the rule, a hand-labelled sample, then what to automate. TIDE's loop ratio (arXiv 2602.02196) may appear as a definition only, never as a memory result. No count is in the file. |
| ingest | Amaan | to build | `sheldon/memory/` | `tests/memory/test_ingest.py` (Amaan) | schema | A git-log fixture writes `Developer-AUTHORED→Commit-MODIFIED→File` and `CO_CHANGED_WITH`. Two concurrent writes do not fork one chain. |
| pr-ingest | Amaan | wired and tested (draft by Akshat, for Amaan to review) | `sheldon/pr/` | `tests/pr/test_ingest.py` (Amaan) | schema | A fixture diff writes `(:PR)-[:CHANGES]->(:File)` for that head sha. |
| seed | Amaan | wired and tested (draft by Akshat, for Amaan to review) | `sheldon/seed/` | `tests/seed/test_snapshot.py` (Amaan) | ingest | The frozen graph contains INC-12 and E-41. `GRAPH.COPY` of it resets a destination graph. |
| s0 | Akshat | keyword half wired; vector half waits on `EMBEDDING_DIM` | `sheldon/retrieval/s0.py` | `tests/retrieval/test_s0.py` (Akshat) | seed | Vector plus keyword, no traversal, run on the demo question. The recorded result is a miss. |
| r1-recall | Akshat | wired on a fixture; seed run to do | `sheldon/retrieval/recall.py` | `tests/retrieval/test_recall.py` (Akshat) | seed, pr-ingest | `recall` returns incident → claim → evidence rows for a `checkout/` file through `GRAPH.RO_QUERY` with a timeout. |
| w1-approve | Hariharan | built | `sheldon/gate/approve.py` | `tests/gate/test_approve.py` (Hariharan) | schema, seed | The call refuses missing, unexecuted, empty, duplicate, and wrong-sha ids. Valid ids create 1 `FOR` and 2 `CITES`. |
| w2-cascade | Hariharan | query ran; wiring to build | `sheldon/belief/` | `tests/belief/test_refute.py` (Hariharan) | schema, seed | One call refutes C-7 and stales A-3 and T-9. A missing evidence id changes nothing. Nothing is deleted. `REFUTE_IS_STUB` is `False`. The refute race file is Amaan's `race-tests` row. |
| w3-done | Hariharan | to build | `sheldon/gate/done.py` | `tests/gate/test_done.py` (Hariharan) | w1-approve, evidence-run | A "done" claim with no passing executed `test_run` on the head sha returns no approval id. |
| evidence-run | Hariharan | producer built | `sheldon/evidence/` | `tests/evidence/test_run.py` (Hariharan) | schema | The producer writes an Evidence node with `executed`, sha, exit code, model, and session. The gate does not accept Evidence minted by the model. |
| claim-lease | Hariharan | built | `sheldon/coordination/board.py`, `queries/claim_task.cypher` | `tests/coordination/test_claim.py` (Hariharan) | schema | Twenty claimers, one winner. A non-owner cannot heartbeat or complete. `CLAIM_IS_STUB` is `False`. The claim race file is Amaan's `race-tests` row. |
| provenance | Hariharan | to build | `sheldon/provenance.py` | `tests/test_provenance.py` (Hariharan) | w1-approve, w2-cascade, evidence-run | A read returns model and session for every Claim, Evidence, Approval, and Action the seed writes. |
| preflight | Satyansh | to build | `sheldon/preflight.py`, `sheldon/mcp/` | `tests/test_preflight.py`, `tests/mcp/test_server.py` (Satyansh) | w2-cascade, seed | Preflight on the INC-12 TTL retry returns block with E-41. |
| capsule | Satyansh | to build | `sheldon/capsule.py` | `tests/test_capsule.py` (Satyansh) | preflight | The returned text includes a do-not from a refuted attempt and the proving command. |
| resume | Satyansh | to build | `sheldon/coordination/resume.py` | `tests/coordination/test_resume.py` (Satyansh) | claim-lease, w2-cascade | The dict has tried, failed, believed, and next, with ids. The refuted claim is still present. |
| compose | Satyansh | to build | `sheldon/answers/` | `tests/answers/test_compose.py` (Satyansh) | r1-recall | The comment text is built from traversal rows. An empty bundle abstains. No id appears that was not in the bundle. |
| check-run | Akshat | decision and webhook wired; not yet run against GitHub | `sheldon/check/` | `tests/check/test_check_run.py` (Akshat) | r1-recall, w1-approve, pr-ingest | On the seed repo a PR gets a red check citing E-52, and approval A-3 is reported stale. A clean PR gets a green check and no comment. |
| eval-count | Satyansh | to build | `sheldon/eval/` | `tests/eval/` (Satyansh) | eval-def, seed, w3-done, preflight | At least 3 runs per arm, each reset with `GRAPH.COPY`. The table has pass rate, total tokens, and the spread. Wording stays "safer at the same quality" unless the margin beats a 1-task gap. |
| race-tests | Amaan | xfail until the write lands | `tests/test_races.py` | `tests/test_races.py` (Amaan) | claim-lease, w2-cascade | The claim race and the missing-evidence refute race pass with the stub flags false. Until those writes land they stay xfail. Do not delete them or mark them passed. |
| ci | Akshat | runs on pull requests | `.github/workflows/ci.yml` | `.github/workflows/ci.yml` (Akshat) | none | A pull request runs `ruff check sheldon tests` and `pytest` against `falkordb/falkordb:v4.22.1`. The image tag is unchanged. |
| check-e2e | Akshat | E-52 half passes on the seed; A-3 stale half waits on W2 | `tests/check/test_check_run.py` | `tests/check/test_check_run.py` (Akshat) | check-run | End to end on the seed repo: a PR gets a red check citing E-52, and approval A-3 is reported stale. A clean PR gets a green check and no comment. |
| gate-tests | Hariharan | to build | `tests/gate/test_approve.py`, `tests/gate/test_done.py`, `tests/belief/test_refute.py` | those files (Hariharan) | w1-approve, w2-cascade, w3-done | W1 refuses missing, unexecuted, empty, duplicate, and wrong-sha ids. Valid ids create 1 `FOR` and 2 `CITES`. W2 refutes C-7 and stales A-3 and T-9, and deletes nothing. W3 returns no approval id when a done claim has no passing executed `test_run` on the head sha. |
| provenance-tests | Hariharan | to build | `tests/test_provenance.py` | `tests/test_provenance.py` (Hariharan) | provenance | A read returns model and session for every Claim, Evidence, Approval, and Action the seed writes. |
| eval-harness | Satyansh | to build | `tests/eval/` | `tests/eval/` (Satyansh) | eval-def, seed, w3-done, preflight | At least 3 runs per arm, each reset with `GRAPH.COPY`. The table has pass rate and total tokens, and the spread. |
| package-name | Amaan (guess) | to build | none in this tree | none in this tree | none | PyPI and npm show `sheldon-ai` owned by the team. This row does not publish code. |
| demo-submit | Akshat (guess) | to build | none in this tree | none in this tree | check-run, eval-count | The video is under about 3 minutes, covers the five demo steps, and the portal shows the submission before 11:00 PM IST. |
| public-repo | Hariharan (guess) | to build | none in this tree | none in this tree | check-run | A fresh public repo, not this history, passes a clean-tree scan and a clone-and-install test. |
