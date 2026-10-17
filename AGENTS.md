# Sheldon

Sheldon blocks coding agents from retrying fixes that already failed, and from calling work done without a real test run, from the first edit to the merge, on one shared FalkorDB graph per repo.

Read [`docs/plan/README.md`](docs/plan/README.md) first. Product scope and wording are that plan. W1 (evidence gate), W2 (refute plus stale cascade), and R1 (PR-time recall) are the only queries that have run. Every other station is **to build** or **roadmap**. A stub that raises `NotImplementedError` is not a working feature.

## Start here

Docker is required. The image pin is `falkordb/falkordb:v4.22.1`. Do not change it.

Linux:

```bash
./scripts/setup.sh
```

Windows (one teammate is on Windows):

```powershell
powershell -File scripts/setup.ps1
```

The Windows interpreter is `.venv\Scripts\python.exe`. Linux uses `.venv/bin/python`. Then follow [`TESTING.md`](TESTING.md): `ruff check sheldon tests`, `pytest`, and the smoke test against the pinned image. Paste that output in the PR. Do not mark a row done without it.

## Locked

- **Scope** is p0–p4, the with/without eval, pr-ingest, the GitHub App check, provenance, and MCP preflight. Roadmap stays unbuilt: model allowlist, Stop hooks, hosted MCP, `sameAction` wiring, diff-scope evidence, falkordblite parity, A\*/CCH, Bolt, replication, `MULTI`/`EXEC`.
- **W1** `approve` is built. **W2** `refute_claim` is built. **W3** `claim_done` is built. Provenance `writes_with_provenance` is built. Claim and lease are built; `handoff_task` is partly built. **R1** query ran; recall wiring is on a fixture.
- **Image:** `falkordb/falkordb:v4.22.1` (module `42201`). Never `latest` or `edge`. 4.x tags start with `v`. 6.x tags do not. Do not switch images in a feature branch.

Claim status in the plan is `open | confirmed | refuted`. `sheldon/schema.py` still has the older set. Confirm it in the schema PR. Do not add another copy of the strings.

## Engine facts

- Constraints can only make a property required or unique. They cannot require an edge or check that a cited id exists. The evidence gate is the write query. Constraints are the backstop.
- UDFs are JavaScript and read-only. They belong on `6.0.2` only. Do not rely on FLEX in v4.22.1 (unchecked). A UDF cannot perform the refute write.
- Personalized PageRank does not exist. `algo.pageRank` is global. A\* and CCH are 4.22-only and out of scope. Do not reach for them.
- `LIMIT` does not restrict eager writes. Do not use an unbounded `*0..`.
- A vector `WHERE` runs after the top-k cut. Empty does not always mean "no match".
- Whole-graph algos (`algo.WCC`, `algo.betweenness`, `algo.labelPropagation`) take no positional args. A wrong call returns `[]` and does not error.
- The image's default query timeout is 1000ms.
- Before guessing that a command exists, read [`docs/engine/features.md`](docs/engine/features.md). Before citing a paper's engine behavior, read [`docs/engine/papers.md`](docs/engine/papers.md). Each paper notes the FalkorDB version it was checked against.

## Never write these

Not in the README, the pitch, or code comments:

- "only possible on FalkorDB"
- "nobody else measures this"
- "no competitor has GRAPH.COPY"
- "reaching the task board is ours"
- "revolutionary"
- any speed number that has not been measured on our harness
- any cost-saving number

Also drop the list in [`docs/facts.md`](docs/facts.md) and [`docs/decisions/REPORT.md`](docs/decisions/REPORT.md) §5. Say "we measured" and "none we found".

## Repo map

| Path | Owner | Contract |
|---|---|---|
| `sheldon/schema.py` | Amaan | Status strings, labels, edge names, image pin. To build |
| `sheldon/memory/`, `sheldon/pr/`, `sheldon/seed/` | Amaan | Ingest, pr-ingest, seed. To build |
| `sheldon/retrieval/`, `sheldon/check/` | Akshat | S0, R1, check run. R1 query ran; wiring is to build |
| `sheldon/gate/`, `sheldon/belief/`, `sheldon/evidence/`, `sheldon/provenance.py`, `sheldon/coordination/board.py` | Hariharan | W1 `approve`, `record_run`, W2 `refute_claim`, W3 `claim_done`, and provenance `writes_with_provenance` are built. Claim and lease are built; `handoff_task` is partly built |
| `sheldon/mcp/`, `sheldon/preflight.py`, `sheldon/capsule.py`, `sheldon/coordination/resume.py`, `sheldon/answers/`, `sheldon/eval/` | Satyansh | Retry block, MCP stdio server, and capsule are built. Resume, comment, eval are to build |
| `queries/` | whoever owns the caller | One Cypher statement per file |
| `docs/plan/` | shared | Product scope. Read before the older design notes |

Each of those folders has its own `AGENTS.md`. Read that one before editing.

## Run

```bash
./scripts/setup.sh          # compose, venv, smoke test
.venv/bin/python -m pytest  # lint is separate
.venv/bin/ruff check sheldon tests
```

On Windows, run `powershell -File scripts/setup.ps1` (the venv interpreter is `.venv\Scripts\python.exe`).

FalkorDB listens on `localhost:6379`. The bundled browser is on `localhost:3000`. `FALKORDB_HOST` and `FALKORDB_PORT` override the client.

Smoke test: module version is `42201`, and `GRAPH.COPY` of a one-node graph round-trips. CI runs lint, the suite, and that smoke test against the same pinned image.

## Branches

`area/short-name`, one branch per row in [`TASKS.md`](TASKS.md). Details in [`CONTRIBUTING.md`](CONTRIBUTING.md). Do not share a branch. Do not commit to `main`.

## Docs

[`docs/plan/`](docs/plan/README.md) wins on product scope and wording. [`docs/facts.md`](docs/facts.md), [`docs/decisions/REPORT.md`](docs/decisions/REPORT.md), and [`docs/engine/papers.md`](docs/engine/papers.md) still override `docs/design/` and `docs/research/` on engine limits. `papers.md` retires the personalized-PageRank design row: that procedure does not exist. Index: [`docs/README.md`](docs/README.md).

The five quotes the plan uses are in [`docs/plan/quotes.md`](docs/plan/quotes.md). Do not add others, and do not paste them into UI text.

No Cursor rules. They would repeat this file.
