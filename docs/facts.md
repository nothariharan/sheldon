# Facts that override the older research

[`docs/facts.md`](facts.md), [`docs/decisions/REPORT.md`](decisions/REPORT.md), and [`docs/engine/papers.md`](engine/papers.md) override `docs/design/` and `docs/research/`. When an older file disagrees, follow these three. `papers.md` is the one that retires the personalized-PageRank design row: that procedure cannot be built.

## Pin

- Image: `falkordb/falkordb:v4.22.1` (module 42201). 4.x tags start with `v`. 6.x tags do not (`falkordb/falkordb:6.0.2`).
- Never `latest` or `edge`.
- 4.22.1 is the C engine. 6.x is the Rust engine. Move to 6.0.2 only if a JS UDF ships.

## What the engine cannot do

- Constraints are `MANDATORY` or `UNIQUE` on properties. They cannot require an edge, and they cannot check that a cited id exists.
- UDFs are JavaScript and read-only. They cannot write. The UDF fixes we would want are on 6.0.2. Do not assume FLEX is loaded on v4.22.1.
- There is no personalized PageRank. `algo.pageRank` is global.
- A\* and CCH exist on the 4.22 line only. They are geographic, and they are cut. They are not in 6.0.

## Research corrections

- MIRIX is arXiv `2507.07957`, not `2501.02388`.
- HippoRAG's figure is +38.6 points AR@5 on 2Wiki (37.1 → 75.7), not "+38.6%".
- A vector `WHERE` after `YIELD` does run. It runs on the top-k only, so recall drops outside that window. Per-investigation graphs are a choice, not a requirement.
- The 8.7% → 68.0% staleness figure is a published result from the cited paper, not Sheldon's own number. Always caption it that way.

## Claims never to write

- "only possible on FalkorDB", and any speed number we have not measured
- "no competitor has GRAPH.COPY" / "no other graph DB has an equivalent"
- "vector queries can't be combined with filters, so per-investigation graphs are forced"
- "coordination and memory on one graph is our gap"
- "we track hypotheses" as a differentiator
- "refutations propagate downstream" as novel, on its own
- "reaching the task board is ours"
- "nobody else measures repeated steps"
- personalized PageRank, or `algo.pageRank` described as personalized
- TIDE's 15.8% → 1.0% loop-ratio drop as a memory effect (that drop is model scaling)
- "IRCoT 4–6 round trips" — that figure isn't in the paper
- the product name SynapseOS
