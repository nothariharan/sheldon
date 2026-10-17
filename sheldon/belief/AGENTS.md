# belief (W2)

Status: built. `tests/belief/test_refute.py` shows one call refuting C-7 and staling A-3 and T-9. Hariharan owns this folder. `queries/refute_claim.cypher` is the statement that ran. `queries/refute_hypothesis.cypher` stays the older sketch because the contract test locks its text. `refute_hypothesis` runs that sketch. The race test rejects a missing id.

Owns the refute. One file, one query.

## Contract

`refute_hypothesis` loads `queries/refute_hypothesis.cypher` and returns `True` only when every cited evidence id matched. A missing id returns `False` and writes nothing. There is no LLM call on this path.

The same write sets `status` and `confidence` and marks dependent open tasks `stale` along `INVESTIGATES`, depth `*1..3`. The hypothesis node stays.

Dedupe evidence ids before the call. When this is real, set `REFUTE_IS_STUB = False` and delete the `NotImplementedError`. The race test then sends 20 refutes that cite a missing id and expects every one to be rejected.

## Gotchas

- Constraints cannot see whether the cited id exists. Don't move the gate into `GRAPH.CONSTRAINT`.
- A bare `MATCH` of dependent tasks makes "no open tasks" look like a rejection, because the query returns 0 rows. Keep the `OPTIONAL MATCH` plus `FOREACH` shape, and spike the empty-task path on v4.22.1. `collect` must not invent a task from a null.
- Never `DELETE` the hypothesis. Never open the walk to unbounded `*0..`.
- Confidence rule is unset (`CONFIDENCE_ON_REFUTE`). Don't bake in Hindsight's −2α unless the team confirms it.
- The hop check (n ≤ 2) stays off (`PATH_CHECK_MAX_HOPS`).
