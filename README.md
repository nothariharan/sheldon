# Sheldon

Multi-agent incident-investigation memory on FalkorDB. An investigation is one graph: an append-only event chain, hypotheses that can be refuted only with cited evidence, and a task board on that same graph.

Graph Hacks (WeMakeDevs × FalkorDB), Track 02 — Agent Memory and Coordination. Team SheldonAI.

## Setup

Docker is required.

```bash
./scripts/setup.sh
```

That starts FalkorDB `v4.22.1`, installs the package into `.venv`, and runs the smoke test. The smoke test checks the engine module version (`42201`) and a `GRAPH.COPY` round trip.

```bash
source .venv/bin/activate
pytest
ruff check sheldon tests
```

The database is on port 6379. FalkorDB Browser is on port 3000.

## Where to read

Agents and people start at [`AGENTS.md`](AGENTS.md). Product scope is [`docs/decisions/REPORT.md`](docs/decisions/REPORT.md). Engine limits and the claims drop list are [`docs/facts.md`](docs/facts.md). Paper corrections, including the personalized-PageRank row that cannot be built, are [`docs/engine/papers.md`](docs/engine/papers.md). Those three override the older design notes. Work items are in [`TASKS.md`](TASKS.md). Branch rules are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## What is in scope

p0 through p4, plus a repeated-failed-steps count against plain memory. Each eval run resets from one frozen `GRAPH.COPY`. A refute is one conditional Cypher write. Refuted hypotheses stay in the graph.

This tree is the skeleton. The modules raise `NotImplementedError` until a task branch lands them.
