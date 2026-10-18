# Trap suite

Deterministic checks on seeded graph states. No LLM is in the loop.

`python -m eval.traps` prints a markdown table and writes `results.md` (date, main sha, image tag, and that command). Each scenario resets from one frozen `GRAPH.COPY` before the check. The median is the check, not the copy.

## Check interface

An arm is one class with:

- `name: str` — the label in the table
- `blocks(self, graph: str, scenario: dict) -> bool` — `True` when the arm refuses the action

`graph` is a fresh copy of the frozen seed for that scenario. The arm may read or write it. `scenario` is one object from `scenarios.json` or `heldout/scenarios.json`. Both files use the same shape. `blocks` is the whole interface: do not add a required argument. A `trace` string set inside `blocks` is optional and is not part of the interface.

- `id`, `family`, `expected` (`block` or `allow`), `text`, `action`
- `action.type` is `preflight`, `done`, or `approve`
- `expected` is the ground-truth verdict, written in the file before a run

`eval.traps.arms.Arm` is that interface. Add an arm by implementing it and appending an instance to `ARMS` in `runner.py`. The runner uses the same scenarios, the same FalkorDB, and the same three metrics: bad actions blocked / total bad, good actions wrongly blocked / total good, median milliseconds per check. Do not edit the scenarios or an existing arm's rule to change a score.

## Arms

1. `no-memory` — `blocks` returns false.
2. `search-only baseline` — S0 keyword search (`queries/s0_keyword.cypher`) on `text` only. Block when a hit is a refuted claim, or an incident whose `HAS_CAUSE` claim is refuted. An open claim does not block. This is a stand-in for recall-style memory, not a named product.
3. `sheldon` — preflight R2, W3 `claim_done`, and W1 `approve`. Preflight blocks only on decision `block` (`warn` and `ok` count as allow). The exact fingerprint is checked first. When it misses, and the scenario has text, a full-text query (`db.idx.fulltext.queryNodes` in `queries/preflight_attempt_search.cypher`) runs over failed attempts. A hit counts only when the attempt touched the same file, or the hit is the same refuted claim. Path tokens are left out of the query. They are the file scope. `claim_done` blocks when it returns no approval id. The same write refuses when that claim is refuted or reaches a refuted claim in 1..3 `RELIES_ON` or `DEPENDS_ON` hops. `approve` blocks when it returns no approval id. It checks that the cited evidence executed on the PR head sha. If the action has `cites_claim`, that id is `relies_on`: the write is refused on the same hop check. The refusal reason is the path (claim ids, edge types, and the refuting evidence id).

## Scenarios

`scenarios.json` is the dev set: 4 exact retries of the recorded refuted fix, 4 reworded retries on the same file, 3 done claims with no executed passing run on the head sha, 3 approvals that cite a claim 1, 2, and 3 `RELIES_ON` hops from a refuted claim, and at least 6 actions that should be allowed.

`heldout/scenarios.json` is a second set, scored separately. `FROZEN` is the sha256 of both files. A test fails if either file changes. Do not edit an expected verdict after a run.
