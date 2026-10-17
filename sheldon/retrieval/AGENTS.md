# retrieval (p2)

Status: to build, except the R1 query, which ran. `recall` is still to build and is not a working feature. Akshat owns this folder. S0 is `s0.py`. Do not treat `q_star` as the demo read.

Owns anchors, bounded traversal, the evidence bundle, and Q\*.

## Contract

`retrieve` returns evidence the graph selected, not a flat nearest-neighbour list. `q_star` runs `queries/q_star.cypher`. The demo question is in that file. S0 (vector + keyword, no traversal) has to fail it.

Reads should go through `RO_QUERY` with a timeout once you wire a read helper. Don't put that helper in `belief/` or `coordination/`.

## Gotchas

- Upper bound every var-length pattern. `*1..3` is the locked stale depth. Do not use unbounded `*0..`.
- A `WHERE` after `db.idx.vector.queryNodes` filters the top-k only. An empty result can mean "outside the window".
- No personalized PageRank, no A\*, no CCH. `algo.pageRank` is global. Whole-graph algos with positional args return `[]` and do not error.
- `INVESTIGATES` vs `JUSTIFIED_BY` is unconfirmed. Use `schema.TASK_TO_HYPOTHESIS`.
- The default server timeout is 1000ms. A killed query is not an empty answer.
