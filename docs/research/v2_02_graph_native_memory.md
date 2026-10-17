> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# Graph-Native Memory and the FalkorDB Ecosystem (Round 2)

**Claim prefix:** M2-  **Research date:** 2026-10-15
**Status:** PARTIAL — the assigned subagent was interrupted. This file contains only what the main agent verified from pages it fetched this pass. Open scope is listed at the bottom rather than filled with unverified content.

**Sources fetched this pass:**
- https://docs.falkordb.com/_llms/falkor-db.txt (integration and agentic-memory index)
- https://docs.falkordb.com/_llms/falkor-db/documentation.txt (documentation index)
- https://docs.falkordb.com/agentic-memory/graphiti.md
- https://docs.falkordb.com/agentic-memory/mem0.md
- https://github.com/getzep/graphiti (via `v2_09`)

---

## What the FalkorDB docs themselves list as agent-memory integrations

From the Agentic Memory section of the FalkorDB docs index:

> **Agentic Memory: Long-Term Graph Memory for AI Agents** — "Implement persistent, contextual memory for AI agents with FalkorDB using Graphiti, Cognee, and MCP servers for temporally-aware, multi-tenant knowledge graphs."

Four documented integration pages in that section:
1. **Graphiti** — "Dynamic Temporal Knowledge Graph Memory for AI Agents" — verified in depth in `v2_01` and `v2_09`.
2. **Cognee** — "Deterministic Agentic Memory with FalkorDB" — page exists and is linked from the docs index. **Page not fetched this pass.**
3. **Graphiti MCP Server** — "Run Graphiti MCP server with FalkorDB for persistent AI agent memory in Claude Desktop, Cursor IDE, and other MCP clients with temporally-aware knowledge graphs." **Page not fetched this pass.**
4. **Mem0** — "Personalized Agentic Memory Powered by FalkorDB" — verified in `v2_01`.

The hackathon marketing page also names GraphRAG-SDK, QueryWeaver, MCP, Graphiti, Cognee, LangChain, LlamaIndex. The full documented FalkorDB integration surface, from the docs index fetched this pass, is:

LangChain, LangGraph, LlamaIndex, AG2 (formerly AutoGen), AWS GraphRAG Toolkit, QueryWeaver (open-source Text2SQL over PostgreSQL/MySQL/Snowflake), Code-Graph (codebases as knowledge graphs), Graphify (unstructured text to knowledge graph), GraphRAG SDK (first-party), n8n, PyTorch Geometric, Snowflake, Spring Data (Java OGM), Apache Jena (RDF/SPARQL adapter), Kafka Connect sink, FalkorDB MCP Server (stdio and SSE transports, Docker Compose deploy).

## Is FalkorDB a backbone or an adapter, per integration?

| Integration | Relationship to FalkorDB | Evidence |
|---|---|---|
| **GraphRAG SDK** | First-party FalkorDB product; its own docs section on docs.falkordb.com. Publishes a vendor benchmark (71.48 on GraphRAG-Bench vs 55.39 for vector RAG with reranking) — **vendor-published, cite as such** | docs index |
| **Graphiti** | FalkorDB is one of several supported backends (Neo4j, FalkorDB, Amazon Neptune), with a documented `graphiti-core[falkordb]` install extra and a `falkor://` URI scheme. README states supported backend version "FalkorDB 1.1.2" | fetched |
| **Mem0** | FalkorDB is a plugin-provided graph store backend, `mem0-falkordb`, plus `mem0ai` installed separately | fetched |
| **Cognee** | Documented FalkorDB integration page exists | docs index only, not fetched |
| **LangChain / LangGraph / LlamaIndex / AG2 / AWS toolkit** | Framework adapters, each with its own docs page | docs index only, not fetched |
| **QueryWeaver** | A Text2SQL product that uses graph-powered schema understanding. Not an agent-memory system — do not cite it as one | docs index |

**Conclusion on this question:** FalkorDB is the backbone for GraphRAG SDK and for the memory-specific plugins (mem0-falkordb, Graphiti's `[falkordb]` extra), and an adapter target for the general frameworks. For our Track 02 pitch the two that matter are Graphiti and the mem0 plugin, both of which we have now verified in depth.

## Claims table

| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| M2-01 | FalkorDB documents an "Agentic Memory" section listing Graphiti, Cognee, and MCP servers for agent memory | docs.falkordb.com/_llms/falkor-db.txt | VERIFIED | |
| M2-02 | Graphiti supports FalkorDB as one backend among Neo4j, FalkorDB, Amazon Neptune; install extra `graphiti-core[falkordb]`; README states FalkorDB 1.1.2 | docs.falkordb.com/agentic-memory/graphiti.md + github.com/getzep/graphiti | VERIFIED | Also via v2_09 |
| M2-03 | mem0-falkordb plugin provides per-user graph isolation named `{database}_{user_id}` | docs.falkordb.com/agentic-memory/mem0.md | VERIFIED | Also v2_01 |
| M2-04 | Graphiti's bi-temporal edge fields are `valid_at`, `invalid_at`, `expired_at`, `created_at` | github.com/getzep/graphiti/graphiti_core/edges.py | VERIFIED | See v2_09 |
| M2-05 | GraphRAG SDK publishes 71.48 vs 55.39 on GraphRAG-Bench | docs.falkordb.com/graphrag/graphrag-accuracy-benchmark.md (index entry only) | VERIFIED as vendor-published | Page itself not fetched; treat as vendor claim |
| M2-06 | QueryWeaver is an agent-memory system | docs.falkordb.com/genai-tools/queryweaver.md (index entry) | FALSE framing | It is open-source Text2SQL for PostgreSQL/MySQL/Snowflake. Do not list it under agent memory |
| M2-07 | Cognee's graph schema, backends, and write latency characteristics | — | UNVERIFIED | Page not fetched |
| M2-08 | Any MCP primitive exists for agent-to-agent state sharing, locking, or coordination | — | UNVERIFIED | Not investigated this pass. This is the key open question for Track 02, because our whole coordination story is about shared state |
| M2-09 | Any 2025-2026 newer graph memory project beyond Graphiti, mem0, Cognee | — | UNVERIFIED | No discovery search run |

## What this means for our build

1. **FalkorDB's own docs already market "agentic memory"** using Graphiti, Cognee and MCP servers. We are entering a field the sponsor has already characterised, and the sponsor's own documentation is our best source for what the judges will consider table stakes.
2. **Graphiti + mem0 cover "memory persists" and "memory per tenant".** Our submission is judged on what those two do not do, which `v2_08` section F defines precisely.
3. **M8 (MCP as a coordination surface) is a genuine open question.** Whether the Model Context Protocol has any primitive for locking, leasing, or broadcasting state between agents is unverified. If it does, our coordination story changes. If it does not, "shared state between agents needs a graph primitive, not a chat protocol" becomes a stronger claim. This is the highest-value item to resolve in this file's scope.

## Open scope (assignment not completed)

- Cognee's graph schema, supported graph backends, and whether writes are real-time in-loop or batch ingestion.
- LightRAG and Microsoft GraphRAG: low/high-level retrieval, community summaries, offline-corpus assumption.
- **MCP memory servers and MCP coordination primitives** — the highest-value unexamined question here.
- Any newer OSS agent-memory layer from 2025-2026. Nothing searched; no claim made either way.

## Coordination log

- 2026-10-15: assigned to a subagent that was interrupted before writing content. This file was then written by the main agent from the pages listed above rather than left empty, so the ecosystem facts captured while fetching FalkorDB docs are not lost.
- Overlaps deliberately with `v2_01` (Graphiti, mem0) and `v2_05` section 10 (integration list). `v2_01` holds the deep per-system audit; `v2_09` holds the Graphiti source-code-level verification. This file holds the ecosystem-shape facts.
- Highest-value next step: investigate MCP for any state-sharing or locking primitive. Nothing else in this file's open scope changes the architecture.
