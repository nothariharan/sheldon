> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# Batch, Graph-RAG, and Emerging Memory Systems (Round 2)

**Claim prefix:** M3-
**Status:** ASSIGNMENT NOT COMPLETED — subagent interrupted before writing.

This file was assigned to a research subagent covering Cognee, LightRAG, Microsoft GraphRAG, and any newer OSS memory layers. The subagent was interrupted before it produced content. This placeholder exists so the gap is visible rather than silent.

**Open scope, not yet researched:**

- Cognee (`topoteretes/cognee`): Extract-Cognify-Load pipeline, supported graph backends including Redis/FalkorDB, and whether writes are real-time in-loop or batch ingestion. Round-1 claims (`research/01_EXISTING_MEMORY_LANDSCAPE.md`) are batch-heavy and use SQLite WAL locking, but these were not re-verified.
- LightRAG (`HKUDS/LightRAG`) and Microsoft GraphRAG (`microsoft/graphrag`): low/high-level retrieval, community summaries, offline-corpus assumption.
- Any newer OSS agent-memory layer discovered in 2025-2026. Nothing was searched; no such project is claimed to exist or not to exist here.
- MCP memory servers: how memory is exposed over MCP and whether the protocol has any primitive for agent-to-agent state sharing, locking, or coordination.

**Partially covered elsewhere:** the FalkorDB ecosystem integration list, Graphiti-on-FalkorDB and mem0-on-FalkorDB are covered in `v2_01_existing_memory_systems.md` and `v2_05_falkordb_technical.md` section 10.

## Coordination log

- 2026-10-15: assignment issued to a subagent; the subagent was interrupted before writing. Recorded as incomplete, with the open scope listed above rather than filled with unverified content.
