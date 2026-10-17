# coordination (p4)

Owns the task board. The refute gate is not in this folder.

## Contract

`claim_task` is one conditional write (`queries/claim_task.cypher`). Many callers, exactly one `True`. `heartbeat`, `complete_task`, and `handoff_task` are each one statement and only affect a task this agent holds. `resume` is a read: tried, failed, believed, next, with event ids. Refuted hypotheses stay in that result.

`$now` is the service clock, passed in as `now_ms`.

When `claim_task` is real, set `CLAIM_IS_STUB = False` and delete the `NotImplementedError`. `tests/test_races.py` then requires exactly one winner.

## Gotchas

- Do not use `MULTI`/`EXEC`. It serializes work across every graph.
- Alias `DEPENDS_ON` if you count it (`ID(dep) >= 0` in the claim query). An unaliased relationship under-counts, and the count is not safe to display.
- `<>` is not index-backed. Fine at demo scale.
- Task status values live in `schema.TaskStatus`. `stale` is a boolean, not a status. Belief's write is what sets it.
- Do not delete a task to "unblock" a claim.
