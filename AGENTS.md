# Sheldon

Multi-agent incident-investigation memory on FalkorDB. Track 02 (Agent Memory and Coordination), Graph Hacks. One graph per investigation, a task board on that same graph, and answers that cite the path.

Scope is frozen. Do not reopen it.

## Locked

- **p0–p4 plus the repeated-failed-steps eval.** Cut: label vector filters, the MCP server, BeliefMem's multi-candidate machinery, ablations, playbooks, `GRAPH.COPY` branch-and-merge, A\*/CCH, Bolt, replication, GraphRAG-SDK, `MULTI`/`EXEC`.
- **(a)** A refute lands only through one atomic conditional Cypher write that `MATCH`es every cited evidence id. No LLM in the decision. A missing id returns 0 rows and changes nothing.
- **(b)** That same write marks dependent open tasks stale, bounded `*1..3`, and sets confidence. Refuted hypotheses are never deleted.
- **(c)** Repeated failed steps, Sheldon vs plain memory, raw counts, at least 3 runs. Every run resets from one frozen `GRAPH.COPY`.
- **Image:** `falkordb/falkordb:v4.22.1` (module `42201`). Never `latest` or `edge`. 4.x tags start with `v`. 6.x tags do not. To switch for a JS UDF, set the tag to `falkordb/falkordb:6.0.2` in `sheldon/schema.py`, `docker-compose.yml`, and `.github/workflows/ci.yml`, re-run `spikes/`, and put the new `MODULE LIST` version in `FALKORDB_MODULE_VERSION`.

Hypothesis status words are **not** locked. The working set is `open | supported | refuted` in `sheldon/schema.py`. Confirm it. Do not add another copy of the strings.

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
- any speed number that has not been measured on our harness

Also drop the list in [`docs/decisions/REPORT.md`](docs/decisions/REPORT.md) §5. Say "we measured" and "none we found".

## Repo map

| Path | Owner | Contract |
|---|---|---|
| `sheldon/schema.py` | shared | The only status strings, labels, edge names, image pin |
| `sheldon/memory/` | p1 | Append-only events. Prev derived inside the query |
| `sheldon/retrieval/` | p2 | Bounded traversal and Q\* |
| `sheldon/answers/` | p3 | Citations and abstention. Does not decide refutes |
| `sheldon/coordination/` | p4 | Claim, lease, handoff, resume |
| `sheldon/belief/` | lead (a)(b) | The refute write |
| `sheldon/eval/` | eval | `GRAPH.COPY` reset and the repeated-step count |
| `queries/` | whoever owns the caller | One Cypher statement per file |
| `spikes/` | whoever changes the image | P0 scripts. Not the test suite |
| `docs/decisions/` | rarely | `REPORT.md` and `check.md` win |

Each of those folders has its own `AGENTS.md`. Read that one before editing.

## Run

```bash
./scripts/setup.sh          # compose, venv, smoke test
.venv/bin/python -m pytest  # lint is separate
.venv/bin/ruff check sheldon tests
```

FalkorDB listens on `localhost:6379`. The bundled browser is on `localhost:3000`. `FALKORDB_HOST` and `FALKORDB_PORT` override the client.

Smoke test: module version is `42201`, and `GRAPH.COPY` of a one-node graph round-trips. CI runs lint, the suite, and that smoke test against the same pinned image.

## Branches

`area/short-name`, one branch per row in [`TASKS.md`](TASKS.md). Details in [`CONTRIBUTING.md`](CONTRIBUTING.md). Do not share a branch. Do not commit to `main`.

## Docs

[`docs/decisions/REPORT.md`](docs/decisions/REPORT.md) and [`docs/decisions/check.md`](docs/decisions/check.md) override `docs/design/` and `docs/research/`. Index: [`docs/README.md`](docs/README.md).

No Cursor rules. They would repeat this file.
