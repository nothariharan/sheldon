# seed

Amaan. Status: `load_seed` and `copy_graph` are wired and tested in `tests/seed/test_snapshot.py`.

## Contract

`load_seed(graph)` writes `queries/seed_demo.cypher` (one `CREATE`) into an empty graph and returns the key. It refuses a graph that has nodes. `copy_graph(source, dest)` deletes `dest` if it exists, then runs `GRAPH.COPY`.

Seed once, freeze once, then copy from the frozen key for every demo take and every eval run. Never copy from a graph that already ran.

The ids are listed in `docs/plan/demo.md` (Seed ids). The snapshot includes INC-12 and E-41, which the retry block needs.

## Gotchas

- The tests also check that R1, the check run, and the W2 cascade pattern from `docs/plan/deep.md` read the seed the way the demo needs. If you change an id or an edge, run them.
- Every Claim, Evidence, Approval, and Action carries `model` and `session`, for the provenance row.
- `Action.fingerprint` is a placeholder (`edit checkout/cache.py`). The preflight row owns the fingerprint format. Change it here when that lands.
