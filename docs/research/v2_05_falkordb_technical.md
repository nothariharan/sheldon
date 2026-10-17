> **Precedence:** [`facts.md`](../facts.md), [`REPORT.md`](../decisions/REPORT.md), and [`papers.md`](../engine/papers.md) override this file.
>
> **Do not quote or implement these. They were disproved:**
> - "vector queries can't combine with filters" — a `WHERE` after `YIELD` runs, but only on the top-k, so recall drops. Per-investigation graphs are a choice, not a requirement (see [`facts.md`](../facts.md)).
> - "no competitor has GRAPH.COPY" — false. It is an eval-reset method, not a novelty claim.
> - MIRIX arXiv `2501.02388` — the id is **`2507.07957`** ("MIRIX: Multi-Agent Memory System for LLM-Based Agents").
> - HippoRAG "+38.6%" — it is **+38.6 points** AR@5 on 2Wiki (37.1 → 75.7), not a relative percent.
> - any personalized-PageRank design — `algo.pageRank` is global only. Personalized PageRank does not exist.
>
> The product name is **Sheldon**. SynapseOS was an earlier name.

# FalkorDB Technical Ground Truth (Round 2)

**Claim prefix:** M5-  **Research date:** 2026-10-15
**Method:** Direct fetch of docs.falkordb.com pages listed below. Every command and number in this file is quoted or copied from a page fetched on this date. No procedure name, parameter, or benchmark figure in this file is recalled from memory.

**Sources fetched:**
- https://docs.falkordb.com/ (index, agent instructions)
- https://docs.falkordb.com/llms.txt
- https://docs.falkordb.com/_llms/falkor-db/documentation.txt (page index)
- https://docs.falkordb.com/commands/graph.copy.md
- https://docs.falkordb.com/design/concurrency.md
- https://docs.falkordb.com/cypher/indexing/vector-index.md
- https://docs.falkordb.com/algorithms/index.md
- https://docs.falkordb.com/algorithms/pagerank.md
- https://docs.falkordb.com/design/index.md
- https://docs.falkordb.com/cypher/cheat-sheet.md
- https://docs.falkordb.com/agentic-memory/graphiti.md
- https://docs.falkordb.com/agentic-memory/mem0.md

---

## 1. What FalkorDB is

- A graph database built **on top of Redis** using the Redis Modules API; a native C implementation. Queries are issued as OpenCypher via `GRAPH.QUERY` and `GRAPH.RO_QUERY` — not over Bolt or a SQL connection (per docs.falkordb.com agent instructions).
- FalkorDB implements a **subset of OpenCypher version 9** plus proprietary extensions. The docs page repeatedly warns: "Do not assume Neo4j-only syntax or procedures are available — check /cypher/cypher-support and /cypher/known-limitations before using a clause."
- License: **Server Side Public License v1 (SSPLv1)**.
- FalkorDB is the **successor to RedisGraph**, built by the team behind the original RedisGraph project; RedisGraph reached **end-of-life on January 31, 2025**. Docs explicitly instruct: do not present RedisGraph commands, versions, or limitations as current FalkorDB behavior.
- The docs site covers four products and instructs you to name which one an answer applies to: FalkorDB (core), FalkorDB Cloud, FalkorDB Enterprise, and the GraphRAG SDK.

## 2. Internal representation

Quoted from https://docs.falkordb.com/design/index.md:

- "FalkorDB uses sparse adjacency matrices to represent graphs." A directed relationship from source S to destination T sets `M[S,T] = 1`. Rows represent source nodes, columns destination nodes.
- Every graph has at least **one relation-type-agnostic adjacency matrix ("THE adjacency matrix")**, plus **one dedicated matrix per typed relationship**. A graph with `visits` and `friend` relation types maintains three matrices: the global one, a visit matrix, a friend matrix.
- **One additional symmetric matrix per node label**, with ones along the main diagonal, representing typed nodes.
- Traversal is done by **matrix multiplication**: friends-of-friends is `F^2`. A pattern like `(N0)-[A]->(N1)-[B]->(N2)<-[A]-(N3)` is translated into `A * B * Transpose(A)`.
- FalkorDB uses **GraphBLAS**, a "standard API similar to BLAS", currently using the **CSC (compressed sparse columns)** format. Docs note the underlying format is subject to change.
- Data lives **in RAM** using memory-efficient custom data structures, with **on-disk persistence**.
- Docs benchmark statement: "inserting a new relationship is done in O(1). FalkorDB is able to create over 1 million nodes under half a second and form 500K relations within 0.3 of a second." Note this is a docs-page claim with "depending on the underlying hardware results may vary."

## 3. Concurrency and atomicity — the most important verified page for Track 02

All quoted from https://docs.falkordb.com/design/concurrency.md.

**Model:** "FalkorDB uses a per-graph reader-writer model: many read queries can run in parallel against the same graph, while write queries are serialized so that only one write executes at a time on a given graph. Readers always observe a consistent snapshot of the graph as it existed when the read began — they never see partial state from an in-flight write."

Specific verified guarantees:

| Guarantee | Exact doc statement |
|---|---|
| Single-query atomicity | "Every query that modifies the graph — using any combination of `CREATE`, `SET`, `DELETE`, or `MERGE` — is **atomic**. The entire query either succeeds completely or fails without applying any partial changes." |
| Schema-change atomicity | "If a query that creates a new label (e.g., via `CREATE (:NewLabel)`) subsequently fails, that label is rolled back along with all other modifications made by the query." |
| Compound clauses | "Atomicity extends to queries that use `WITH`, `UNION`, or other compound clauses." |
| Parallel reads | "Multiple read-only queries can execute in parallel against the same graph. Read queries do not block each other." Concurrency governed by the `THREAD_COUNT` configuration parameter. |
| Serialized writes | "Only **one write query** executes at a time on a given graph. If multiple write queries arrive concurrently, they are queued and executed one at a time in arrival order." |
| Reader isolation | "While a write query is executing, concurrent read queries observe the graph state as it was **before** the write began... an isolation level similar to **snapshot isolation** for readers." |
| Multi-query transactions | "FalkorDB does not natively support multi-query transactions. For cases where multiple independent queries must all succeed or fail together, use Redis `MULTI`/`EXEC` blocks. Note that this serializes all enclosed commands across all graphs." |
| Write scaling limit | "Write-heavy workloads are bottlenecked by write serialization. Consider batching multiple changes into a single query where possible." |

**Consequence for our architecture (verified inference):** a single `GRAPH.QUERY` containing `MATCH ... SET ... RETURN` is atomic, so a task-lease claim expressed as ONE query cannot be double-claimed by two agents. This removes the need for external `SETNX` locking. This is the single strongest technical finding for Track 02 coordination.

**Consequence (caveat):** single-query atomicity does NOT give multi-step transaction semantics. Any read-modify-write spanning two queries is not protected. Two separate queries with a decision in between can race.

## 4. `GRAPH.COPY` — exact semantics

Quoted from https://docs.falkordb.com/commands/graph.copy.md:

- Usage: `GRAPH.COPY <src> <dest>`
- "The `GRAPH.COPY` command creates a copy of a graph, while the copy is performed the `src` graph is fully accessible."
- FAQ: "Yes. The source graph remains **fully accessible** for both reads and writes during the copy operation."
- FAQ: "Yes. `GRAPH.COPY` creates a complete clone of the source graph including all nodes, relationships, properties, indexes, and constraints."
- FAQ: "The command will return an error. You must delete the destination graph first using `GRAPH.DELETE` before copying to that key name."
- FAQ: "The copy reflects a consistent snapshot of the source graph at the time the command begins. Modifications to the source graph during the copy will not affect the destination."

**Correction to round-1 research:** round-1 said GRAPH.COPY "does not provide native 'zero-copy' semantics in the traditional OS sense". That is still true, but the docs add a fact round-1 missed and which is more useful to us: **the destination is a consistent snapshot, and indexes and constraints are copied.** That makes `GRAPH.COPY` a genuine candidate for speculative sandboxing with deterministic copy state, which is stronger than round-1's framing.

```python
from falkordb import FalkorDB
db = FalkorDB(host='localhost', port=6379)
graph_a = db.select_graph('A')
graph_a.query('CREATE (:Account {number: 516637})')
graph_z = graph_a.copy('Z')           # Python client method: .copy()
result = graph_z.query('MATCH (a:Account) RETURN a.number')
```
```bash
127.0.0.1:6379> GRAPH.COPY A Z
"OK"
```

**Latency:** NOT DOCUMENTED. The docs give no figure for copy time. Do not claim a number.

## 5. Vector index — exact syntax

Quoted from https://docs.falkordb.com/cypher/indexing/vector-index.md and the cheat sheet.

- FalkorDB's vector index uses the **HNSW (Hierarchical Navigable Small World)** algorithm with cosine similarity or Euclidean distance.
- Supported dimension range: **1–4096**.
- Similarity functions supported: **`cosine` and `euclidean` only**. Docs: "Currently, the only supported similarity functions are 'euclidean' or 'cosine'."

```cypher
CREATE VECTOR INDEX FOR (p:Product) ON (p.embedding)
OPTIONS {dimension: 768, similarityFunction: 'cosine'}
```
| Option | Required | Default | Description |
|---|---|---|---|
| `dimension` | Yes | — | Vector length, 1–4096 |
| `similarityFunction` | Yes | — | `cosine` or `euclidean` |
| `M` | No | `16` | Max outgoing edges per HNSW node |
| `efConstruction` | No | `200` | Candidates evaluated while building |
| `efRuntime` | No | `10` | Candidates evaluated while searching |

Indexes on relationships are supported:
```cypher
CREATE VECTOR INDEX FOR ()-[e:Call]->() ON (e.summary)
OPTIONS {dimension: 128, similarityFunction: 'euclidean'}
```

Query:
```cypher
CALL db.idx.vector.queryNodes('Product', 'embedding', 10, vecf32(<array_of_vector_elements>))
YIELD node, score
```
Relationship variant: `CALL db.idx.vector.queryRelationships('RelType', 'attribute', k, vecf32(...)) YIELD relationship, score`

Drop: `DROP VECTOR INDEX FOR (p:Product) ON (p.embedding)`
List all indexes: `CALL db.indexes()`

**Documented limitations that affect retrieval design:**
- Docs: "Vector index queries do not combine with property filters." **Overstated.** Spike B2/D1: a `WHERE` after `YIELD` runs on the top-k only. See [`facts.md`](../facts.md).
- Results are approximate, not exact: "Returns approximate (not exact) nearest neighbors."
- Memory: "A 1M vector index with 768 dimensions (float32) requires ~3GB of memory."
- Sort direction depends on the function: cosine score higher = more similar (sort `DESC`); euclidean score is a distance (sort `ASC`).

## 6. Algorithms — verified complete list

Quoted from https://docs.falkordb.com/algorithms/index.md. Invoked as `CALL algo.<name>()` with `YIELD`.

| Category | Algorithm | Notes from docs |
|---|---|---|
| Pathfinding | `algo.BFS` | Level-by-level, optional target/max depth |
| Pathfinding | `algo.SPpaths` | Shortest paths between a source and one or more destinations |
| Pathfinding | `algo.AStar` | Haversine geographic heuristic |
| Pathfinding | `algo.SSpaths` | All paths from a single source |
| Pathfinding | `algo.MSF` | Minimum spanning forest |
| Centrality | `algo.pageRank` | Influence from incoming links |
| Centrality | `algo.betweenness` | Bridge nodes |
| Centrality | `algo.HarmonicCentrality` | Robust on disconnected graphs |
| Community | `algo.WCC` | Weakly connected components |
| Community | `algo.labelPropagation` | Label propagation |
| Network flow | `algo.maxFlow` | Source-to-sink max flow |

> ### ⚠ EXECUTED CORRECTION (15 Oct 2026) — supersedes the table above and the note below it
>
> The table above was transcribed from `docs.falkordb.com`. The table below was read from a **running engine** (module 42201) via `CALL dbms.procedures()`. Where they differ, the engine wins. Full detail: **`v3_00_p0_engine_spike_findings.md`**.
>
> - `algo.CDLP` **does not exist**. Community detection is `algo.labelPropagation()`, yielding `communityId`.
> - `algo.betweennessCentrality` **does not exist**. It is `algo.betweenness()`.
> - `algo.harmonicCentrality` → `algo.HarmonicCentrality` (capital H); `algo.MaxFlow` → `algo.maxFlow` (lowercase m).
> - **`algo.labelPropagation` DOES exist** — the correction note immediately below this table is itself wrong and is struck.
> - Whole-graph algorithms (`WCC`, `labelPropagation`, `betweenness`) take **no arguments**; `algo.WCC('S','L')` returns `[]` **silently**.
> - `algo.AStar` requires `latitudeProperty`/`longitudeProperty` — it is geographic, not a general A*. Do not plan around it.

**CORRECTION to round-1 research:** round-1 file `03_FALKORDB_TECHNICAL_DEEP_DIVE.md` listed `algo.CDLP`, `algo.WCC`, `algo.betweennessCentrality` correctly but round-1's `05_FACT_CHECK` audit claimed `algo.labelPropagation` and `algo.bipartite` exist. **Neither `algo.labelPropagation` nor `algo.bipartite` appears in the docs.** Label propagation in FalkorDB is `algo.CDLP`. Do not use `algo.labelPropagation` or `algo.bipartite` in build code.

**CORRECTION to round-1 research:** the exact name is `algo.SPpaths` and `algo.SSpaths` (with the trailing `s`), per both the docs index and the cheat sheet example. Round-1 wrote `algo.SPpath`. The cheat sheet shows the call taking a **map argument**, not positional parameters:

```cypher
MATCH (a:City {name: 'A'}), (g:City {name: 'G'})
CALL algo.SPpaths({
  sourceNode: a,
  targetNode: g,
  relTypes: ['ROAD'],
  weightProp: 'dist',
  pathCount: 1
}) YIELD path, pathWeight
RETURN path, pathWeight
```

PageRank exact signature (from the pagerank page):
```cypher
CALL algo.pageRank(label, relationship-type)
YIELD node, score
```
| Param | Type | Default | Description |
|---|---|---|---|
| `label` | String | null | Label of nodes to run on. If null, all nodes. |
| `relationship-type` | String | null | Relationship type to traverse. If null, all types. |

Yields `node`, `score` (float). Docs: scores are relative, "the sum of all scores in a graph equals 1.0", power-law distribution, based on incoming relationships.

**What is NOT documented:** there is no Personalized PageRank (`algo.ppr`) procedure in the algorithms list. FalkorDB ships global PageRank only. Do not implement HippoRAG-style PPR in application code either. Personalized PageRank is out of scope. Use a bounded Cypher traversal. Do not claim FalkorDB has built-in PPR.

## 7. Useful introspection procedures (verified from the cheat sheet)

| Procedure | Yields |
|---|---|
| `db.labels()` | `label` |
| `db.relationshipTypes()` | `relationshipType` |
| `db.propertyKeys()` | `propertyKey` |
| `db.indexes()` | `label`, `properties`, `types`, `options`, `language`, `stopwords`, `entitytype`, `status`, `info` |
| `db.constraints()` | `type`, `label`, `properties`, `entitytype`, `status` |
| `db.meta.stats()` | `labels`, `relTypes`, `relCount`, `nodeCount`, `labelCount`, `relTypeCount`, `propertyKeyCount` |
| `db.idx.fulltext.queryNodes(label, query)` | `node`, `score` |
| `db.idx.vector.queryNodes(label, attr, k, query)` | `node`, `score` |
| `dbms.procedures()` | `name`, `mode` |

Correction: the introspection procedure is `db.relationshipTypes()`, **not** `db.relTypes()`. Round-1 file `03` did not mention it, but the index page link text says `db.relationshipTypes`; the cheat sheet procedure table confirms `db.relationshipTypes()` yielding `relationshipType`.

Fulltext index (RediSearch syntax):
```cypher
CREATE FULLTEXT INDEX FOR (n:Movie) ON (n.title)
CALL db.idx.fulltext.queryNodes('Movie', 'Jun*') YIELD node, score
CALL db.idx.fulltext.queryNodes('Movie', '%Jangle%1') YIELD node, score
```
`%term%distance` is fuzzy matching with max Levenshtein distance 1–3, default 1.

## 8. Known limitations that will bite us

All quoted from the cheat sheet "Gotchas" section:

- "Indexes do not optimize `<>` filters — those still fall back to a full scan of the label or the relationship type."
- "`LIMIT` does not restrict eager operations. `UNWIND [1,2,3] AS v CREATE (a {property: v}) RETURN a LIMIT 1` creates three nodes and returns one." **This directly affects any pattern that writes after an `UNWIND` and then applies `LIMIT`.**
- "When a relationship in a pattern is never referenced elsewhere, FalkorDB only verifies that at least one match exists. Reference the alias (for example `WHERE ID(e) >= 0`) when you need every match." **This affects edge-count and edge-property writes.**
- "Aggregation functions are not allowed inside pattern comprehensions."
- "Regular-expression operators are unsupported; use `STARTS WITH`, `ENDS WITH`, `CONTAINS`, or `string.matchRegEx()`."
- "Label expressions such as `(n:A|B)` in node patterns are unsupported. Filter with `WHERE n:A OR n:B`."
- Docs: "Vector index queries do not combine with property filters." Overstated — see M5-13.
- "A mandatory `MATCH` cannot follow an `OPTIONAL MATCH`."
- "MERGE on a whole path either matches the entire path or creates all of it. Merging `(a {name: 'Alice'})-[:KNOWS]->(b {name: 'Bob'})` in one clause duplicates Alice and Bob when the relationship is missing." Merge one entity per clause.
- Constraints are created with a Redis command, not Cypher, and are built asynchronously; a UNIQUE constraint "requires a supporting range index on exactly the same properties".

Useful scalar functions available (cheat sheet): `timestamp()`, `randomUUID()`, `id()`, `labels()`, `type()`, `properties()`, `startNode()`, `endNode()`, `indegree()`, `outdegree()`, `nodes()`, `relationships()`, `length()`, `shortestPath()`, `allShortestPaths()`, `vecf32()`, `vec.cosineDistance()`, `vec.euclideanDistance()`, `exp()`, `log()`.

Note for memory-decay math: `exp()` and `log()` exist, and `timestamp()` exists, so an Ebbinghaus-style decay expression is expressible in pure Cypher.

## 9. Deployment and client

- Docker: `docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest`
- Port **6379 = FalkorDB Server**, port **3000 = FalkorDB Browser** web UI at `http://localhost:3000`.
- Python client package is `falkordb` (PyPI `FalkorDB`), `from falkordb import FalkorDB`. Docs show lowercase `import falkordb` in the page example and `from falkordb import FalkorDB` in the clients example; package name is `FalkorDB` on PyPI.
- Named graphs are selected with `db.select_graph('MotoGP')`; the graph object has `.query()`, `.delete()`, `.copy()`, `.explain()`.
- Node.js: `import { FalkorDB } from 'falkordb'`, `FalkorDB.connect({socket: {host, port}})`, `client.selectGraph(...)`.
- Other clients listed in docs: Java, Rust, Go, PHP, C#. Java shows `FalkorDB.driver("localhost", 6379)` and `driver.graph("MotoGP")`.
- RESP and Bolt protocols both supported (Bolt is described as "Experimental feature for compatibility with BOLT-based tools and Neo4j client libraries").
- Bulk load: `pip install falkordb-bulk-loader`, `falkordb-bulk-insert GRAPHNAME -n nodes.csv -r edges.csv`.
- `FalkorDBLite` exists as an embedded runtime for Python and TypeScript, "without managing external servers".
- Graph management commands: `GRAPH.QUERY`, `GRAPH.RO_QUERY`, `GRAPH.DELETE`, `GRAPH.EXPLAIN`, `GRAPH.PROFILE`, `GRAPH.LIST`, `GRAPH.COPY`, `GRAPH.INFO`, `GRAPH.MEMORY USAGE`, `GRAPH.SLOWLOG`, `GRAPH.CONFIG SET/GET`, `GRAPH.CONSTRAINT CREATE/DROP`.
- Config parameter named in docs: `THREAD_COUNT` (thread pool size), plus `import_folder` for `LOAD CSV`. Set with `GRAPH.CONFIG SET` or at startup; "Values are not persisted across a server restart."

**Multigraph isolation:** the docs verify that a single instance holds many named graphs and that `GRAPH.LIST` returns every graph key in the keyspace. The phrase "thousands of isolated graphs" comes from the hackathon page, not the FalkorDB docs I fetched; the docs page for Graphiti says "Isolated graph instances for different users or agents". **The specific number "thousands" is NOT in the FalkorDB docs I fetched — treat as a vendor marketing claim, not a documented limit.**

## 10. Documented FalkorDB integrations relevant to us

From the docs "Agentic Memory" and "GenAI Tools" sections:

- **Graphiti** — `pip install graphiti-core[falkordb]`, connect with `Graphiti(uri="falkor://localhost:6379")`, `graph_name` parameter gives per-tenant isolation (docs example creates `user1_memory`, `user2_memory` as separate graph names). One-time `await graphiti.build_indices_and_constraints()`. Prerequisites: Python 3.10+. Docs list LLM/embedding provider as OpenAI.
- **Mem0** — plugin `mem0-falkordb` (`pip install mem0-falkordb`, from `github.com/FalkorDB/mem0-falkordb`), registered at runtime via `from mem0_falkordb import register; register()`. Docs: "Each user automatically gets their own isolated FalkorDB graph (e.g., `mem0_alice`, `mem0_bob`)". Config key `database` is a graph-name prefix, each user gets `{database}_{user_id}`. `delete_all(user_id=...)` "simply drops the user graph". Plugin provides `base_label` using `__Entity__`.
- **Cognee** — has a FalkorDB integration page in the same Agentic Memory section.
- **GraphRAG SDK** — first-class FalkorDB product; the docs state "GraphRAG-SDK on FalkorDB scores 71.48 overall on GraphRAG-Bench vs 55.39 for vector RAG with reranking" with a full methodology page. **Caveat: this is a vendor-published benchmark of FalkorDB's own SDK. Cite it as vendor-reported, never as independent.**
- Also documented: LangChain, LangGraph, LlamaIndex, AG2 (AutoGen), AWS GraphRAG Toolkit, QueryWeaver (Text2SQL, PostgreSQL/MySQL/Snowflake), Code-Graph, Graphify, MCP server (stdio/SSE), n8n, PyTorch Geometric, Snowflake, Spring Data, Apache Jena, Kafka Connect sink.

## 11. Corrections to round-1 research (file `research/03_FALKORDB_TECHNICAL_DEEP_DIVE.md`)

| Round-1 claim | Verdict | Correct statement |
|---|---|---|
| `algo.labelPropagation`, `algo.bipartite` exist | CORRECTED | Neither appears in FalkorDB docs. Use `algo.CDLP` for label propagation. |
| `algo.SPpath` | CORRECTED | Exact documented names are `algo.SPpaths` (point-to-point) and `algo.SSpaths` (single source to all). `algo.SPpaths` takes a map argument, not positional args. |
| `algo.betweennessCentrality()` yields `node, score` | UNVERIFIED for exact yield fields | Only `algo.pageRank` yield fields were verified this pass (`node`, `score`). Verify each algorithm's YIELD on its own docs page before writing build code. |
| `algo.CDLP()` yields `community_id` | UNVERIFIED this pass | Not confirmed from a fetched page. Verify before use. |
| `algo.WCC()` yields `component_id` | UNVERIFIED this pass | Not confirmed from a fetched page. Verify before use. |
| GRAPH.COPY "sub-second for typical agent memory graphs (< 100k nodes)" | SOFTENED | No latency figure in the docs at all. Say "latency not documented; measure on your own graph size." Round-1's parenthetical size guess has no source. |
| In-memory C engine with "single-threaded event loop" | SOFTENED | The concurrency page documents a thread pool (`THREAD_COUNT`) with parallel reads and a serialized FIFO write queue — not a single-threaded event loop. Reads are explicitly parallel. Round-1's model was wrong about reads. |
| "thousands of isolated named graphs per instance" | SOFTENED | Verified that many named graphs coexist per instance and that Graphiti's pattern is one graph per user/agent. The number "thousands" is not in the docs I fetched. |
| p50 ~55ms / p90 ~108ms / p99 ~136ms vs Neo4j on SNAP Pokec | NOT RE-VERIFIED THIS PASS | These round-1 numbers were not on any page I fetched. Do not quote them in a submission without re-fetching the benchmark page. |
| Neo4j Cypher "Full", FalkorDB "Full" | CORRECTED | FalkorDB documents a **subset** of OpenCypher v9 plus extensions, with a dedicated "Known limitations" page and a cypher-support coverage page. "Full" overstates it. |
| `CALL db.idx.vector.queryNodes('Entity', 'embedding', 5, vecf32($query_vector))` | VERIFIED with correction | Correct procedure and signature. Round-1 wrote `YIELD entity, score`; the docs yield `node, score`. The yielded column name is `node`, not `entity`. |

## Claims table

| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| M5-01 | FalkorDB is a Redis module, native C, OpenCypher subset v9 with extensions | docs.falkordb.com/design/index.md | VERIFIED | |
| M5-02 | Graphs stored as sparse adjacency matrices; one global matrix plus one per relationship type plus one symmetric diagonal matrix per label | docs.falkordb.com/design/index.md | VERIFIED | Docs page |
| M5-03 | Traversal performed by matrix multiplication (e.g. F^2 for friends-of-friends); GraphBLAS used; CSC format | docs.falkordb.com/design/index.md | VERIFIED | |
| M5-04 | Per-graph reader-writer model: parallel reads, serialized writes FIFO | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M5-05 | Every write query is atomic; failed writes roll back including new labels | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M5-06 | Readers see snapshot isolation: state as of query start, never partial | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M5-07 | No native multi-query transactions; use Redis MULTI/EXEC, which serializes across all graphs | docs.falkordb.com/design/concurrency.md | VERIFIED | Important caveat for task leasing |
| M5-08 | GRAPH.COPY copies nodes, relationships, properties, indexes, constraints; source fully accessible; dest must not exist; dest is a consistent snapshot | docs.falkordb.com/commands/graph.copy.md | VERIFIED | |
| M5-09 | Vector index uses HNSW, 1-4096 dims, cosine or euclidean only | docs.falkordb.com/cypher/indexing/vector-index.md | VERIFIED | |
| M5-10 | Algorithm list is exactly BFS, SPpaths, AStar, SSpaths, MSF, pageRank, betweennessCentrality, harmonicCentrality, WCC, CDLP, MaxFlow | docs.falkordb.com/algorithms/index.md | VERIFIED | No labelPropagation, no bipartite |
| M5-11 | algo.pageRank(label, relationship-type) YIELD node, score; both params default null | docs.falkordb.com/algorithms/pagerank.md | VERIFIED | |
| M5-12 | No Personalized PageRank procedure exists in the docs | docs.falkordb.com/algorithms/index.md | VERIFIED (negative) | Full algorithm list fetched; no ppr |
| M5-13 | Vector index queries do not combine with property filters | docs.falkordb.com/cypher/cheat-sheet.md | OVERSTATED | Spike B2/D1: the filter runs after the top-k cut. See [`facts.md`](../facts.md) |
| M5-14 | LIMIT does not restrict eager write operations | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED | Directly affects write-then-limit queries |
| M5-15 | Unreferenced relationship alias only verifies at least one match exists | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED | Affects edge property writes |
| M5-16 | Docker run command, port 6379 server, port 3000 browser | docs.falkordb.com/index.md | VERIFIED | |
| M5-17 | db.relationshipTypes() yields relationshipType | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED | |
| M5-18 | graphiti-core[falkordb] is the install extra; falkor:// URI scheme | docs.falkordb.com/agentic-memory/graphiti.md | VERIFIED | |
| M5-19 | mem0-falkordb plugin exists, runtime-patched via register(), per-user graphs named {database}_{user_id} | docs.falkordb.com/agentic-memory/mem0.md | VERIFIED | |
| M5-20 | GRAPH.COPY latency is not documented | (absence on graph.copy.md) | VERIFIED (negative) | Do not quote a figure |
| M5-21 | GraphBLAS GraphBLAS "standard API similar to BLAS", CSC format "subject to change" | docs.falkordb.com/design/index.md | VERIFIED | |
| M5-22 | Timestamp, randomUUID, id, labels, type, properties, startNode, endNode, indegree, outdegree, exp, log all exist as functions | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED | Enables Cypher-native decay math |
| M5-23 | RedisGraph reached EOL 2025-01-31; FalkorDB is the successor by the same team | docs.falkordb.com/llms.txt agent instructions | VERIFIED | |

## NOT DOCUMENTED / could not verify

- `algo.CDLP`, `algo.WCC`, `algo.betweennessCentrality`, `algo.harmonicCentrality`, `algo.MaxFlow` exact YIELD column names (only `algo.pageRank` was fetched in full).
- `algo.BFS`, `algo.AStar`, `algo.MSF`, `algo.SSpaths` exact signatures and parameters.
- Any latency or throughput number for `GRAPH.COPY`, `algo.pageRank`, or vector search.
- The batch `GRAPH.BULK` binary endpoint spec exists in the design section but was not fetched.
- The "thousands of isolated graphs" figure from the hackathon page.
- Round-1's Pokec benchmark numbers (p50/p90/p99 vs Neo4j) — page not fetched this pass.
- Whether FalkorDB's Cypher implementation has a per-query configurable timeout default (the command page lists "optional query timeout" for GRAPH.QUERY but the parameter name was not captured).

## Coordination log

- 2026-10-15 main agent wrote this file directly after seven subagent attempts were interrupted or returned empty. Subagents could not complete; this file is built only from pages fetched by the main agent on this date.
- Round-1 file `research/03_FALKORDB_TECHNICAL_DEEP_DIVE.md` left unmodified; corrections are recorded in section 11 above.
- Build-critical fix: the yielded column from `db.idx.vector.queryNodes` is `node`, not `entity`. Round-1 code samples would have failed on `RETURN entity.name`.
