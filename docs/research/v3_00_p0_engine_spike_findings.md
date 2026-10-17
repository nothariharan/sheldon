> **Spike record, 15 Oct 2026**, against `falkordb/falkordb:latest`. The engine reported module **42201**, which is 4.22.1. The pin is now `falkordb/falkordb:v4.22.1`. Re-run `spikes/` on that tag before trusting a result.
>
> This file is what overturned "vector queries can't combine with filters": a filter after `YIELD` runs, and it applies **after the top-k cut** (section D1). Product scope still comes from [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md).

# v3_00 — P0 Engine Spike Findings (Executed, Not Read)

**Date:** 15 Oct 2026
**Method:** queries executed against a live `falkordb/falkordb:latest` container (engine reports module version **42201**), Python `falkordb` client on Python 3.12.10.
**Scripts:** `spikes/p0_engine_semantics.py`, `spikes/p0b_capability_inventory.py`, `spikes/p0c_algorithm_signatures.py`, `spikes/p0d_invocation_shapes.py`

> **Why this file exists.** Every FalkorDB fact the project held before today came from reading `docs.falkordb.com`. This file replaces reading with execution. Several documented facts turned out to be **wrong for this build**, and one correctness trap was found that the docs do not mention at all.

---

## A. Findings that unblock the build

### A1. `timestamp()` returns milliseconds — CONFIRMED
```
timestamp() = 1792112280980
python time.time()*1000 = 1792112280982   (drift 2.4 ms)
```
Unit is **milliseconds**. `time()` and `unixtime()` are both **unknown functions** — they do not exist. All lease timestamps, TTL arithmetic, and ordering keys use `timestamp()` in ms.

*This was a hard blocker on all coordination code. Cleared.*

### A2. Multi-type variable-length patterns work — CONFIRMED
```cypher
MATCH p=(a:N {n:'a'})-[:CAUSED_BY|RESULTED_IN*1..3]->(z) RETURN z.n, length(p)
-- returns [['b',1], ['c',2]]
```
The causal traversal `[:CAUSED_BY|RESULTED_IN*1..3]` — the pattern the whole "show how it got to the answer" story depends on — **works, and `length(p)` works alongside it**. This was the single riskiest P0 unknown. Cleared.

### A3. `FOREACH ... CASE` conditional write works — CONFIRMED
```cypher
FOREACH (x IN CASE WHEN cond THEN [1] ELSE [] END | SET n.p = x)
```
Works, and `ELSE []` is a true no-op (the property is untouched). The conditional-write idiom is available.

### A4. Empty `OPTIONAL MATCH` + `ORDER BY .. LIMIT 1` — CONFIRMED
With no events yet, the query still returns the root node with `prev = null`. This is the precondition for the event-chain fork fix.

### A5. The fork-race fix holds under real concurrency — CONFIRMED
8 threads appending concurrently to the same investigation's event chain:
```
8 events, 7 NEXT links (expected 7); no fork
```
Deriving `prev` **inside the query** (rather than passing it as a parameter) produces a single unbranched chain under concurrency. The bug found in `stuff.md` §5.1 has a verified fix.

### A6. Single-query atomic task lease — CONFIRMED (the core differentiator)
12 threads racing to claim one task in one graph:
```
winners = ['a1']   final status = claimed   owner = a1   errors = 0
```
**Exactly one winner, zero errors.** A single conditional `MATCH … WHERE … SET … RETURN` *is* an atomic lease. This is the coordination claim the whole product rests on, and it is now proven on the engine rather than inferred from docs.

### A7. Vector index works end-to-end — CONFIRMED
```
CREATE VECTOR INDEX FOR (n:Doc) ON (n.emb) OPTIONS {dimension:4, similarityFunction:'cosine'}
CREATE (:Doc {emb: vecf32([1.0,0.0,0.0,0.0])})
CALL db.idx.vector.queryNodes('Doc','emb',2,vecf32([1.0,0.0,0.0,0.0])) YIELD node, score
-- returns [['d1', 0.0], ['d2', 1.0]]
```
The yielded column is **`node`** (not `entity`). `score` is a **distance** — `0.0` means identical under cosine. Create, insert, and query all work.

---

## B. Documentation was WRONG — corrections from execution

### B1. The algorithm list does not match the docs

`CALL dbms.procedures()` on this build registers exactly **11** `algo.*` procedures:

```
algo.AStar  algo.betweenness  algo.BFS  algo.HarmonicCentrality
algo.labelPropagation  algo.maxFlow  algo.MSF  algo.pageRank
algo.SPpaths  algo.SSpaths  algo.WCC
```

| Docs / prior belief | Running engine | Verdict |
|---|---|---|
| `algo.CDLP` exists | **not registered** | docs wrong — community detection is `algo.labelPropagation` |
| `algo.labelPropagation` does NOT exist | **it exists** | **round-2 research was wrong**; round-1 was right |
| `algo.betweennessCentrality` | **`algo.betweenness`** (no "Centrality") | docs wrong on the name |
| `algo.MaxFlow` | **`algo.maxFlow`** (lowercase m) | casing differs |
| `algo.harmonicCentrality` | **`algo.HarmonicCentrality`** (capital H) | casing differs |
| — | `algo.labelPropagation` yields `communityId` | confirmed |

**Consequence for `PLAN_SHELDON.md` and `stuff.md`:** every mention of `algo.CDLP` must become `algo.labelPropagation`, and `algo.betweennessCentrality` must become `algo.betweenness`. Round-2's "correction" that removed label propagation was itself the error. This is the second time a confidently-held FalkorDB fact has flipped; the pattern is that docs and the build diverge, so **the engine is the only authority**.

### B2. Vector queries DO combine with property filters

The docs state vector queries cannot be combined with property filters. On this build, **both** forms work:

```cypher
-- WHERE form
CALL db.idx.vector.queryNodes('D','emb',3,vecf32([1,0,0,0])) YIELD node,score
WHERE node.team='blue' RETURN node.id,score      -- PASS

-- MATCH-join form
CALL db.idx.vector.queryNodes('D','emb',3,vecf32([1,0,0,0])) YIELD node,score
MATCH (node) WHERE node.team='blue' RETURN node.id,score   -- PASS
```

### B3. Whole-graph algorithms take **no** arguments, and passing some fails **silently**

The most dangerous finding. Argument shape by algorithm:

| Algorithm | Correct invocation | Passing `('S','L')` |
|---|---|---|
| `algo.WCC` | `algo.WCC()` | returns **[]** — no error |
| `algo.labelPropagation` | `algo.labelPropagation()` | returns **[]** — no error |
| `algo.betweenness` | `algo.betweenness()` | returns **[]** — no error |
| `algo.pageRank` | `algo.pageRank(label, relType)` or `(NULL, NULL)` | works with 2 args |

```
algo.WCC()                    -> [['a',0],['b',0],['c',0],['d',0],['e',4]]   <- correct
algo.WCC('S','L')             -> []                                          <- silent empty
algo.WCC(NULL, NULL)          -> []                                          <- silent empty
```

**A wrong call to `algo.WCC` does not raise. It returns nothing.** Any code that treats "no rows" as "no result" instead of "bad invocation" will silently produce wrong answers. This must be a lint or a wrapper in the codebase, not a comment (see `principle-encode-lessons-in-structure`).

### B4. `algo.AStar` is geographic, not a general A*
```
algo.AStar(...) -> Error: latitudeProperty and longitudeProperty are required
```
It is a map-routing algorithm (needs lat/long properties), **not** usable as generic shortest-path. Do not plan around it. `algo.SPpaths` covers path queries:
```cypher
MATCH (a:S {n:'a'}), (d:S {n:'d'})
CALL algo.SPpaths({sourceNode:a, targetNode:d, relTypes:['L'], maxLen:3})
YIELD path RETURN [n IN nodes(path) | n.n]     -- PASS -> [['a','d']]
```
Note the arguments are **node references**, not ID strings — passing strings errors with `sourceNode must be of type Node`.

---

## C. Verified algorithm surface for Sheldon

Only what Sheldon needs, with the exact working invocation:

| Need | Use | Verified |
|---|---|---|
| Causal / temporal traversal | plain Cypher `[:CAUSED_BY\|RESULTED_IN*1..3]` + `length(p)` | PASS |
| Rank "hot" events | `CALL algo.pageRank(label, relType) YIELD node, score` | PASS |
| Bridging events | `CALL algo.betweenness() YIELD node, score` | PASS |
| Cluster related incidents | `CALL algo.labelPropagation() YIELD node, communityId` | PASS |
| Connected components | `CALL algo.WCC() YIELD node, componentId` | PASS |
| Path between two events | `CALL algo.SPpaths({sourceNode, targetNode, relTypes, maxLen}) YIELD path` | PASS |
| Local neighbourhood | `CALL algo.BFS(node, depth, relType) YIELD nodes, edges` | PASS |

`algo.HarmonicCentrality` resolves its config keys but rejects the ones tried; `algo.MSF` / `algo.maxFlow` are not needed. Not worth further spike time.

---

## D. Resolved during this pass

### D1. Vector filter is applied AFTER the top-k cut — SILENT WRONG RESULTS
This is the most dangerous finding in the whole spike series, and it contradicts the optimistic reading of B2.

Test: 4 red docs at cosine distance ~0.00005 from the query, 1 blue doc at distance 1.0.
```
k=5, no filter            -> [['r1',0.0],['r2',...],['r3',...],['r4',...],['b1',1.0]]
k=2, no filter            -> [['r1',0.0], ['r2',...]]        <- blue is 5th
k=2, WHERE team='blue'    -> []                              <- EMPTY, no error
k=2, MATCH ... team='blue'-> []                              <- EMPTY, no error
```
**A filtered vector search silently returns nothing if the matching nodes rank outside the top-k.** It does not error, does not warn, and does not fall back.

Consequences, and they are architectural:
- "Find the k most similar events **belonging to investigation X**" is **not implementable** as a single filtered vector query. Any `WHERE` on a property after `queryNodes` is a post-cut filter over a fixed window.
- **This is a strong argument for graph-per-investigation scoping** (the design already chosen): if the graph *is* the investigation, no property filter is needed and the cliff cannot bite. What looked like a workaround is now the correct architecture for correctness reasons, not just tidiness.
- If a filter is ever needed, the only safe forms are: over-fetch with a large k and filter in application code (unbounded and approximate), or vector top-k **then** a graph traversal to filter by connected structure (exact within the window, still window-limited).
- **This becomes a lint/codepath rule**: no `WHERE` on node properties downstream of `db.idx.vector.queryNodes` in shipped code.

## E2. Still open

- **D2.** Does the fork-fix chain hold at higher concurrency (100+ writers) and across a real second investigation in the same graph? 8 threads is a smoke test, not a load test.
- **D3.** Complete the round-2 correction list: `research/v2_05_falkordb_technical.md` and `research/00_RESEARCH_INDEX.md` still carry the wrong `algo.CDLP` / `labelPropagation` claims and must be fixed.
- **D4.** `MSF` yields something other than `node`; `HarmonicCentrality`'s single argument is undocumented. Neither is needed, but the docs page should not be trusted as a signature reference.

---

## E. What this changes in the plan

- **P0 gate: PASSED.** The engine semantics the build depended on are resolved, and the two headline mechanism claims (fork-free chain, atomic lease) are proven on the engine.
- **`algo.CDLP` → `algo.labelPropagation`** everywhere; `algo.betweennessCentrality` → `algo.betweenness`.
- **Add a wrapper** around algorithm calls that **fails loudly** on an empty result from a whole-graph procedure, so B3 cannot bite.
- **Remove `algo.AStar`** from any planned use.
- **D1 becomes a P1 blocker** (before retrieval, not before the demo — the 48h demo can use exact-k where k is generous).
- **Docker + Python venv are now part of the setup path**, not future work: `docker run -d --name sheldon-falkor -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest`, then `.venv\Scripts\python.exe`.

*All findings above are from execution on 15 Oct 2026 against engine module version 42201. Re-run the spikes after any image update.*
