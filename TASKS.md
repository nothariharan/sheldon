# Tasks

Proposed split, Akshat to confirm. One owner per row. One branch per row: `area/short-name`. Edit the files in that row and leave the other rows' files alone.

Scope is the [plan](docs/plan/README.md). Do not add roadmap rows (model allowlist, Stop hooks, hosted MCP, `sameAction` wiring, diff-scope evidence, falkordblite parity).

Status words: **ran** is only W1, W2, and R1, and even those queries are not wired through a working function. **To build** is Sunday's scope. A stub is not a working feature.

## Order and deadlines

Times are IST. Submission closes Sun 18 Oct 2026, 11:59 PM IST.

- Amaan's smoke test, schema, and seed go first. Everyone else builds on them.
- Satyansh writes `eval-def` before any count is quoted.
- Akshat shows the demo question failing on plain memory (S0) before treating R1 as the demo read.
- W1, W2, W3, and preflight are green by Sun 18 Oct 1:00 PM, then the eval runs. Recording is Sun 6–9 PM. The public repo is a fresh repo, Sun evening.

| ID | Owner (proposed) | Status | Files | Depends on | Done when |
|---|---|---|---|---|---|
| smoke-docker | Amaan | to build | `tests/test_smoke.py` | none | On `falkordb/falkordb:v4.22.1` the script checks module `42201`, `GRAPH.COPY`, `timestamp()`, `UNIQUE` on `Claim.id` after an exact-match index, and the W1, W2, and R1 cases in `docs/plan/deep.md`. The image tag is unchanged. |
| schema | Amaan | to build | `sheldon/schema.py`, `queries/create_index_*.cypher` | smoke-docker | Applying the constraints rejects a duplicate `Claim.id` `CREATE`. The exact-match index exists first. |
| eval-def | Satyansh | to build | `docs/plan/eval-def.md` | none | The file defines a repeated failed step MAST-style (step repetition, FM-1.3, arXiv 2503.13657): the rule, a hand-labelled sample, then what to automate. TIDE's loop ratio (arXiv 2602.02196) may appear as a definition only, never as a memory result. No count is in the file. |
| ingest | Amaan | to build | `sheldon/memory/` | schema | A git-log fixture writes `Developer-AUTHORED→Commit-MODIFIED→File` and `CO_CHANGED_WITH`. Two concurrent writes do not fork one chain. |
| pr-ingest | Amaan | to build | `sheldon/pr/` | schema | A fixture diff writes `(:PR)-[:CHANGES]->(:File)` for that head sha. |
| seed | Amaan | to build | `sheldon/seed/` | ingest | The frozen graph contains INC-12 and E-41. `GRAPH.COPY` of it resets a destination graph. |
| s0 | Akshat | to build | `sheldon/retrieval/s0.py` | seed | Vector plus keyword, no traversal, run on the demo question. The recorded result is a miss. |
| r1-recall | Akshat | query ran; wiring to build | `sheldon/retrieval/recall.py` | seed, pr-ingest | `recall` returns incident → claim → evidence rows for a `checkout/` file through `GRAPH.RO_QUERY` with a timeout. |
| w1-approve | Hariharan | query ran; wiring to build | `sheldon/gate/approve.py` | schema, seed | The call refuses missing, unexecuted, empty, duplicate, and wrong-sha ids. Valid ids create 1 `FOR` and 2 `CITES`. |
| w2-cascade | Hariharan | query ran; wiring to build | `sheldon/belief/` | schema, seed | One call refutes C-7 and stales A-3 and T-9. A missing evidence id changes nothing. Nothing is deleted. `REFUTE_IS_STUB` is `False` and the refute race is not xfailed. |
| w3-done | Hariharan | to build | `sheldon/gate/done.py` | w1-approve, evidence-run | A "done" claim with no passing executed `test_run` on the head sha returns no approval id. |
| evidence-run | Hariharan | to build | `sheldon/evidence/` | schema | The producer writes an Evidence node with `executed`, sha, exit code, model, and session. The gate does not accept Evidence minted by the model. |
| claim-lease | Hariharan | to build | `sheldon/coordination/board.py`, `queries/claim_task.cypher` | schema | Twenty claimers, one winner. A non-owner cannot heartbeat or complete. `CLAIM_IS_STUB` is `False` and the claim race is not xfailed. |
| provenance | Hariharan | to build | `sheldon/provenance.py` | w1-approve, w2-cascade, evidence-run | A read returns model and session for every Claim, Evidence, Approval, and Action the seed writes. |
| preflight | Satyansh | to build | `sheldon/preflight.py`, `sheldon/mcp/` | w2-cascade, seed | Preflight on the INC-12 TTL retry returns block with E-41. |
| capsule | Satyansh | to build | `sheldon/capsule.py` | preflight | The returned text includes a do-not from a refuted attempt and the proving command. |
| resume | Satyansh | to build | `sheldon/coordination/resume.py` | claim-lease, w2-cascade | The dict has tried, failed, believed, and next, with ids. The refuted claim is still present. |
| compose | Satyansh | to build | `sheldon/answers/` | r1-recall | The comment text is built from traversal rows. An empty bundle abstains. No id appears that was not in the bundle. |
| check-run | Akshat | to build | `sheldon/check/` | r1-recall, w1-approve, pr-ingest | On the seed repo a PR gets a red check citing E-52, and approval A-3 is reported stale. A clean PR gets a green check and no comment. |
| eval-count | Satyansh | to build | `sheldon/eval/` | eval-def, seed, w3-done, preflight | At least 3 runs per arm, each reset with `GRAPH.COPY`. The table has pass rate, total tokens, and the spread. Wording stays "safer at the same quality" unless the margin beats a 1-task gap. |
| package-name | Amaan (guess) | to build | none in this tree | none | PyPI and npm show `sheldon-ai` owned by the team. This row does not publish code. |
| demo-submit | Akshat (guess) | to build | none in this tree | check-run, eval-count | The video is under about 3 minutes, covers the five demo steps, and the portal shows the submission before 11:00 PM IST. |
| public-repo | Hariharan (guess) | to build | none in this tree | check-run | A fresh public repo, not this history, passes a clean-tree scan and a clone-and-install test. |
