# retrieval (p2)

Status: `recall` (R1) and the keyword half of `s0` are wired and tested on a fixture in `tests/test_retrieval.py`. Neither has run on the seed yet, because pr-ingest and the seed are to build. `retrieve` and `q_star` are older stubs. Akshat owns this folder. Do not treat `q_star` as the demo read.

Reads go through `sheldon.db.read`: `GRAPH.RO_QUERY`, a 1000ms timeout, rows keyed by column. The server refuses a write sent that way.

Owns anchors, bounded traversal, the evidence bundle, and Q\*.

## Contract

`retrieve` returns evidence the graph selected, not a flat nearest-neighbour list. `q_star` runs `queries/q_star.cypher`. The demo question is in that file. S0 (vector + keyword, no traversal) has to fail it.

`recall` returns rows from `queries/recall_pr.cypher`: the changed file, the file the incident touched (`via`, the file itself or a 1-hop `CO_CHANGED_WITH` neighbour), incident, claim, and the supporting or refuting evidence. `s0` is keyword-only over Incident titles and Claim text, with no traversal. On the demo question it finds the incident and claim text but no evidence id, and that miss is what the demo shows.

## Gotchas

- `db.idx.fulltext.queryNodes` on a label with no full-text index returns no rows and does not error. Call `create_s0_indexes` first.
- A raw question sent to full-text returns nothing: terms are ANDed and punctuation breaks the parser. `keyword_terms` ORs the words.
- R1 as it ran used `CO_CHANGED_WITH*0..1`. `test_contracts` bans that substring, so the query adds the file to its own neighbour list instead.

- Upper bound every var-length pattern. `*1..3` is the locked stale depth. Do not use unbounded `*0..`.
- A `WHERE` after `db.idx.vector.queryNodes` filters the top-k only. An empty result can mean "outside the window".
- No personalized PageRank, no A\*, no CCH. `algo.pageRank` is global. Whole-graph algos with positional args return `[]` and do not error.
- `INVESTIGATES` vs `JUSTIFIED_BY` is unconfirmed. Use `schema.TASK_TO_HYPOTHESIS`.
- The default server timeout is 1000ms. A killed query is not an empty answer.
