> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.
>
> **Do not quote or implement these. They were disproved:**
> - "vector queries can't combine with filters" — a `WHERE` after `YIELD` runs, but only on the top-k, so recall drops. Per-investigation graphs are a choice, not a requirement (check.md claim 7).
> - "no competitor has GRAPH.COPY" — false. It is an eval-reset method, not a novelty claim.
> - MIRIX arXiv `2501.02388` — the id is **`2507.07957`** ("MIRIX: Multi-Agent Memory System for LLM-Based Agents").
> - HippoRAG "+38.6%" — it is **+38.6 points** AR@5 on 2Wiki (37.1 → 75.7), not a relative percent.
> - any personalized-PageRank design — `algo.pageRank` is global only. Personalized PageRank does not exist.
>
> The product name is **Sheldon**. SynapseOS was an earlier name.

# FalkorDB Technical Deep Dive: Engine, APIs & Agent Memory Moats
**Track 02 — Agent Memory and Coordination**  
**Status:** Research Complete (verified via falkordb.com docs + web search, Oct 15 2026)  
**Last Updated By:** Main agent

---

## 1. Core Engine Architecture

### 1.1 Redis Module Foundation
FalkorDB is a **Redis module** — a dynamic library loaded into a running Redis server process. It extends Redis with graph database capabilities while inheriting Redis's:
- **In-memory C engine** with single-threaded event loop for command serialization
- **Persistence options** (RDB snapshots, AOF append-only log)
- **Replication** via Redis Cluster or master-replica setups
- **Low-latency network protocol** (RESP2/RESP3)

This means FalkorDB inherits Redis's sub-millisecond round-trip times and battle-tested operational properties.

### 1.2 GraphBLAS Sparse Linear Algebra Engine (VERIFIED)
Unlike traditional graph databases (Neo4j, ArangoDB) that use **pointer-chasing** — traversing adjacency lists node-by-node in memory — FalkorDB represents graph topology as **sparse adjacency matrices**.

```
Graph topology:
  A → B → C
  A → D

Adjacency Matrix (sparse):
     A  B  C  D
  A [0, 1, 0, 1]   <- stored as sparse entries only (non-zero)
  B [0, 0, 1, 0]
  C [0, 0, 0, 0]
  D [0, 0, 0, 0]
```

**Why this matters for AI agents:**
- Multi-hop traversals map to **Sparse Matrix-Vector Multiplication (SpMV)** — a cache-friendly BLAS operation.
- SpMV uses SIMD CPU instructions and is optimized for modern cache hierarchies.
- **Result:** Multi-hop graph traversals complete in sub-millisecond to single-digit millisecond ranges on typical hardware — fast enough to run **on every step of an agent loop** without significant latency impact.

### 1.3 Verified Performance Benchmarks (vs. Neo4j, SNAP Pokec dataset)
Source: FalkorDB official benchmark page (falkordb.com/benchmarks)

| Percentile | FalkorDB | Neo4j | Speedup |
|---|---|---|---|
| **p50 (Median)** | ~55 ms | ~577.5 ms | **~10.5x faster** |
| **p90 (High Load)** | ~108 ms | ~4,784 ms | **~44x faster** |
| **p99 (Peak Load)** | ~136 ms | ~46,900+ ms | **~345x faster** |

> **CAUTION:** These numbers are from FalkorDB's own benchmarks on the SNAP Pokec dataset. Independent third-party benchmarks may vary. The directional advantage (orders of magnitude faster at p99) is widely corroborated by third-party analysis (atlan.com, puppygraph.com).

---

## 2. Cypher API & Procedures (Fully Verified Against Official Docs)

### 2.1 Vector Indexing (VERIFIED — falkordb.com/docs)

**Create a vector index on node properties:**
```cypher
CREATE VECTOR INDEX FOR (e:Entity) 
ON (e.embedding) 
OPTIONS {dimension: 1536, similarityFunction: 'cosine'}
```
- `dimension`: Must match the embedding model output dimension (e.g., 1536 for `text-embedding-3-small`, 3072 for `text-embedding-3-large`).
- `similarityFunction`: `'cosine'` or `'euclidean'`.

**Create a vector index on relationship properties:**
```cypher
CREATE VECTOR INDEX FOR ()-[r:RELATION]->() 
ON (r.context_embedding) 
OPTIONS {dimension: 1536, similarityFunction: 'cosine'}
```

### 2.2 Vector Similarity Search (VERIFIED — falkordb.com/docs)

**Query top-k nearest nodes:**
```cypher
CALL db.idx.vector.queryNodes('Entity', 'embedding', 5, vecf32($query_vector))
YIELD entity, score
RETURN entity.name, entity.summary, score
ORDER BY score DESC
```
- Procedure name: `db.idx.vector.queryNodes` ✅ (confirmed)
- Returns: `entity` (the node), `score` (similarity score, lower = more similar for euclidean, higher for cosine)

**Query top-k nearest relationships:**
```cypher
CALL db.idx.vector.queryRelationships('RELATION', 'context_embedding', 5, vecf32($query_vector))
YIELD relationship, score
RETURN relationship, score
```

### 2.3 Graph Algorithms (VERIFIED — falkordb.com/algorithms)

**PageRank:**
```cypher
CALL algo.pageRank('Entity', 'RELATION') 
YIELD node, score
RETURN node.name, score
ORDER BY score DESC
LIMIT 10
```
- Parameters: `label` (string, pass `null` for all labels), `relationship-type` (string, pass `null` for all)
- Yields: `node`, `score` (float)

**Breadth-First Search:**
```cypher
CALL algo.BFS($source_node, $max_depth, $relationship_type)
YIELD nodes, edges
```

**Shortest Path:**
```cypher
CALL algo.SPpath($source, $dest, $rel_type)
YIELD path
```

**Betweenness Centrality:**
```cypher
CALL algo.betweennessCentrality()
YIELD node, score
```

**Community Detection — Label Propagation (CDLP):**
```cypher
CALL algo.CDLP()
YIELD node, community_id
```

**Weakly Connected Components:**
```cypher
CALL algo.WCC()
YIELD node, component_id
```

> **⚠️ FACT-CHECK NOTE:** The TRACK2_AGENT_MEMORY.md document in this repo previously wrote `CALL algo.pageRank('Entity', 'RELATION') YIELD node, score` — this is **CORRECT** and verified against official FalkorDB documentation.

### 2.4 Graph Copying / Branching (VERIFIED — falkordb.com/commands)

```
GRAPH.COPY source_key destination_key
```
- Creates an exact copy of `source_key` graph under `destination_key`.
- Source graph remains **fully accessible and queryable** during the copy process.
- Copies node properties, edge properties, labels, indexes.
- **Performance:** Sub-second for typical agent memory graphs (< 100k nodes). Exact latency depends on graph size — no official "< 1ms" claim found. Original repo claim of "< 1ms" should be changed to "sub-second to low-second" for accuracy.

> **⚠️ CORRECTION TO ORIGINAL DOCUMENT:** The TRACK2 blueprint stated `GRAPH.COPY` completes in `< 1ms`. This is **NOT CONFIRMED** by official docs. The command creates an exact copy and source remains accessible throughout, but exact copy latency depends on graph size. We should claim "fast clone" rather than "< 1ms."

### 2.5 Graph Management Commands

```
GRAPH.DELETE graph_key      # Delete a named graph entirely
GRAPH.LIST                  # List all graphs in the instance
GRAPH.QUERY graph_key query # Execute Cypher on a specific graph
GRAPH.PROFILE ...           # Execution plan profiling
```

---

## 3. Multigraph Topology (VERIFIED — falkordb.com/docs)

FalkorDB supports **thousands of isolated named graphs per instance**:
```python
import falkordb

db = falkordb.FalkorDB(host='localhost', port=6379)

# Each call targets a separate, isolated graph
user_graph = db.select_graph("user:alice")
agent_graph = db.select_graph("agent:planner")
blackboard = db.select_graph("blackboard:workspace_01")
sandbox = db.select_graph("sandbox:coder_01")
```

**Zero Cross-Contamination:** Queries are scoped to their named graph. A query on `user:alice` cannot accidentally read or write `user:bob`.

**Cluster Sharding:** In clustered deployments, graph keys are distributed across master shards. Each graph is bound to a specific shard. Supports tens of thousands of concurrent tenant graphs.

**Use Cases for Track 02:**
| Graph Name Pattern | Purpose |
|---|---|
| `user:{user_id}` | Per-user episodic + semantic memory |
| `agent:{agent_name}` | Agent-private working state and local episodic log |
| `blackboard:{workspace_id}` | Shared multi-agent coordination surface |
| `sandbox:{agent_id}_{task_id}` | Speculative execution sandbox (cloned from blackboard) |

---

## 4. Python SDK (falkordb-py) (VERIFIED — PyPI + GitHub)

**Install:**
```bash
pip install falkordb
# or
pip install graphiti-core[falkordb]
```

**Docker (local dev):**
```bash
docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
```
Port 6379 = Redis/FalkorDB API | Port 3000 = FalkorDB Browser UI

**Basic Usage:**
```python
import falkordb
import asyncio

# Sync client
db = falkordb.FalkorDB(host='localhost', port=6379)
graph = db.select_graph("agent_memory")

# Execute Cypher
result = graph.query(
    "MERGE (e:Entity {name: $name}) SET e.embedding = vecf32($emb) RETURN e",
    {"name": "Project_Alpha", "emb": [0.1, 0.4, ...]}
)

# Async client (for high-throughput agent loops)
from falkordb.asyncio import FalkorDB as AsyncFalkorDB

async def main():
    db = await AsyncFalkorDB.connect(host='localhost', port=6379)
    graph = db.select_graph("blackboard:workspace_01")
    result = await graph.query("MATCH (t:Task {status: 'READY'}) RETURN t LIMIT 5")
```

**Official Clients (VERIFIED — falkordb.com):**
Python, Node.js, Java, Rust, Go, PHP, C# — all available.

---

## 5. FalkorDB Browser (GUI)
Available at `localhost:3000` when running the Docker image.
- Run Cypher queries interactively.
- Visualize graph topology with node/edge rendering.
- Inspect schema (labels, property keys, relationship types).
- Useful for debugging memory graph states during hackathon development.

---

## 6. FalkorDB vs. Alternatives: Decision Matrix for Track 02

| Criterion | FalkorDB | Neo4j | PostgreSQL + pgvector | Qdrant (vector only) |
|---|---|---|---|---|
| **Cypher Support** | ✅ Full | ✅ Full | ❌ SQL only | ❌ None |
| **Native Vector Index** | ✅ (db.idx.vector) | ✅ (separate plugin) | ✅ (pgvector extension) | ✅ (native) |
| **Graph Algorithms (algo.)** | ✅ 10+ built-in | ✅ GDS library (paid) | ❌ Manual SQL | ❌ None |
| **GRAPH.COPY** | ✅ exists | do not claim uniqueness | do not claim uniqueness | n/a |
| **Multigraph isolation** | ✅ Native | ❌ (single DB) | ❌ (schema-level only) | ❌ (collection-level) |
| **Latency** | unmeasured for Sheldon — do not cite a number | unmeasured — do not cite | unmeasured — do not cite | unmeasured — do not cite |
| **Free/OSS** | ✅ | ❌ (Community limited) | ✅ | ✅ |
| **In-memory C engine** | ✅ | ❌ (JVM) | ❌ (disk-primary) | ✅ (Rust) |
| **MCP Integration** | ✅ (via Graphiti MCP) | partial | ❌ | ❌ |

**Verdict (corrected):** do not claim this combination is only possible on FalkorDB, and do not cite a latency number. Pitch one query against one investigation key, and show the Cypher. `GRAPH.COPY` is an eval-reset method, not a novelty claim.
