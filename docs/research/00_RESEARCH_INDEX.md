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

# SheldonAI Research Ledger: Track 02 (Agent Memory & Coordination)

**Hackathon:** Graph Hacks: Give Your AI Agents Real Context (WeMakeDevs × FalkorDB), Oct 15–18 2026
**Track:** Track 02 — Agent Memory and Coordination
**Status:** ROUND 2 COMPLETE (10 research files `v2_01`..`v2_10`, 94 claims with fetched sources)
**ROUND 3 (execution):** `v3_00_p0_engine_spike_findings.md` — P0 gate **PASSED**. Engine semantics resolved by running queries, not reading docs. Two docs claims overturned, one silent-failure trap found. Scripts in `spikes/`.
**Rounds:** Round 1 = `research/01..05` (main-agent research, partially unverified). Round 2 = `research/v2_*` (subagent + main-agent research, source-fetched). Round-1 files were left unmodified; all corrections to them are recorded inside the round-2 files.

---

## 1. Round 2 file matrix

| File | Topic | Author | Claims | Status |
|---|---|---|---|---|
| `v2_01_existing_memory_systems.md` | Mem0-on-FalkorDB, Graphiti-on-FalkorDB in depth; 6 other systems carried from round 1 | main agent | M1- | COMPLETE (2 systems freshly audited, 6 carried and flagged) |
| `v2_02_graph_native_memory.md` | FalkorDB ecosystem shape, which integrations are first-party vs adapter, MCP question | main agent (subagent interrupted, salvaged) | M2- (9) | PARTIAL — ecosystem verified; MCP coordination primitives open |
| `v2_10_differentiation_research.md` | The gap the 2025–2026 multi-agent literature names; predicted competing field; Generative Agents | main agent | D- (12) | COMPLETE — 4 papers verbatim-quote our exact gap |
| `v2_03_batch_and_graphrag_systems.md` | Cognee, LightRAG, GraphRAG, newer OSS | — | — | **NOT COMPLETED** — subagent interrupted; open scope listed in file || `v2_04_benchmarks_and_evaluation.md` | LongMemEval, LoCoMo, Mem0 eval, benchmark criticisms, 48h eval plan | subagent A4 | M4- (17) | COMPLETE — all arXiv IDs re-verified |
| `v2_05_falkordb_technical.md` | FalkorDB ground truth: engine, concurrency, GRAPH.COPY, vector, algorithms, limits, SDK | main agent | M5- (23) | COMPLETE — every command quoted from a fetched docs page |
| `v2_06_academic_foundations.md` | CoALA, HippoRAG, A-MEM in depth; 6 papers carried from round 1 | main agent | M3- (18) | COMPLETE — 2 round-1 claims downgraded |
| `v2_07_multiagent_coordination.md` | Atomic task leasing, GRAPH.COPY sandboxing, graph-delta handoffs, concurrency posture | main agent | M6- (15) | COMPLETE |
| `v2_08_verification_audit.md` | Audit of every claim across round 2, plus downgrades of round-1 claims | verifier | V- | COMPLETE |
| `v2_09_critical_claim_verification.md` | CoALA taxonomy + Graphiti bi-temporal model, verified to source code | subagent | 2 claims | COMPLETE — both CONFIRMED |
| `v2_02_graph_native_memory.md` | MCP memory servers, wider FalkorDB ecosystem | — | — | **NOT COMPLETED** — subagent interrupted |

## 2. What makes Sheldon different — the sourced version

`v2_10_differentiation_research.md` established this, from papers fetched 15 Oct 2026. Before that pass our differentiation rested on comparing ourselves to Graphiti and mem0, which was weak and partly wrong (Graphiti *does* have bi-temporal validity).

The stronger, sourced argument: **four independent 2025–2026 papers name our exact gap in their own words.**

- **WorkflowOps** (arXiv:2610.07860): "their orchestration layers remain largely **memoryless**: each new task is decomposed, assigned, and executed from scratch with no benefit from prior successful executions" — *and* it reports the largest gains on "structured, decomposable tasks where past agent handoff patterns transfer", which is exactly the incident-response regime.
- **VeriMAP** (arXiv:2510.17109): failures arise "from subtle misalignments in task interpretation, output format, or **inter-agent handoffs**".
- **Veri-Sure** (arXiv:2601.19747): names "**semantic drift as intent is reinterpreted across agent handoffs**" — the failure Sheldon's "events are ground truth" rule prevents.
- **OneVoice** (arXiv:2609.31673): "agent-to-agent handoff fragile" with tool-specific formats; an explicit shared representation beats "**implicit agent-defined handoffs**".

Every one of them treats a handoff as *passing the task along*. None transfers *verified accumulated state*. That is Sheldon's contribution.

We also get a published metric name: Agentic Success Rate / Transition Recall and Transition Precision (arXiv:2605.06457), plus its warning that a system can score perfectly on outcome and handoff-F1 metrics while still skipping checkpoints — which is why our eval counts graph state, not just task completion.

## 3. Verified findings we can build on

### FalkorDB engine (all from docs.falkordb.com, fetched Oct 15 2026)

- **Per-graph reader-writer model:** many reads in parallel, writes serialized FIFO, one write at a time per graph.
- **Every write query is atomic**, including rollback of schema changes created mid-query.
- **Readers get snapshot isolation** — state as of query start, never partial writes.
- **No native multi-query transactions.** `MULTI`/`EXEC` blocks *all* graphs, so coordination must be single-query.
- **`GRAPH.COPY`** produces a consistent snapshot, copies nodes, relationships, properties, **indexes and constraints**, keeps the source accessible, and errors if the destination exists. **Latency is not documented — do not quote a figure.**
- **Algorithm list (read from docs, then EXECUTED — engine disagrees):** the running engine registers exactly 11: `algo.AStar`, `algo.betweenness`, `algo.BFS`, `algo.HarmonicCentrality`, `algo.labelPropagation`, `algo.maxFlow`, `algo.MSF`, `algo.pageRank`, `algo.SPpaths`, `algo.SSpaths`, `algo.WCC`. **`algo.CDLP` and `algo.betweennessCentrality` do not exist; `algo.labelPropagation` does.** Whole-graph algorithms take **no arguments** (`algo.WCC()`, `algo.labelPropagation()`, `algo.betweenness()`); passing `('S','L')` returns `[]` silently. `algo.pageRank` takes `(label, relType)` or `(NULL, NULL)`. `algo.AStar` is geographic (needs lat/long), not general A*. Full detail: `v3_00_p0_engine_spike_findings.md`.
- **`algo.pageRank(label, relationship-type) YIELD node, score`**, both parameters optional (null = all).
- **Vector index:** HNSW, 1–4096 dims, `cosine` or `euclidean` only, params `dimension`/`similarityFunction` required plus `M`=16, `efConstruction`=200, `efRuntime`=10.
- **`CALL db.idx.vector.queryNodes(label, attr, k, vecf32(...)) YIELD node, score`** — the yielded column is `node`, not `entity`.
- **Documented traps that affect our queries:** `LIMIT` does not restrict eager writes; an unreferenced relationship alias only requires one match; vector queries don't combine well with property filters (overstated; see check.md claim 7 — post-filter is a top-k cut); `<>` is not index-optimised; label expressions and regex operators are unsupported.

### Prior art (fetched)

- **`mem0-falkordb` plugin** exists: `register()` runtime patch, per-user graphs named `{database}_{user_id}`, `delete_all` drops the user graph. Mem0-on-FalkorDB per-user isolation **already exists**.
- **`graphiti-core[falkordb]`** exists: `Graphiti(uri="falkor://...")`, `graph_name` per tenant, one-time `build_indices_and_constraints()`. Graphiti's bi-temporal model is **confirmed**: `EntityEdge` carries `valid_at`, `invalid_at`, `expired_at` (all default `None`), `created_at` on base `Edge`, persisted on the `RELATES_TO` relationship via `SET e = $edge_data`. Invalidation **marks, never deletes**. README: "old facts are invalidated — not deleted."

### Academic (fetched, quotable)

- **CoALA** arXiv:2309.02427, TMLR. Section 4.1 verbatim: "These include short-term working memory and several long-term memories: episodic, semantic, and procedural." Also: "CoALA's notion of working memory is more general: it is a data structure that persists across LLM calls", and "CoALA structures this top-level program into decision cycles". **Caveat: CoALA does not discuss bi-temporal validity — do not attribute that to it.**
- **HippoRAG** arXiv:2405.14831, NeurIPS 2024. Orchestrates "LLMs, knowledge graphs, and the Personalized PageRank algorithm". Results: **"up to 20%"** over SOTA on multi-hop QA; single-step retrieval **10-30x cheaper and 6-13x faster** than IRCoT. **If you quote HippoRAG's 2Wiki AR@5 figure, say +38.6 points (37.1 → 75.7), never "+38.6%".**
- **A-MEM** arXiv:2502.12110, NeurIPS 2025. Zettelkasten-style dynamic linking with memory evolution. Key quotable line: existing memory systems lack organisation **"despite recent attempts to incorporate graph databases."**
- **LongMemEval** arXiv:2410.10813 (500 questions, LLM-judge + Recall@k/NDCG@k). **LoCoMo** arXiv:2402.17753 (7,512 questions). **Mem0's system paper** arXiv:2504.19413. See `v2_04` for full detail and for benchmark-instability criticisms.

## 3. The gap, stated correctly

Round 1's gap matrix claimed Graphiti "lacks bi-temporal validity". **That is false and must be removed from any submission.** The defensible, sourced gap is:

1. Graphiti's bi-temporality is on **entity fact edges (`RELATES_TO`) only** — episodic and structural edges carry only `uuid`, `group_id`, `created_at`.
2. Graphiti has **no procedural memory** as reusable action DAGs. CoALA Section 4.1 names procedural memory as a distinct long-term store; no fetched Graphiti page implements it.
3. Graphiti has **no coordination primitive** — no task leasing, no shared blackboard, no handoff, on any page we fetched.
4. **No fetched system** provides speculative sandboxed execution. `GRAPH.COPY` is documented as a graph clone command, but no fetched page uses it for agent sandboxing.
5. **No public benchmark exists** for agent-memory race conditions, shared-state corruption, or handoff fidelity (subagent A4's negative finding, stated as a negative finding).

The engine guarantee that makes our coordination claim defensible without any invention: a single `GRAPH.QUERY` is atomic and writes are serialized, so one Cypher query is a correct task lease with no external lock. That is quoted from `docs.falkordb.com/design/concurrency.md`.

## 4. Claims removed from our pitch (round-1 claims that did not survive re-check)

| Removed claim | Why |
|---|---|
| "HippoRAG improves All-Recall@5 by 38.6%" | The abstract says "up to 20%"; the 38.6% figure is not there. |
| "Graphiti lacks bi-temporal validity" | False. Confirmed from `graphiti_core/edges.py`. |
| "`algo.labelPropagation` exists" / "`algo.bipartite` exists" | **Partially reversed by execution (v3_00).** `algo.labelPropagation` **DOES** exist on the running engine. `algo.bipartite` does not. `algo.CDLP` does not exist — it was the docs, not the engine, that misled here. |
| "GRAPH.COPY is sub-second for < 100k nodes" | No latency figure exists in the docs. Measure it ourselves. |
| "FalkorDB uses a single-threaded event loop" | Docs describe a thread pool with parallel reads and a serialized FIFO write queue. |
| "96% token savings on graph-delta handoffs" | An estimate with no experiment. Measure it or drop it. |
| "Memorable (YC 2026)" | Round-1 audit already flagged as unverifiable; not revived in round 2. |

## 5. What still must be checked before the submission

| # | Item | Why it matters | Cost |
|---|---|---|---|
| C3 | `timestamp()` unit in FalkorDB | Every lease calculation. **This blocks writing coordination code.** | 2 minutes in a live container |
| C4 | YIELD fields for algorithms other than `algo.pageRank` | Build code will use `algo.labelPropagation` / `algo.WCC` / `algo.betweenness` | **RESOLVED by execution 15 Oct 2026 (`v3_00_p0_engine_spike_findings.md`)** — `WCC`→`componentId`, `labelPropagation`→`communityId`, `betweenness`→`score`, `pageRank`→`score`, `BFS`→`nodes,edges`, `SPpaths`/`SSpaths`→`path` |
| C5 | Voyager abstract (procedural-memory precedent) | CoALA now covers the concept, but Voyager is the implementation precedent | 1 fetch |
| C6 | Round-1's Pokec benchmark numbers | Do not quote; re-fetch or drop | 1 fetch |
| C7 | Whether `algo.pageRank` can be scoped to a subgraph | Determines the retrieval design | Docs + experiment |
| — | Cognee / LightRAG / GraphRAG deep audit, MCP memory servers and coordination primitives, newer OSS memory layers | Only relevant if we compare against them; Graphiti is the real competitor | Deferred — one open question worth resolving: whether MCP has any state-sharing or locking primitive (`v2_02` M2-08) |

## 6. Recommended next actions

1. **Run FalkorDB locally** (`docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest`) and resolve C3, C4, C7 empirically. Nothing about the build is blocked by anything else.
2. **Build the task-lease query first.** It is the cheapest demonstration of our core differentiator, and the engine docs already justify it. Test two concurrent claimers.
3. **Build the bi-temporal update second.** Graphiti's model is the comparison point and is now known exactly; the gap on episodic edges is where we can differentiate.
4. **Use `v2_04`'s eval plan** (20-50 hand-built cases, retrieval hit rate, scripted concurrent-write scenarios, latency percentiles, no-memory and plain-RAG baselines) rather than claiming leaderboard numbers.
5. **Write the blog post** around the verified engine semantics — the single-query-atomicity argument is genuinely interesting and most competitors will not have noticed it.
