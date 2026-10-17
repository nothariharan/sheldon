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

---
date: 2026-10-14
type: architecture-spec
tags:
  - falkordb
  - graph-databases
  - graphblas
  - redis
  - linear-algebra
  - performance
ai-first: true
---

# FalkorDB: Architectural Deep Dive, Internals & Constraints

> A comprehensive technical reference on FalkorDB's execution engine, mathematical graph representation, strengths, and hidden failure modes.

---

## 1. Engine Heritage & Lineage

FalkorDB is the direct spiritual and architectural successor to **RedisGraph**, engineered by its original creators: **Guy Korland** (former CTO of Redis Labs) and **Roi Lipman** (author of RedisGraph). When Redis Ltd shifted its corporate licensing and deprecated RedisGraph in 2023, the core authors fork-migrated the engine into an independent company (FalkorDB Inc.), optimizing it specifically as the **low-latency context layer for AI agent loops**.

---

## 2. Core Engine: Sparse Linear Algebra & GraphBLAS

Traditional graph databases (Neo4j, Memgraph, Amazon Neptune) implement **labeled property graph engines based on physical memory pointer-chasing**:
* Nodes and edges exist as discrete C++ heap objects.
* A multi-hop query `(A)->(B)->(C)->(D)` requires the CPU to dereference pointers jumping across physical RAM addresses.
* **The Consequence:** Modern CPUs spend hundreds of clock cycles stalled on L1/L2/L3 cache misses.

### The GraphBLAS Breakthrough
FalkorDB completely replaces physical pointer-chasing with **algebraic graph theory** powered by **SuiteSparse:GraphBLAS** (authored by Dr. Tim Davis, Texas A&M):

1. **Adjacency Representation as Sparse Matrices:**
   A directed relationship of type $R$ between $N$ nodes is represented as an adjacency matrix:
   $$A_R \in \{0, 1\}^{N \times N}$$
   Stored using **Compressed Sparse Column (CSC)** or **Compressed Sparse Row (CSR)** formats, meaning only active edges consume memory.

2. **Graph Traversal as Matrix-Vector Multiplication (SpMV):**
   Finding all immediate neighbors reachable from an active set of frontier nodes (represented as a sparse indicator vector $v \in \{0, 1\}^N$) across edge type $R$ is formulated as:
   $$v_{\text{next}}^T = v^T \cdot A_R$$
   Over the boolean semiring $(\lor, \land)$.

3. **Multi-Hop Traversal as Matrix-Matrix Multiplication (SpGEMM):**
   Traversing a two-hop path across relationships $R_1$ and $R_2$ is computed as the product of two sparse matrices:
   $$A_{R_1 \circ R_2} = A_{R_1} \cdot A_{R_2}$$

4. **Hardware SIMD Vectorization:**
   Because traversals are matrix operations, the CPU utilizes **AVX-512 and SSE SIMD vector registers**. Traversals operate on cache-aligned contiguous memory blocks, executing multi-hop queries in **microseconds** rather than milliseconds.

```
       POINTER CHASING (Neo4j) vs LINEAR ALGEBRA (FalkorDB)

  [Node A] ──ptr──► [Node B] ──ptr──► [Node C]
  (CPU Cache Misses: Jumping across fragmented RAM)

                      vs.

  [ 0 1 0 0 ]   [ 0 ]     [ 1 ]
  [ 0 0 1 0 ] · [ 1 ]  =  [ 0 ]   <-- Hardware Vectorized SpMV
  [ 0 0 0 1 ]   [ 0 ]     [ 0 ]       (AVX-512 in < 50 microseconds)
  [ 0 0 0 0 ]   [ 0 ]     [ 0 ]
```

---

## 3. Storage Substrate & Protocols

* **Redis Native Module:** FalkorDB runs as a native C dynamic module inside the Redis process.
* **Dual Protocols:**
  1. **RESP (Redis Serialization Protocol):** Allows querying via standard Redis clients across Python, Node.js, Go, Rust, and Java using commands like `GRAPH.QUERY`, `GRAPH.RO_QUERY`, `GRAPH.COPY`, `GRAPH.DELETE`.
  2. **Bolt Protocol:** Emulates Neo4j's Bolt binary wire protocol, enabling interoperability with existing Cypher toolchains.
* **Persistence:** Leverages Redis’s battle-tested persistence guarantees:
  - **RDB (Snapshotting):** Periodic point-in-time binary dumps to disk.
  - **AOF (Append-Only File):** Log of all mutation commands with `fsync=everysec` for near-zero data loss.

---

## 4. The Multigraph Architecture (Key Isolation)

In conventional graph platforms, creating isolated graphs for different tenants requires deploying multiple server clusters or complex namespace configurations.

In FalkorDB, **each graph is simply a Redis key**:
```bash
# Graph for Tenant Alpha
GRAPH.QUERY tenant_alpha "CREATE (:User {name: 'Alice'})"

# Graph for Tenant Beta (completely isolated in memory)
GRAPH.QUERY tenant_beta "CREATE (:User {name: 'Bob'})"

# Zero-Copy In-Memory Clone for Simulation
GRAPH.COPY tenant_alpha tenant_alpha_sandbox
```

### Architectural Implications:
* **Massive Multi-Tenancy:** A single FalkorDB instance can host **10,000+ distinct graphs** with zero provisioning lag.
* **No Tenant Cross-Talk:** Because each graph is an independent set of GraphBLAS matrices, queries on `tenant_alpha` cannot leak into or lock `tenant_beta`.

---

## 5. Native Vector Indexing & Hybrid Search

FalkorDB natively integrates **HNSW (Hierarchical Navigable Small World)** vector indexing directly into the graph engine:

```cypher
// 1. Create HNSW Vector Index on Entity Node Embeddings
CREATE VECTOR INDEX FOR (e:Entity) 
ON (e.embedding) 
OPTIONS {
    dimension: 1536, 
    similarityFunction: 'cosine', 
    M: 32, 
    efConstruction: 200
};

// 2. Hybrid Search (Vector Seed -> GraphBLAS 2-Hop Traversal)
CALL db.idx.vector.queryNodes('Entity', 'embedding', 5, vecf32($query_vector))
YIELD node AS seed, score
MATCH (seed)-[:WORKED_ON]->(p:Project)-[:DEPENDS_ON]->(s:System)
RETURN seed.name, p.title, s.name, score
ORDER BY score DESC;
```
* **Why this matters for agents:** It executes semantic similarity search and structural graph expansion in a **single engine call**, removing the need for a separate vector database (e.g., Pinecone/Qdrant) alongside the graph.

---

## 6. Built-in Graph Algorithms

FalkorDB provides compiled C implementations of classical graph algorithms directly callable in openCypher:

| Algorithm | Cypher Procedure | Mechanism | Optimal Agent Use Case |
|---|---|---|---|
| **PageRank (global only)** | `CALL algo.pageRank('Label', 'TYPE')` | SpMV Power Iteration | Not personalized. Personalized PageRank does not exist. Do not use this for HippoRAG-style seeding. |
| **Betweenness Centrality** | `CALL algo.betweenness()` | Brandes Algorithm | **Choke Point Discovery:** Finding critical dependencies or security vulnerabilities. |
| **Shortest Path** | `CALL algo.SPpaths(src, dst)` | Dijkstra / BFS | **Attack Path Discovery & Invariance Testing.** |
| **Weakly Connected Components** | `CALL algo.wcc()` | Transitive Closure | **Security Zoning & Cluster Discovery:** Proving isolated subgraphs have zero links. |

---

## 7. Hidden Constraints & Architectural Pitfalls

Understanding what FalkorDB is **bad** at is critical to prevent disqualifying bugs during the hackathon:

### ⚠️ Pitfall 1: The RAM Bloat Hazard (Not a Blob Store)
* **The Reality:** FalkorDB stores all active graph data in **RAM**.
* **The Trap:** If an agent dumps full 5,000-word Notion documents, raw PDF text, or high-volume Slack JSON blobs into node properties, Redis memory usage skyrockets into gigabytes. Furthermore, large strings inside node property tables degrade CPU cache-line packing.
* **The Rule:** Implement the **Two-Tier Storage Architecture**:
  - Store full raw texts in SQLite, MinIO, or disk files.
  - Store strictly canonical IDs, scalar timestamps, status flags, and `source_uri` pointers in FalkorDB.

### ⚠️ Pitfall 2: Single-Graph Write Contention
* **The Reality:** Redis is single-threaded at its core event-loop level. While GraphBLAS algorithms parallelize read queries over multiple threads, **mutating a specific graph key acquires a write lock on that graph**.
* **The Trap:** If 10 parallel agent workers simultaneously bombard the **same graph key** with dense `MERGE` and `CREATE` statements, operations serialize, creating request timeouts.
* **The Solution:** Use **Multigraph Partitioning**: each agent writes to its private scratchpad graph key (`agent:worker_01`), and a coordinator merges consolidated graph deltas into the master graph in batched transactions.

### ⚠️ Pitfall 3: Dynamic Edge Property Updates
* **The Reality:** Modifying edge attributes frequently requires GraphBLAS to update auxiliary property matrices.
* **The Trap:** Dense, high-frequency updates on relationship properties are computationally more expensive than updating static node properties.
* **The Solution:** Prefer modeling high-frequency state changes as discrete nodes (`:Event`, `:Claim`, `:Episode`) with immutable edges rather than constantly overwriting properties on a single edge.

---
*Reference specification compiled for FalkorDB v0.4+ / Redis 7.2+.*
