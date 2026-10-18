# Trap suite

Deterministic checks on seeded graph states. No LLM is in the loop.

`python -m eval.traps` prints a markdown table and writes `results.md` (date, main sha, image tag, and that command). Each scenario resets from one frozen `GRAPH.COPY` before the check. The median is the check, not the copy.

## Check interface

An arm is one class with:

- `name: str` — the label in the table
- `blocks(self, graph: str, scenario: dict) -> bool` — `True` when the arm refuses the action

`graph` is a fresh copy of the frozen seed for that scenario. The arm may read or write it. `scenario` is one object from `scenarios.json`:

- `id`, `family`, `expected` (`block` or `allow`), `text`, `action`
- `action.type` is `preflight`, `done`, or `approve`
- `expected` is the ground-truth verdict, written in the file before a run

`eval.traps.arms.Arm` is that interface. Add an arm by implementing it and appending an instance to `ARMS` in `runner.py`. The runner uses the same scenarios, the same FalkorDB, and the same three metrics: bad actions blocked / total bad, good actions wrongly blocked / total good, median milliseconds per check. Do not edit the scenarios or an existing arm's rule to change a score.

## Arms

1. `no-memory` — `blocks` returns false.
2. `search-only baseline` — S0 keyword search (`queries/s0_keyword.cypher`) on `text` only. Block when a hit is a refuted claim, or an incident whose `HAS_CAUSE` claim is refuted. An open claim does not block. This is a stand-in for recall-style memory, not a named product.
3. `sheldon` — preflight R2, W3 `claim_done`, and W1 `approve` as they exist on main. Preflight blocks only on decision `block` (`warn` and `ok` count as allow). `claim_done` blocks when it returns no approval id. `approve` blocks when it returns no approval id. `approve` checks that the cited evidence executed on the PR head sha. It does not walk `RELIES_ON` or `DEPENDS_ON`. W2 is the refute write that stales dependents; the hop scenarios are already in that post-refute state. This arm does not add a hop walk.

## Scenarios

`scenarios.json` holds the cases: 4 exact retries of the recorded refuted fix, 4 reworded retries on the same file, 3 done claims with no executed passing run on the head sha, 3 approvals that cite a claim 1, 2, and 3 `RELIES_ON` hops from a refuted claim, and at least 6 actions that should be allowed.
