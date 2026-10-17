> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# SUBAGENT COORDINATION LEDGER — Track 02 (Agent Memory & Coordination)

**Hackathon:** Graph Hacks: Give Your AI Agents Real Context (WeMakeDevs × FalkorDB), Oct 15–18 2026
**Track:** 02 — Agent Memory and Coordination (memory persists, updates over time, shared between agents)
**Repo dir:** `C:\Users\HARIHARAN\Desktop\SheldonAI`
**Round:** 2 (subagent-driven research, fresh)

## ROUND 2 OUTCOME (final, 2026-10-15)

Seven subagent launches were attempted. **Two completed** (A4 on benchmarks; the narrow critical-claim verifier on CoALA + Graphiti). The rest were interrupted before producing content. The main agent then wrote the remaining files from pages it fetched directly. Every claim marked VERIFIED in a `v2_*` file has a fetched URL; nothing is recalled from memory. See `v2_08_verification_audit.md` for what that does and does not guarantee.

Completed by subagents:
- `v2_04_benchmarks_and_evaluation.md` — subagent A4, 17 claims, all arXiv IDs re-verified, caught 3 of its own wrong ID guesses.
- `v2_09_critical_claim_verification.md` — both claims CONFIRMED to source code level.

Written by the main agent after subagent interruption:
- `v2_01`, `v2_02` (salvaged), `v2_05`, `v2_06`, `v2_07`, `v2_08`, `v2_03` (placeholder with open scope).

Not completed: `v2_03` (Cognee / LightRAG / GraphRAG / newer OSS) — open scope listed inside the file.

---

## RULES FOR EVERY SUBAGENT (hard)

1. **Never invent a source.** Every claim must carry a URL you actually fetched this run. If you could not fetch it, mark it `UNVERIFIED` and say what you tried.
2. **No exaggeration.** Prefer "10–30x cheaper per IRCoT baseline in paper Table X" over "dominates competitors". Numbers must be traceable to a line in a source.
3. **Numbers are the enemy.** arXiv IDs, benchmark percentages, latency figures, SDK syntax, and Cypher commands must be copied from the fetched page, not recalled. If a number differs between sources, record both.
4. **Write your own file.** Do not edit another agent's file. Do not edit the round-1 `research/01..05` files. You write exactly one `research/v2_*.md` file listed in the assignment table below.
5. **Append your coordination entry** at the bottom of your own file (never lock-step edit a shared file).
6. **One task, returned in your final message:** path written, claims count, verified vs unverified count, top 3 findings, anything you could not confirm.

---

## ASSIGNMENTS

| Agent | ID | File to write | Claim prefix | Scope |
|---|---|---|---|---|
| A1 | `A1` | `research/v2_01_existing_memory_systems.md` | `M1-` | Mem0, Supermemory, Letta/MemGPT, LangGraph Store, Cognee, LightRAG, + any newer OSS memory layers (2025–2026). Feature-by-feature audit against the Track 02 brief. |
| A2 | `A2` | `research/v2_02_graph_native_memory.md` | `M2-` | Zep/Graphiti (incl. FalkorDB backend), Cognee on FalkorDB/Neo4j, LightRAG, GraphRAG-SDK / QueryWeaver, MCP-based memory servers, Microsoft GraphRAG. What is FalkorDB-native vs ported. |
| A3 | `A3` | `research/v2_03_academic_foundations.md` | `M3-` | CoALA, Generative Agents, MemoryBank, A-MEM, Reflexion, Voyager, ExpeL, HippoRAG 1/2, AriGraph. Exact arXiv IDs, author lists, institutions, venues, and the ONE mechanism from each we can defend in a pitch. |
| A4 | `A4` | `research/v2_04_benchmarks_and_evaluation.md` | `M4-` | LongMemEval, LoCoMo, MemBench, plus any 2025–2026 agent-memory evals. What each measures, dataset size, metric names, baseline numbers, and how a 48-hour hackathon build could be honestly evaluated (nobody has time for full LongMemEval). |
| A5 | `A5` | `research/v2_05_falkordb_technical.md` | `M5-` | FalkorDB docs as ground truth: Cypher/procedure syntax (`algo.*`, `db.idx.vector.*`, `db.labels`, `GRAPH.*`), multigraph/tenant isolation, SDK surface (Python/Node), official benchmark numbers, deployment, limits. Quote commands verbatim. |
| A6 | `A6` | `research/v2_06_multi_agent_coordination.md` | `M6-` | Blackboard architecture, atomic task leasing, speculative execution / sandboxing, graph-delta handoffs, and what LangGraph / AutoGen / CrewAI / OpenAI Swarm actually offer for shared state today (and where they break). |
| A7 | `A7` | `research/v2_07_bleeding_edge_and_signals.md` | `M7-` | Recent 2025–2026 signals: agentic-memory research (MemAgent, G-Memory, memory-as-graph), HN / arXiv / lab blog activity on graph-backed agent memory, and FalkorDB-specific ecosystem/news. Trends and what judges will have seen. |
| V1 | `V1` | `research/v2_08_verification_audit.md` | `V-` | Runs LAST. Audits every claim ID from A1–A7 by re-fetching sources. Verdict per claim: VERIFIED / CORRECTED / UNVERIFIED / FALSE. |

---

## FILE FORMAT (all research agents)

```markdown
# <Title>
**Agent:** A<n> | **Claim prefix:** M<n>- | **Research date:** 2026-10-15
**Method:** search terms + pages actually fetched
**Sources fetched:** <url, url, ...>

## Claims
| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| M1-01 | ... | https://... | VERIFIED | ... |

## Synthesis (what this means for our build)
## Open questions / could not verify
## Coordination log
- 2026-10-15 A<n>: wrote this file. N claims (V/U). Blocked on: ...
```

## VERIFIER (V1) FORMAT

Per claim: `| Claim ID | Original claim | Re-fetched source | Verdict | Correction |`
Plus a final section: **integrity table** (per file: claims, verified, corrected, unverified) and **list of every claim that must be softened or deleted before it goes in a submission.**

---

## CONFLICT RULES

- Two agents may research overlapping systems. Overlap is wanted: disagreement between two fetched sources is a finding, not an error. Record both citations, do not silently pick one.
- If a source contradicts a round-1 file (`research/01..05`), log it explicitly under `## Corrections to round-1 research` and keep the round-1 file untouched.
