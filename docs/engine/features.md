> Feature list with doc links. Each row says whether Sheldon uses it.
> [`facts.md`](../facts.md), [`REPORT.md`](../decisions/REPORT.md), and [`papers.md`](papers.md) override this file and the older research.
> `GRAPH.COPY` stays as the eval-reset method. Branch-and-merge sandboxing stays cut.
> Read this before guessing that an algorithm or command exists.

# FalkorDB feature inventory, mapped to Sheldon

Written Sat 17 Oct 2026. Sources: docs.falkordb.com and the FalkorDB GitHub release notes. **UNVERIFIED** means not confirmed from a primary source.

Sheldon scope is the three-part lead in REPORT.md: an evidence-gated refute, Q*, and a measured count of repeated failed steps.

## 0. Engine version: read this first
- **FalkorDB 6.0.0 (Sep 29 2026) is the first release on a new engine written in Rust.** It replaces the C engine used by every 4.x release. Same Redis module (`graph`), same `GRAPH.*` commands, same Cypher, same clients. Replication now sends only *effects* (format v3), so 4.x and 6.0 can't be mixed in one replica set, and `EFFECTS_THRESHOLD` is ignored. Full-text and vector indexes now run on RediSearch 8.6.1 (up from 2.6.23). Docker tags `latest` and `6.0.0` point at the Rust engine; `v4.x.y` and `edge-c` stay on C; there are no Alpine images for 6.0. Source: https://github.com/FalkorDB/FalkorDB/releases (6.0.0 notes). Since then: 6.0.1 (Oct 1, dependency refresh) and 6.0.2 (Oct 8). 6.0.2 fixes a wrong-dimension vector dropping an entity from every index on its label, clamps vector KNN `k`, validates vector index OPTIONS, fixes UDF edge cases, fixes GRAPH.CONSTRAINT/GRAPH.MEMORY parsing, and runs Docker as a non-root user.
- **The 6.0 notes say directly: "6.0 has the same procedures as 4.20.7".** A* (`algo.AStar`), CCH (`algo.CCH`) and Leiden/Louvain "have not shipped in any release" on the new engine and "are being ported". However, **v4.22.0 (C engine, Sep 30) does ship A*, Yen's k-shortest paths and the CCH index**. So the docs pages for A* and CCH describe the 4.22 line, not 6.0.
- **This contradicts the team's spike.** The spike (research/v3_00 line 4) ran on `falkordb/falkordb:latest` and the engine reported **module 42201 = 4.22.1**, not 6.0. Possible explanations: an old cached `latest` image, or the tag being repointed. **UNVERIFIED which.** Pulling `latest` today could switch engines mid-build. **Pin the exact tag you spiked on, re-run the spikes on it, and write the tag in the README.**

## 1. Inventory
| # | Feature | What it does | Docs | Introduced | Sheldon uses? |
|---|---|---|---|---|---|
| 1 | Per-graph concurrency, atomic write queries | Reads run in parallel, writes are serialized per graph, each write query is atomic. No multi-query transactions | https://docs.falkordb.com/design/concurrency | long-standing | **Yes, core.** PLAN §5.1 Fix 2, §7 `claim_task` |
| 2 | Many graphs per instance (multigraph keys) | Each graph is its own key: `GRAPH.LIST`, `GRAPH.DELETE`, one graph per tenant | https://docs.falkordb.com/commands/graph.list | long-standing | **Yes.** One graph per investigation plus a shared playbooks graph: stuff.md §4.4 l.186–188; PLAN §4 |
| 3 | GRAPH.COPY | `GRAPH.COPY src dest` copies a graph; the source stays fully accessible during the copy | https://docs.falkordb.com/commands/graph.copy | 4.x (exact version **UNVERIFIED**) | Eval reset for every run (REPORT.md). Not a novelty claim. Branch-and-merge stays cut |
| 4 | Vector index (HNSW) | `CREATE VECTOR INDEX`, `db.idx.vector.queryNodes/queryRelationships(... ) YIELD node, score`. Cosine/euclidean. A WHERE after YIELD runs on the top-k only | https://docs.falkordb.com/cypher/indexing/vector-index | 4.0 | **Yes.** `Event.embedding`: stuff.md l.182, §6 l.265; PLAN §4 table |
| 5 | Edge vector index | Vectors stored on relationships, queried with `db.idx.vector.queryRelationships` | same page; https://docs.falkordb.com/cypher/procedures | **UNVERIFIED** | Mentioned only (stuff.md l.29, research/03). Not used |
| 6 | Full-text index (RediSearch) | `db.idx.fulltext.createNodeIndex` or DDL; prefix and fuzzy (`%term%`) matching; scores; also on relationships (`queryRelationships`) | https://docs.falkordb.com/cypher/indexing/fulltext-index | long-standing; 6.0 moved to RediSearch 8.6.1 | **Yes.** `Event.text`: stuff.md l.179, §6 l.266; PLAN §4 |
| 7 | Range indexes | `CREATE INDEX FOR (e:Event) ON (e.ts)`; don't help `<>` filters | https://docs.falkordb.com/cypher/indexing/range-index | long-standing | **Yes.** stuff.md l.172–174 |
| 8 | Constraints (UNIQUE / MANDATORY) | `GRAPH.CONSTRAINT CREATE key MANDATORY\|UNIQUE NODE label\|RELATIONSHIP type PROPERTIES n ...`; writes that break them fail. UNIQUE requires a supporting exact-match index (4.20.7 notes) | https://docs.falkordb.com/commands/graph.constraint-create | 4.x (**UNVERIFIED** which version) | **Not used.** `schema.py # labels, indexes, constraints` is listed in stuff.md l.396, but no constraint is specified anywhere |
| 9 | UDFs (JavaScript) | `GRAPH.UDF LOAD [REPLACE] lib script`; `falkor.register(...)`; called as `lib.fn()` in Cypher; a `graph` object with `graph.traverse`/`getNodeById` (the old `falkor.traverse` was removed in 4.16). The FLEX library adds text, collections, similarity (jaccard), date, json, map, bitwise | https://docs.falkordb.com/udfs ; FLEX https://docs.falkordb.com/udfs/flex | v4.16 or earlier (exact **UNVERIFIED**) | **Not used** |
| 10 | Temporal types | `date`, `localtime`, `localdatetime`, `duration` (ISO 8601). Stored as properties, comparable, with component accessors | https://docs.falkordb.com/datatypes | **UNVERIFIED** | **Not used.** PLAN §7 takes `$now` from the service clock "sidestepping `timestamp()`'s unit". Times are not typed `localdatetime` |
| 11 | Point (geospatial) type | `point({latitude, longitude})`, `distance()` | https://docs.falkordb.com/datatypes | long-standing | Not used. **No fit** |
| 12 | algo.BFS | `CALL algo.BFS(src, max_depth, relType) YIELD nodes, edges` | https://docs.falkordb.com/algorithms/bfs | long-standing | Spike PASS (research/v3_00 l.145). Not in the read path |
| 13 | algo.SPpaths / algo.SSpaths | Weighted shortest paths, point-to-point or from one source; YIELD `path, pathWeight, pathCost` | /algorithms/sppath, /algorithms/sspath | 4.x | Listed in PLAN §4 l.132. Not used |
| 14 | algo.AStar | Shortest path guided by a haversine heuristic over lat/long | https://docs.falkordb.com/algorithms/astar | **4.22.0 (Sep 30); not in 6.0** | Listed only. **No fit** (needs coordinates) |
| 15 | CCH index | `CREATE CCH INDEX FOR ()-[e:T]->() ON (e.w)`; `db.idx.cch.query({...}) YIELD pathWeight, path` | https://docs.falkordb.com/cypher/indexing/cch-index | **4.22.0; not in 6.0** | Not used. **No fit** |
| 16 | algo.pageRank | Global PageRank over a label and relationship type; no personalization | https://docs.falkordb.com/algorithms/pagerank | long-standing | Considered and rejected for personalized use (stuff.md l.32, PLAN §4) |
| 17 | algo.betweenness | Betweenness centrality, `YIELD node, score`, config map | /algorithms/betweenness-centrality | 4.x | Listed only |
| 18 | algo.HarmonicCentrality | Harmonic centrality, `YIELD node, score, reachable` | /algorithms/harmonic-centrality | May 2026 | Listed only |
| 19 | algo.WCC | Weakly connected components; config map, or `null` | /algorithms/wcc | 4.x | Spike note: takes `null`/config, not `('S','L')` (PLAN l.132). Not used |
| 20 | algo.labelPropagation (docs call it CDLP) | Community detection | /algorithms/cdlp | 4.x | Listed only |
| 21 | algo.maxFlow / algo.MSF | Max flow, minimum spanning forest | /algorithms/maxflow, /algorithms/msf | maxFlow May 2026 | Not used. **No fit** |
| 22 | Path functions / variable-length multi-type patterns | `shortestPath()`, `[:A\|B*1..3]` | https://docs.falkordb.com/cypher | long-standing | **Yes, core to Q\*.** Spike A2 PASS (on 4.22.1) |
| 23 | GRAPH.RO_QUERY + per-query timeout | Read-only command that errors on writes; optional `timeout` ms; optional `version` arg that rejects the query if the graph version changed | https://docs.falkordb.com/commands/graph.ro-query | long-standing | Mentioned in research/v2_07 l.110 only. **Not in PLAN** |
| 24 | Server timeouts / config | `TIMEOUT_DEFAULT`, `TIMEOUT_MAX` (since v2.10), `THREAD_COUNT`, `CACHE_SIZE`, `RESULTSET_SIZE`, via `GRAPH.CONFIG` or `FALKORDB_ARGS` | https://docs.falkordb.com/getting-started/configuration | v2.10 | Not used (research/v2_05 l.315 leaves it as an open question) |
| 25 | GRAPH.MEMORY USAGE | Per-graph memory breakdown in MB (label/relation matrices, attributes by label, indices) | https://docs.falkordb.com/commands/graph.memory | **UNVERIFIED** | Not used |
| 26 | GRAPH.PROFILE / EXPLAIN / SLOWLOG | Query plan, per-op profiling, slow queries | /commands/graph.profile, /graph.explain, /graph.slowlog | long-standing | REPORT l.209 (product vision only) |
| 27 | db.* introspection | `db.labels`, `db.indexes`, `db.constraints`, `db.meta.stats`, `dbms.procedures()` | https://docs.falkordb.com/cypher/procedures | long-standing | **Yes.** PLAN §4 "Introspection" row (schema health and demo stats) |
| 28 | Replication / HA / cluster | Single primary with async replicas; replicas serve `RO_QUERY`; cluster docs. 6.0 is effects-only | https://docs.falkordb.com/operations/replication ; /operations/cluster | long-standing; changed in 6.0 | research/04 only. Not used (and shouldn't be) |
| 29 | ACL / auth | Redis ACL users for FalkorDB | https://docs.falkordb.com/commands/acl | — | Not used |
| 30 | Bolt protocol | **Experimental.** Docs say "not meant to be used in production"; Neo4j drivers on port 7687 via `BOLT_PORT` | https://docs.falkordb.com/integration/bolt-support | 4.0-a1 | Not used. **Avoid** |
| 31 | FalkorDB Browser | Web UI on :3000 bundled with the `falkordb/falkordb` image. Query editor, graph canvas, schema view, Chat panel (natural language through your own LLM key or Ollama), UDF libraries panel, data upload. v2.7.0 (Oct 15) adds 3D graph/schema view and desktop/mobile apps | https://docs.falkordb.com/browser ; https://github.com/FalkorDB/falkordb-browser/releases | — | **Yes.** Demo graph view: stuff.md l.54, l.382, l.508 |
| 32 | MCP server | `@falkordb/mcpserver` (npm/Docker): OpenCypher queries with read-only mode, create nodes/relationships, list/delete graphs, replica read-only support. v1.3.0 (Jul 1) adds schema discovery tools `get_graph_schema`, `get_node_schema`, `get_relationship_schema` | https://docs.falkordb.com/genai-tools/mcpserver ; https://github.com/FalkorDB/FalkorDB-MCPServer/releases | — | Optional wrapper, **cut first**: stuff.md l.359; PLAN §10 cut order |
| 33 | GraphRAG-SDK | Document → knowledge-graph pipeline with provenance and abstention. 1.0 on Apr 21; 1.2 (Jun 1), 1.3 (Jun 4: ontology auto-discovery), 1.4 (Aug 10: chunk extraction cache for `update()`) | https://docs.falkordb.com/graphrag ; https://github.com/FalkorDB/GraphRAG-SDK/releases | 1.0 Apr 21 2026 | Deliberately not built on it: stuff.md l.385; REPORT l.117 cites the benchmark |
| 34 | falkordb-py client | Python client; `graph.copy()`, `ro_query`, asyncio, UDF helpers. v1.8.0 Oct 14 (CI/deps), v1.7.0/1.7.1 Aug 13 (asyncio pool fix; redis restricted to 8.x) | https://github.com/FalkorDB/falkordb-py/releases | — | **Yes** (spike used the Python `falkordb` client) |
| 35 | FalkorDBLite | Embedded Redis + FalkorDB in one process (`pip install falkordblite`, also TS); persists given a path; "swap the connection line" to go remote. Latest v0.10.0 (May 2) **bundles server v4.18.3**, older than 4.22/6.0 | https://docs.falkordb.com/operations/falkordblite ; https://github.com/FalkorDB/falkordblite/releases | 2025 | REPORT l.208 (future deployment). Not used |
| 36 | Agent-memory integrations | Graphiti (plus its MCP server), Cognee, Mem0 (`mem0-falkordb`, per-user graphs), LangChain/LangGraph, LlamaIndex | https://docs.falkordb.com/agentic-memory | — | Graphiti positioned as the competitor (PLAN §2–3). Not used |
| 37 | Other integrations | Bulk loader, REST, Kafka Connect, n8n, Snowflake, PyG, Jena, Spring Data | https://docs.falkordb.com/integration | — | Not used. Not needed |

## 2. What Sheldon actually uses

Scope is REPORT.md, not this inventory. Constraints are a backstop: they cannot require an edge or check that a cited id exists. UDFs stay off on v4.22.1 because they are read-only and the fixes we would want are on 6.0.2. `GRAPH.COPY` is the eval reset. MCP, A*, CCH, Bolt, replication, and GraphRAG-SDK are cut. There is no personalized PageRank. A vector filter runs after the top-k cut ([`facts.md`](../facts.md)).

## 3. Doesn't fit, or risky for a ~36h build
- **A\*/CCH, point/`distance()`, MaxFlow, MSF:** no geography or flows in incident memory. A\*/CCH also aren't in 6.0. They are cut.
- **Global PageRank as "HippoRAG PPR":** there is no personalized PageRank ([`facts.md`](../facts.md), [`papers.md`](papers.md)). Don't claim it.
- **Bolt:** experimental, "not meant to be used in production".
- **Replication/cluster/HA:** async replicas can lag, so a stale read could break lease semantics. 6.0 also changed replication. Out of scope.
- **Switching engine mid-build (4.22 ↔ 6.0):** the biggest real risk. Pin the image tag.
- **FalkorDBLite:** bundles server 4.18.3 (older than your spike). Fine for CI, but don't demo on it without re-running the spikes.
- **Building on GraphRAG-SDK:** document ingestion isn't the headline, and it would blur "original work" (stuff.md l.385). Citing its abstention/provenance idea is fine.
- **MULTI/EXEC for coordination:** it serializes across all graphs (PLAN §4). Keep the single-query lease.
- **Vector-with-filter claims:** don't say the docs "forbid" it ([`facts.md`](../facts.md)).

## 4. Gaps / unverified
- Version in which GRAPH.COPY, constraints, UDFs, temporal types and GRAPH.MEMORY were introduced: the docs don't say.
- Why `latest` reported 4.22.1 on Oct 15 when the 6.0 notes say `latest` = 6.0. Not resolved.
- Whether FLEX UDFs come preloaded in the Docker image.
- Whether HarmonicCentrality and maxFlow exist on 6.0. The notes imply yes, because both shipped in May, before 4.20.7; not tested.
- The `cypher/procedures` table omits AStar, HarmonicCentrality, maxFlow and CCH; the docs are internally inconsistent.
- The falkordb-py 1.8.0 notes were read only as far as the first lines (CI/deps).
- Not tested on an engine: everything here comes from docs and release notes only.
