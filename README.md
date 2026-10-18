# Sheldon

Sheldon blocks an exact repeat of a refuted fix, and blocks calling work done without a real test run, on one shared FalkorDB graph per repo. A reworded retry of that fix is allowed: the dev table blocks 0 of 4.

Built and tested on main: W1, W2, W3, R1, R2 preflight, claim and lease (handoff is built), provenance, the capsule text, the session-start hook, resume, compose, the check on the seed path, the demo seed, `sheldon run`, and fail-closed for commit, push, and done. Cut or not built: ingest, the S0 vector half, and paired eval runs.

A claim or approval only lands if every evidence id it cites is a real executed run. Refuting evidence marks the claim refuted, and every approval and task that relied on it goes stale, in one atomic write. Nothing marks a claim stale. None we found blocks a coding agent from retrying a code fix refuted in the shared graph.

Graph Hacks (WeMakeDevs × FalkorDB), Track 02 — Agent Memory and Coordination. Team SheldonAI.

> A stale graph is worse than no graph, it lies with confidence.

@falkordb on X, Aug 25 2026.

## Start here

Docker is required. The image is `falkordb/falkordb:v4.22.1` (module `42201`).

Linux:

```bash
./scripts/setup.sh
```

Windows:

```powershell
powershell -File scripts/setup.ps1
```

On Windows the venv interpreter is `.venv\Scripts\python.exe`. On Linux it is `.venv/bin/python`.

That is the one command for a clean clone. It starts FalkorDB, creates `.venv`, installs from `requirements-dev.txt`, and runs the smoke test. The smoke test checks the engine module version and a `GRAPH.COPY` round trip. It does not yet run W1, W2, or R1. That wider smoke test is to build.

`pyproject.toml` states minimums (`falkordb>=1.7`, `pytest>=8`, `ruff>=0.6`). It does not pin them. `requirements.txt` pins the FalkorDB client. `requirements-dev.txt` pins pytest and ruff and installs this package.

```bash
source .venv/bin/activate
pytest
ruff check sheldon tests
```

Windows, after setup:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check sheldon tests
```

The database is on port 6379. FalkorDB Browser is on port 3000.

## MCP client

`python -m sheldon.mcp.server` speaks MCP JSON-RPC on stdin and stdout. Point the client at that command. `sheldon_run` is `sheldon run -- <cmd>`: it runs the command and records one executed Evidence node. `claim_done` writes an Approval when that run passed on the same sha. `tests/mcp/test_e2e_session.py` drives one session on the seed graph: preflight, then the run, then the done claim.

## Session start

Claude Code can print the capsule when a session starts. Set `SHELDON_GRAPH` and `SHELDON_TASK`, then merge [`hooks/claude-session-start.json`](hooks/claude-session-start.json) into `.claude/settings.json`. The command is `python -m sheldon.hooks.session_start`. It writes the capsule to stdout. A missing task exits 1 and names the task.

```bash
export SHELDON_GRAPH=sheldon:demo
export SHELDON_TASK=T-9
python -m sheldon.hooks.session_start
```

## Where to read

People and coding agents start at [`docs/plan/README.md`](docs/plan/README.md). Work items are in [`TASKS.md`](TASKS.md). How to test is in [`TESTING.md`](TESTING.md). How to branch is in [`CONTRIBUTING.md`](CONTRIBUTING.md). Engine limits are in [`docs/facts.md`](docs/facts.md) and [`docs/engine/papers.md`](docs/engine/papers.md).

## What is in scope

The evidence gate, the one-write refute plus stale cascade, and the retry block, plus a with/without count that has not been run. Each eval run will reset from one frozen `GRAPH.COPY`. Paper numbers are not Sheldon results. Cost is to measure. The default quality phrase is "safer at the same quality".

## Benchmark

On 21 synthetic scenarios we wrote, three arms check one proposed action each against the same FalkorDB graph (`falkordb/falkordb:v4.22.1`). Ten more scenarios are held out and scored separately. This is a narrow test of one job, not a general memory benchmark. No benchmark for this exact job that we found. The scenarios are synthetic and deterministic, and no LLM is in the loop. The search-only baseline is a stand-in for a recall-style memory. It is not a named product.

Dev N = 21 (14 actions that should be blocked, 7 that should be allowed). Held-out N = 10 (7 that should be blocked, 3 that should be allowed). Each check resets from a frozen `GRAPH.COPY`. The median is the check, not the copy. Command: `python -m eval.traps`. `eval/traps/FROZEN` is the sha256 of both scenario files. The per-scenario verdicts and the gate return on every miss are in `eval/traps/results.md`.

- **no-memory** always allows.
- **search-only baseline** runs the S0 keyword path (`queries/s0_keyword.cypher`) on the action text and blocks when a hit is a refuted claim, or an incident whose cause claim is refuted.
- **sheldon** runs preflight R2, W3 `claim_done`, and W1 `approve`. Preflight counts as a block only when the decision is `block`. `warn` counts as allow. `approve` checks cited evidence. When the action names a claim, the same write refuses if that claim is refuted or reaches a refuted claim in 1..3 `RELIES_ON` or `DEPENDS_ON` hops, the window W2 uses. The refusal reason is that path: the claim ids, the edge type on each hop, and the refuting evidence id. `python -m sheldon.gate.approve` prints it, and `--json` includes it. `claim_done` uses the same hop check on the done claim.

### Dev

| Arm | Bad blocked | Good wrongly blocked | Median ms |
| --- | --- | --- | --- |
| no-memory | 0/14 | 0/7 | 0.00 |
| search-only baseline | 8/14 | 1/7 | 5.68 |
| sheldon | 10/14 | 0/7 | 4.76 |

Sheldon wrongly blocked good actions: none.

### Held-out

| Arm | Bad blocked | Good wrongly blocked | Median ms |
| --- | --- | --- | --- |
| no-memory | 0/7 | 0/3 | 0.00 |
| search-only baseline | 2/7 | 0/3 | 4.38 |
| sheldon | 5/7 | 0/3 | 5.06 |

Sheldon wrongly blocked good actions: none.

Sheldon still misses four bad actions on the dev set, all reworded retries of the refuted fix (`b1`–`b4`). The command is not the recorded fingerprint `edit checkout/cache.py`, so `queries/preflight_r2.cypher` returns no block and preflight returns decision `warn` (`Files touched in prior incident(s) INC-12; alternative fix attempt allowed`). That is a limit of exact-fingerprint preflight. A different command on that same file is a warn in `tests/test_preflight.py` (`refactor checkout/cache.py`), so this gate does not block every edit of the file.

On the dev set, search-only blocked three bad actions sheldon allowed: `b1`, `b2`, and `b3`. Search-only wrongly blocked one good action, `e7` (the S0 hit was refuted claim C-5). Sheldon wrongly blocked good actions: none.

How another arm is added is in [`eval/traps/README.md`](eval/traps/README.md). The check interface is `name` and `blocks(graph, scenario) -> bool`.

## Graph data model

Labels, relationships, and properties below are the names in `sheldon/schema.py` and the statements in `queries/`.

### Status words

`sheldon/schema.py` defines these enums:

- Hypothesis status: `open`, `supported`, `refuted`.
- Task status: `open`, `claimed`, `done`, `blocked`. `stale` is a boolean on the task.
- Approval status: `active`, `stale`.
- Event type: `observation`, `action`, `result`, `decision`, `note`.

`schema.py` also lists mandatory and unique constraints on `Hypothesis.status`, `Event.id`, `Hypothesis.id`, `Task.id`, and on `REFUTED_BY` `agent` and `at`. The file says to confirm the command on the pinned image before applying them.

### Labels

| Label | Where it is named | Key properties the queries use |
|---|---|---|
| `Investigation` | `schema.py`; `queries/record_event.cypher` | `id` |
| `Event` | `schema.py`; `queries/record_event.cypher` | `id`, `type`, `text`, `ts`, `agent_id`, `session_id`, `source`, `ingest_seq` |
| `Hypothesis` | `schema.py`; `queries/refute_hypothesis.cypher`, `queries/hypothesis_confidence.cypher` | `id`, `status`, `confidence` |
| `Task` | `schema.py`; claim, lease, and cascade queries | `id`, `status`, `owner`, `lease_expires`, `stale`, `stale_because`, `title`, `version` |
| `Claim` | seed, refute, resume, and gate queries | `id`, `kind`, `status`, `confidence`, `text`, `model`, `session`, `refuted_at` |
| `Evidence` | `queries/record_run.cypher` and the seed | `id`, `kind`, `command`, `sha`, `executed`, `exit_code`, `model`, `session` |
| `Approval` | `queries/approve_pr.cypher`, `queries/claim_done.cypher`, seed | `id`, `by`, `actor_kind`, `sha`, `status`, `at`, `model`, `session` |
| `Action` | seed, `queries/record_eval_action.cypher` | `id`, `cmd`, `files`, `fingerprint`, `model`, `session` |
| `PR` | `queries/approve_pr.cypher`, `queries/ingest_pull_request.cypher`, seed | `number`, `head_sha`, `status` |
| `File` | seed, `queries/ingest_pull_request.cypher`, `queries/recall_pr.cypher` | `path`, `extension`, `language` |
| `Incident` | seed, preflight, recall | `id`, `title`, `severity`, `at` |
| `Developer` | seed | `name` |
| `Commit` | seed | `hash`, `message`, `timestamp` |
| `Repository` | seed | `name` |

`schema.py` also names `Session`, `Agent`, and `Entity`. No file under `queries/` creates those labels.

### Relationships

Named in `schema.py` and written or walked by a query:

- `(Event)-[:NEXT {gap_ms}]->(Event)` and `(Event)-[:IN_INVESTIGATION]->(Investigation)` in `queries/record_event.cypher`.
- `(Claim)-[:SUPPORTED_BY]->(Evidence)` in the seed. `(Hypothesis)-[:SUPPORTED_BY]->(Event)` in `queries/q_star.cypher`.
- `(Claim)-[:REFUTED_BY {agent, at, model, session}]->(Evidence)` in the seed and `queries/refute_claim.cypher`. `(Hypothesis)-[:REFUTED_BY]->(Event)` in `queries/refute_hypothesis.cypher`.
- `(Task)-[:DEPENDS_ON]->(Task)` in `queries/claim_task.cypher`. `(Task)-[:DEPENDS_ON]->(Claim)` in the seed.
- `(Event)-[:RESULTED_IN|CAUSED_BY]->(Event)` is the walk in `queries/q_star.cypher`.
- `(Task)-[:INVESTIGATES]->(Hypothesis)`. `INVESTIGATES` is `TASK_TO_HYPOTHESIS` in `schema.py`.

`schema.py` also names `IN_SESSION`, `INVOLVES`, `RELATED_TO`, and `PRODUCED`. No file under `queries/` writes them.

Written by the query files, not declared as constants in `schema.py`:

- `(Approval)-[:FOR]->(PR)` in `queries/approve_pr.cypher`. `(Approval)-[:FOR]->(Claim)` in `queries/claim_done.cypher`.
- `(Approval)-[:CITES]->(Evidence)`.
- `(Approval)-[:RELIES_ON]->(Claim)` in the seed. `queries/refute_claim.cypher` walks `RELIES_ON` and `DEPENDS_ON` up to 3 hops.
- `(PR)-[:CHANGES {sha}]->(File)`.
- `(File)-[:CO_CHANGED_WITH {frequency}]->(File)`.
- `(Incident)-[:HAS_CAUSE]->(Claim)` and `(Incident)-[:TOUCHED]->(File)`.
- `(Action)-[:ATTEMPTED_FIX_FOR]->(Claim)`.
- `(Developer)-[:AUTHORED]->(Commit)-[:MODIFIED {additions, deletions}]->(File)-[:BELONGS_TO]->(Repository)` in the seed.

## Cypher files

Each file under `queries/` is one statement, except `queries/AGENTS.md`, which is the folder rule, and `queries/create_vector_index_event.cypher`, which is comments until `EMBEDDING_DIM` is set.

- `queries/AGENTS.md` — folder rule: one statement per file, parameters, no second query.
- `queries/approve_pr.cypher` — W1 write. An approval lands when every cited Evidence id executed on that sha. If it names a claim, that claim must not be refuted or within 1..3 hops of a refuted claim. Zero rows means refused.
- `queries/audit_refuted_without_evidence.cypher` — demo audit of refuted hypotheses with no `REFUTED_BY` edge to an Event.
- `queries/capsule_task.cypher` — read a task and the refuted attempts that touch it, with evidence ids.
- `queries/check_approvals.cypher` — read approvals `FOR` a PR and cited evidence that is not an executed run on the head sha.
- `queries/check_cited_evidence.cypher` — look up each cited evidence id. A missing id still returns a row, with `found` false.
- `queries/claim_done.cypher` — W3 write. A done claim needs an executed `test_run` that exited 0 on this sha. `MERGE` on the approval id.
- `queries/claim_task.cypher` — one conditional write so concurrent callers produce one winner.
- `queries/complete_task.cypher` — set a claimed task to done for the agent that holds it.
- `queries/count_nodes.cypher` — count the nodes in the graph.
- `queries/create_fulltext_claim_text.cypher` — full-text index on `Claim.text`.
- `queries/create_fulltext_event_text.cypher` — full-text index on `Event.text`.
- `queries/create_fulltext_incident_title.cypher` — full-text index on `Incident.title`.
- `queries/create_index_event_id.cypher` — index on `Event.id`.
- `queries/create_index_event_ts.cypher` — index on `Event.ts`.
- `queries/create_index_hypothesis_id.cypher` — index on `Hypothesis.id`.
- `queries/create_index_task_id.cypher` — index on `Task.id`.
- `queries/create_vector_index_event.cypher` — commented sketch of a vector index on `Event.embedding`. Not runnable until `EMBEDDING_DIM` is set.
- `queries/handoff_task.cypher` — release a claimed lease: status back to open, `owner` and `lease_expires` cleared.
- `queries/heartbeat.cypher` — extend the lease when this agent still holds the task.
- `queries/hypothesis_confidence.cypher` — read `Hypothesis.confidence` so the locked refute sketch can write that value back.
- `queries/ingest_pull_request.cypher` — one statement for the files a PR changes at one head sha. A new push replaces the `CHANGES` set.
- `queries/preflight_r2.cypher` — retry check sent as a read, for an exact action fingerprint and file incident warnings.
- `queries/q_star.cypher` — read open tasks still tied to a hypothesis whose support traces back to an action that was later refuted.
- `queries/recall_pr.cypher` — R1 read. For each file a PR changes, incidents, claims, and the evidence that supports or refutes them, bounded at one co-change hop.
- `queries/record_eval_action.cypher` — write an `Action` during an evaluation run.
- `queries/record_event.cypher` — append one `Event` to an investigation and link `NEXT` from the previous event.
- `queries/record_run.cypher` — write one `Evidence` node. `executed: true` is a literal, so a caller cannot pass it in.
- `queries/refute_claim.cypher` — W2 write. Refute a claim and stale dependents at up to 3 hops. A task keeps its status and gets boolean `stale`.
- `queries/refute_hypothesis.cypher` — older sketch: one write on a `Hypothesis` and cited `Event` ids. A contract test locks this file.
- `queries/repeated_failed_steps.cypher` — count actions that match a prior attempt on a refuted claim backed by executed non-zero evidence.
- `queries/resume_state.cypher` — read tried, failed, believed, and next, each citing ids.
- `queries/s0_keyword.cypher` — keyword hits over stored text, with no traversal. The vector half waits on `EMBEDDING_DIM`.
- `queries/seed_demo.cypher` — demo seed in one `CREATE`. The ids are seed data, not a result.
- `queries/trap_hit_status.cypher` — read claim status, or the cause-claim status of an incident, for S0 hit ids. Used by the trap suite.
- `queries/trap_overlay.cypher` — one `CREATE` of the trap-suite hop chain and the wrong-sha test run, applied after the demo seed.
- `queries/writes_with_provenance.cypher` — read `id`, label, `model`, and `session` for `Claim`, `Evidence`, `Approval`, and `Action`.

## AI disclosure

The team designed the system and wrote and reviewed the code with AI coding assistants (Cursor agents). Every PR went through tests and human or bot review.

## Credits

Repo mapping builds on two MIT projects. Section 2.1 of [`docs/plan/deep.md`](docs/plan/deep.md) names what Sheldon reuses.

- [FalkorDB code-graph](https://github.com/FalkorDB/code-graph) (MIT). Structural calls and imports from that project are roadmap.
- [FalkorDB RepoGraph](https://github.com/FalkorDB/RepoGraph) (MIT). The borrowed vocabulary is `Developer-AUTHORED→Commit-MODIFIED→File`, `File-CO_CHANGED_WITH→File`, `File-PART_OF→Module`, and `File-BELONGS_TO→Repository`. The seed writes `Developer`, `Commit`, `File`, `Repository`, `AUTHORED`, `MODIFIED`, `CO_CHANGED_WITH`, and `BELONGS_TO`.
