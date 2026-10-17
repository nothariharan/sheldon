> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# Existing Agent Memory Systems: Subagent Audit (Round 2)

**Claim prefix:** M1-  **Research date:** 2026-10-15
**Method:** Round-2 subagent attempts were interrupted before completing. This file is built from pages fetched directly by the main agent on this date, listed below, plus round-1 research that was already source-anchored. Every row in the Claims table has a fetched URL or is explicitly marked as carried from round 1.

**Sources fetched this pass:**
- https://docs.falkordb.com/agentic-memory/mem0.md
- https://docs.falkordb.com/agentic-memory/graphiti.md
- https://docs.falkordb.com/agentic-memory/index.md (index only)

**Sources NOT fetched this pass:** Mem0's own site/docs, Supermemory's docs, Letta's docs, LangGraph's docs, Cognee's docs, LightRAG's repo, Microsoft GraphRAG's repo. Claims below about those systems are carried from round 1 and marked as such. They are not falsified, but they also are not newly verified in round 2. Do not treat round-1-carried rows as freshly audited.

---

## Summary table

| System | Bi-temporal | Procedural | Graph-algorithm retrieval | Task leasing | Sandbox | Delta handoff | Decay | Tenant isolation | Source |
|---|---|---|---|---|---|---|---|---|---|
| Mem0 (default) | No | No | No | No | No | No | Partial | Partial (per-user scoping) | round 1 + FalkorDB docs page |
| Mem0 + mem0-falkordb plugin | No (in plugin docs) | No | Partial (PageRank available on the graph, not used by Mem0) | No | Not documented | Not documented | Partial | **Yes, native per-user graph** | fetched |
| Graphiti on FalkorDB | **Yes** | No | Partial (hybrid search documented, PageRank not in docs) | No | No | No | No | **Yes, graph_name per tenant** | fetched |
| Supermemory | No | No | No | No | No | No | Partial | Yes (containers) | round 1 only |
| Letta / MemGPT | No | Partial (archival/recall tiers) | No | No | No | No | No | Partial | round 1 only |
| LangGraph Store | No | No | No | No | No | No | No | Partial | round 1 only |
| Cognee | No | No | No | No | No | No | Partial | Partial | round 1 only |
| LightRAG | No | No | Partial (community/hierarchical) | No | No | No | Partial | Partial | round 1 only |
| Our build | Yes (target) | Yes (target) | Yes (target) | **Yes, via single-query atomicity** | **Yes, via GRAPH.COPY** | Yes (target) | Yes (target) | **Yes, native** | v2_05, v2_07 |

## 1. Mem0

### Documented architecture

Round 1 described Mem0 as a hybrid vector + key-value + knowledge-graph system with an ADD/UPDATE/DELETE/NONE decision step and destructive overwrites on update. That description was not re-verified against mem0's own docs this pass and should be re-checked before a submission cites it.

What IS newly verified this pass is Mem0's **FalkorDB integration**, which matters more for our pitch:

- The `mem0-falkordb` plugin (`github.com/FalkorDB/mem0-falkordb`, PyPI `mem0-falkordb`) adds FalkorDB as a graph store backend "without modifying any Mem0 source code". It uses runtime patching: `from mem0_falkordb import register; register()`.
- Config: `{"graph_store": {"provider": "falkordb", "config": {"host", "port", "database", "username", "password", "base_label"}}}`. Package `mem0ai` still installed separately.
- Per-user graph isolation: "Each user automatically gets their own isolated FalkorDB graph (e.g., `mem0_alice`, `mem0_bob`)." The `database` config key is a graph-name prefix; each user gets `{database}_{user_id}`.
- `m.delete_all(user_id='alice')` "simply drops the user graph".
- Search API: `m.search("what does alice like?", user_id="alice")`. History API: `m.history(memory_id=...)` returning `version` and `changed_at`.
- The docs page claims Mem0 supports "Memory evolution: Support for updates and conflict resolution" but documents no bi-temporal edge model. It describes "Mem0 automatically handles memory updates and conflict resolution" with `m.add("Alice now prefers sushi")` replacing prior preference — that is overwrite semantics, and the page does not describe retaining the prior value.

### Track-02 capability assessment

| Requirement | Yes/No/Partial | Evidence |
|---|---|---|
| Non-destructive / bi-temporal fact updates | **No** (as documented on this page) | FalkorDB docs page describes update as replacing preference; no valid_at/invalid_at interval model described |
| Procedural memory | No | Nothing on the page |
| Graph-algorithm retrieval | Partial | FalkorDB does expose `algo.pageRank`, but the Mem0 plugin docs describe only semantic search with vector embeddings; no algorithm invocation |
| Atomic multi-agent task leasing | No | Nothing on the page |
| Speculative sandboxing | No | Nothing on the page; plugin does not document use of GRAPH.COPY |
| Graph-delta handoffs | No | Nothing on the page |
| Decay / consolidation | Partial | Round-1 claim of "smart forgetting"; not confirmed on this page |
| Native per-tenant isolation | **Yes** | Verified: one graph per user, `mem0_{user_id}` |

**Pitch-relevant reading:** Mem0 on FalkorDB already proves the per-user-graph isolation pattern we want. Our differentiator is therefore NOT "we use graphs for memory" — that is taken. Our differentiator has to be what Mem0's plugin does not do: bi-temporal non-destructive update, procedural DAGs, atomic task leasing, GRAPH.COPY sandboxing, and graph-delta handoffs.

## 2. Graphiti on FalkorDB

### Documented architecture (fetched)

- "Graphiti is a Python framework for building temporally-aware, multi-tenant knowledge graphs designed for multi-agent AI systems with persistent memory."
- Install: `pip install graphiti-core[falkordb]`. Connect with `Graphiti(uri="falkor://localhost:6379")`. One-time `await graphiti.build_indices_and_constraints()`.
- Episodes are the unit of stored information: `await graphiti.add_episode(name=..., episode_body=..., episode_type=EpisodeType.text, reference_time=datetime(2024,3,15), source_description=...)`.
- Hybrid search: `graphiti.search(query=..., num_results=...)`, `graphiti.retrieve_nodes(query=...)`, `graphiti.retrieve_episodes(query=...)`.
- Temporal queries: `graphiti.search(query=..., reference_time=datetime(2024,3,1), ...)` — "Get the state of knowledge at a specific time".
- Multi-tenancy: "Create isolated graphs for different users or agents by specifying a unique `graph_name` parameter... Each graph is completely isolated, leveraging FalkorDB's native multi-graph support."
- Prerequisites: Python 3.10+, OpenAI API key for embeddings and LLM features.

### Important correction to round 1

Round 1 (`research/01_EXISTING_MEMORY_LANDSCAPE.md`) asserted Graphiti's bi-temporal edge model has four specific fields: `valid_at`, `invalid_at`, `created_at`, `expired_at`. **Those four field names did not appear on the FalkorDB docs page I fetched this pass.** The page confirms temporal awareness and `reference_time` on episodes and on search, but the exact property names must be verified from `help.getzep.com/graphiti/` before we cite them in a submission. Round 1's claim is plausible and likely correct, but it is UNVERIFIED in round 2.

Round 1 also asserted "Old edges are not deleted — they are stamped `invalid_at`." That specific mechanism was not confirmed on any page fetched this pass. Verify at https://help.getzep.com/graphiti/.

### Track-02 capability assessment

| Requirement | Yes/No/Partial | Evidence |
|---|---|---|
| Bi-temporal fact updates | **Partial/Yes-in-principle** | Temporally-aware documented, `reference_time` search verified; the specific `valid_at`/`invalid_at` edge model is UNVERIFIED from the fetched page |
| Procedural memory | No | Nothing on the page |
| Graph-algorithm retrieval | Partial | "hybrid search... Combine semantic search with graph traversal" verified as a claim; `algo.pageRank` is not referenced anywhere on the page |
| Atomic multi-agent task leasing | No | Nothing on the page; Graphiti has no task primitive |
| Speculative sandboxing | No | Nothing on the page; no GRAPH.COPY usage documented |
| Graph-delta handoffs | No | Nothing on the page |
| Decay / consolidation | No | Nothing on the page; round 1's "graph bloat, no auto-pruning" observation is consistent with the docs not mentioning any pruning |
| Native per-tenant isolation | **Yes** | Verified: `graph_name` per user/agent |

**Pitch-relevant reading:** Graphiti on FalkorDB is the closest prior art and will be the judge's comparison point. It gives us temporal episode memory and per-tenant graphs but not coordination. Its own docs page positions it as "memory for multi-agent AI systems" without describing any coordination primitive — which is precisely the gap our Track 02 build claims.

## 3. Systems carried from round 1, not re-verified this pass

These rows remain as round 1 wrote them. They are usable internally but must be re-audited against primary docs before appearing in a submission or a blog post.

- **Supermemory** (`supermemoryai/supermemory`): containers/namespaces, decay, MCP server, shallow graph layer. Not fetched this pass.
- **Letta / MemGPT** (`letta-ai/letta`, arXiv:2310.08560): core memory / recall memory / archival memory tiering, `core_memory_append`, `core_memory_replace`, `archival_memory_search`. Not fetched this pass.
- **LangGraph Store / BaseStore**: flat key-value persistent memory across threads, namespace semantics. Not fetched this pass.
- **Cognee** (`topoteretes/cognee`): Extract-Cognify-Load pipeline, pluggable backends including Redis. Not fetched this pass.
- **LightRAG** (`HKUDS/LightRAG`) and **Microsoft GraphRAG** (`microsoft/graphrag`): dual-level retrieval, community summaries, built for offline corpus RAG rather than in-loop agent memory. Not fetched this pass.

## What this means for our build

1. Per-user graph isolation via FalkorDB named graphs is **already taken** by both the `mem0-falkordb` plugin and Graphiti's `graph_name`. Our submission cannot claim it as novel.
2. Temporal memory via episodes + `reference_time` is **already taken** by Graphiti. We need a reason we are not just `graphiti-core[falkordb]` plus glue.
3. The genuinely unclaimed cluster, given the docs above: atomic multi-agent task leasing, speculative sandboxed execution via `GRAPH.COPY`, graph-delta handoffs between agents, and procedural memory as reusable action DAGs. None of the four appears on any page I fetched.
4. The strongest technical claim we can defend: FalkorDB's documented **serialized-write, per-graph, atomic-single-query** model lets a Cypher query be a task lease without external locking, and `GRAPH.COPY`'s documented **consistent-snapshot, index-and-constraint-copying** semantics lets a whole graph be a sandbox. Both are documented engine facts, not our inventions.
5. Framing guidance: say "Mem0-on-FalkorDB and Graphiti already give per-user graph isolation and temporal memory; what neither ships is coordination" rather than "nobody has done graph memory".

## Could not verify

- Graphiti's exact edge property names (`valid_at`, `invalid_at`, `created_at`, `expired_at`) — carried from round 1, not confirmed this pass.
- Mem0's own architecture docs (ADD/UPDATE/DELETE step, vector + KV + graph layers) — carried from round 1.
- Whether the `mem0-falkordb` plugin exposes or preserves any bi-temporal history on updates.
- Supermemory, Letta, LangGraph Store, Cognee, LightRAG, GraphRAG current feature state.
- Any 2025-2026 newer OSS memory layer (MemMachine, Memobase, etc.) — no discovery search completed this pass.

## Coordination log

- 2026-10-15 main agent. Round-2 subagent assignments for this file were interrupted; two subagents wrote only a header stub. This file is the salvage.
- Round-1 file `research/01_EXISTING_MEMORY_LANDSCAPE.md` left unmodified. Its claim about Graphiti's four bi-temporal field names is flagged above as needing re-verification rather than corrected.
- Open item for the next agent: fetch `https://help.getzep.com/graphiti/` (the Graphiti docs, not the FalkorDB page) and confirm or refute the `valid_at`/`invalid_at`/`expired_at` edge model. This is the single highest-value unverified claim in our pitch because our entire bi-temporal design claim rests on it.
