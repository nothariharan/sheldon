# Sheldon

Sheldon blocks coding agents from retrying fixes that already failed, and from calling work done without a real test run, from the first edit to the merge, on one shared FalkorDB graph per repo.

W1, W2, and R1 queries have run. Every other station in this tree is to build or roadmap. Stubs raise `NotImplementedError`. They are not working features.

A claim or approval only lands if every evidence id it cites is a real executed run. Refuting evidence marks the claim refuted, and every approval and task that relied on it goes stale, in one atomic write. Nothing marks a claim stale. None we found blocks a coding agent from retrying a code fix refuted in the shared graph.

Graph Hacks (WeMakeDevs × FalkorDB), Track 02 — Agent Memory and Coordination. Team SheldonAI.

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

That starts FalkorDB, installs the package into `.venv`, and runs the smoke test. The smoke test checks the engine module version and a `GRAPH.COPY` round trip. It does not yet run W1, W2, or R1. That wider smoke test is to build.

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

## Where to read

People and coding agents start at [`docs/plan/README.md`](docs/plan/README.md). Work items are in [`TASKS.md`](TASKS.md). How to test is in [`TESTING.md`](TESTING.md). How to branch is in [`CONTRIBUTING.md`](CONTRIBUTING.md). Engine limits are in [`docs/facts.md`](docs/facts.md) and [`docs/engine/papers.md`](docs/engine/papers.md).

## What is in scope

The evidence gate, the one-write refute plus stale cascade, and the retry block, plus a with/without count that has not been run. Each eval run will reset from one frozen `GRAPH.COPY`. Paper numbers are not Sheldon results. Cost is to measure. The default quality phrase is "safer at the same quality".
