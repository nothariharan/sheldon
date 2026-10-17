> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# Existing Agent Memory Landscape: Full Audit
**Track 02 — Agent Memory and Coordination**  
**Status:** Research Complete (verified via web search, Oct 15 2026)  
**Last Updated By:** Main agent (after subagent rate-limit failure)

---

## Part I: Flat & Hybrid Vector-Based Systems

### 1. Mem0 (YC S24)
**GitHub:** `mem0ai/mem0` | **Website:** mem0.ai

#### Architecture
Mem0 implements a **three-layer hybrid memory system**:
- **Vector Layer:** Embeddings stored in external vector databases (Pinecone, Qdrant, Weaviate). Text chunks indexed by semantic similarity. BM25 keyword matching runs in parallel for exact-token retrieval.
- **Key-Value Layer:** Fast property lookups for user metadata and session flags.
- **Knowledge Graph Layer (native, auto-schema):** Entities are extracted as nodes (`Alice [Person]`). Relations become typed edges (`(Alice)--[LIVES_IN]-->(San Francisco)`). No manual schema required — LLM generates it dynamically.

#### Memory Lifecycle
1. **Extraction Phase:** Incoming messages pass through LLM Entity Extractor + Relations Generator. Output: structured graph triples + semantic chunks.
2. **Evaluation Phase:** Top-k semantically similar memories retrieved. LLM decides: `ADD | UPDATE | DELETE | NONE`.
3. **Commit Phase:** Graph and vector stores updated.

#### Verified Critical Limitations
| Limitation | Detail |
|---|---|
| **Destructive Overwrites** | Hard-overwrites or purges old facts on `UPDATE`/`DELETE`. No temporal versioning — cannot query "what did the agent believe about Alice's location last Tuesday?" |
| **Bi-Temporal Gap** | No `valid_at` / `invalid_at` intervals on edges. Historical graph states are unrecoverable after updates. |
| **No Multi-Agent Coordination** | Memory is per-user/session. No shared blackboard, atomic task leasing, or state handoffs for parallel agents. |
| **LLM in Hot Write Path** | Every write triggers an LLM call for conflict detection. High-frequency agent loops (>5 writes/sec) cause significant latency and token cost. |
| **Vector Drift Under Concept Shift** | If a project name is repurposed, vector cosine similarity surfaces stale semantic matches. |

---

### 2. Supermemory (supermemoryai/supermemory)
**GitHub:** `supermemoryai/supermemory`

#### Architecture
- **Ingestion Pipeline:** Processes PDFs, code (AST-aware chunking), audio/OCR, Gmail, Notion, GitHub into chunks.
- **Semantic Understanding Graph:** Entities grouped inside scoped namespaces (containers). Distinguishes stable facts from dynamic context.
- **Hybrid Retrieval (~50ms):** Combines vector similarity + structured memory fetch.
- **Smart Forgetting/Decay:** Low-signal memories auto-discarded; frequently-accessed ones reinforced; contradictions overwrite.
- **MCP Server:** Compatible with Claude Desktop, Cursor, Codex, Windsurf for cross-tool memory sharing.

#### Verified Critical Limitations
| Limitation | Detail |
|---|---|
| **Shallow Graph Layer** | The "semantic understanding graph" is a named-entity grouping/namespacing layer, not a full property graph with typed multi-hop traversal or PageRank. |
| **No Bi-Temporal Validity** | Contradictions trigger overwrite, not temporal invalidation with audit history. |
| **No Procedural Memory** | Cannot represent or re-execute reusable action DAGs. Every session re-plans. |
| **No Multi-Agent Coordination** | No atomic task leasing, no `GRAPH.COPY` sandboxing, no graph-delta handoffs. |

---

### 3. Letta / MemGPT (Packer et al., UC Berkeley)
**Paper:** arXiv:2310.08560  
**GitHub:** `letta-ai/letta`

#### Architecture: OS Memory Paging
| Tier | Analog | Implementation |
|---|---|---|
| **Core Memory** | CPU RAM | Editable blocks in active LLM context (`persona`, `human`). Agent uses `core_memory_append`, `core_memory_replace`. |
| **Recall Memory** | Page Cache | Chronological episodic history searchable via `conversation_search`. |
| **Archival Memory** | Hard Disk | Long-term vector store (LanceDB / SQLite). Agent uses `archival_memory_search`, `archival_memory_insert`. |

#### Verified Critical Limitations
| Limitation | Detail |
|---|---|
| **Token Budget Pressure** | Core memory competes with system prompts and tool definitions. Over-sized core blocks leave insufficient room for conversation. |
| **Agent Self-Editing Errors** | LLM can probabilistically overwrite critical instructions, hallucinate edits, or loop on redundant updates to its own memory blocks. |
| **Flat Archival Search** | Archival memory is a plain vector store. Fails at: temporal sequencing, exact ID lookups, multi-hop relational reasoning across linked entities. |
| **Multi-turn Latency Cascade** | One user question may trigger: `archival_memory_search` → tool returns → agent processes → heartbeat → agent replies. High time-to-first-token. |
| **No Graph Topology** | Entities in archival memory are unlinked. Multi-hop reasoning (Person A → Project B → Decision C) requires full LLM re-synthesis from flat text chunks. |

---

### 4. LangGraph Store
**GitHub:** `langchain-ai/langgraph`

#### Architecture
Key-value persistence layer for agent state. State is a typed `TypedDict` serialized to SQLite or PostgreSQL. "Store" provides cross-thread flat key-value memory.

#### Verified Critical Limitations
- **Flat Key-Value Semantics:** No graph topology. Relations must be modeled at application layer.
- **No Multi-Hop Reasoning:** Requires iterating keys — no graph traversal query.
- **No Atomic Task Leasing:** Concurrent agent claims require external locking (Redis `SETNX`).
- **No Temporal Validity:** State overwrites are destructive.

---

## Part II: Graph-Native Memory Architectures

### 5. Zep / Graphiti (temporal knowledge graph on FalkorDB)
**GitHub:** `getzep/graphiti`  
**Install:** `pip install graphiti-core[falkordb]`

#### Architecture
Builds a **temporally-aware knowledge graph** from conversational episodes.

**Bi-Temporal Edge Model (VERIFIED):**
- `valid_at`: When the fact became true in the real world (LLM-extracted from text).
- `invalid_at`: When the fact stopped being true (`null` = currently active).
- `created_at`: When the system ingested the data.
- `expired_at`: When a contradiction was detected.

Old edges are **not deleted** — they are stamped `invalid_at`. New edge created. Active queries filter `WHERE r.invalid_at IS NULL`.

**Multi-Tenancy:** `group_id` parameter scopes all nodes, edges, and episodes. Queries cannot cross group boundaries.

**FalkorDB Integration:** FalkorDB is the primary/default graph backend for Graphiti. Redis-based, GraphBLAS engine.

**MCP Server:** Ships with an MCP server for LLM client integration.

#### Verified Limitations
| Limitation | Detail |
|---|---|
| **LLM Extraction Overhead Per Episode** | Each episode ingestion triggers LLM call for entity/relation/temporal extraction. Not suitable for unbuffered high-frequency writes without async queue. |
| **Natural Language Temporal Ambiguity** | "Last Tuesday," "next month" depend on LLM parse context. Misparse → incorrect `valid_at` boundary. |
| **Graph Bloat (No Auto-Pruning)** | Facts accumulate indefinitely (stamped `invalid_at` but never deleted). Long-running graphs require explicit pruning strategies. |
| **No Procedural Memory** | No mechanism for reusable action DAGs / skill templates. |
| **No Native Multi-Agent Blackboard** | No atomic task leasing, no speculative `GRAPH.COPY` sandboxing, no graph-delta handoffs. |

---

### 6. Cognee (ECL Pipeline)
**GitHub:** `topoteretes/cognee`

#### Architecture: Extract → Cognify → Load
1. **Extract (E):** 38+ formats. Content hashing for deduplication. Scoped datasets.
2. **Cognify (C):** Document classification → text chunking → graph element extraction (LLM/GLiNER) → summarization → vector embedding generation.
3. **Load (L):** Pluggable backends (SQLite, PostgreSQL, Neo4j, LanceDB, Qdrant, Weaviate, Redis).

#### Verified Critical Limitations
| Limitation | Detail |
|---|---|
| **Batch-Heavy, Not Real-Time** | Designed for offline/scheduled ingestion. Cannot support high-frequency in-loop agent writes. |
| **Database Locking** | SQLite WAL triggers `database is locked` errors under concurrent `data_per_batch` settings. |
| **LLM Rate-Limit Bottleneck** | Graph extraction is bounded by LLM API limits. Default ~2000 `chunks_per_batch` saturates quotas on large corpora. |
| **No Dynamic Runtime Self-Modification** | Agent cannot atomically write a new fact and immediately query it within the same planning loop. |

---

### 7. LightRAG (Peking University/HKUDS)
**GitHub:** `HKUDS/LightRAG`

#### Architecture
Dual-level graph retrieval: low-level (specific entity/relation) + high-level (abstract community summaries). Hybrid mode combines both.

#### Limitations Relative to Track 02
- Designed for offline GraphRAG over static corpora. Not for real-time agent memory ingestion.
- No bi-temporal validity, no multi-agent coordination, no procedural memory.

---

## Summary Gap Matrix

| Capability Required by Track 02 | Mem0 | Supermemory | Letta | Graphiti | Cognee | LightRAG |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Bi-Temporal validity (non-destructive update) | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Procedural memory (reusable action DAGs) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PPR/Graph-algorithm retrieval | ❌ | ❌ | ❌ | ❌ | ❌ | partial |
| Multi-agent atomic task leasing | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Speculative sandboxing (GRAPH.COPY) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Graph-delta agent handoffs | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Memory decay & sleep consolidation | partial | partial | ❌ | ❌ | ❌ | ❌ |
| Per-tenant isolated graphs (native) | partial | ✅ | ❌ | ✅ | partial | ❌ |

**Conclusion (VERIFIED):** No single existing system covers all Track 02 requirements simultaneously. This gap is real, documented, and winnable.
