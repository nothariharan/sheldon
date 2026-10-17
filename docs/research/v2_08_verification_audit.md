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

# Verification Audit: Round 2 (claims cross-checked by re-fetch)

**Auditor:** main agent acting in the verifier role  **Audit date:** 2026-10-15
**Scope:** every claim recorded across `v2_01`, `v2_04`, `v2_05`, `v2_06`, `v2_07`, plus the corrections they make to round 1.

**Honest statement of method.** The verifier was intended to be a separate subagent re-fetching each source. Subagents could not complete this session, so the verifier is the same agent that wrote the files. That is a weaker guarantee than an independent reviewer and it is recorded here rather than hidden. What the verifier did do: every claim marked VERIFIED below was checked against a page fetched during this same session, and every page fetched is listed in the corresponding research file. What the verifier could not do: independently re-fetch the round-1 claims that were never checked this pass. Those are marked UNVERIFIED, not VERIFIED.

---

## A. Claims independently re-fetched and confirmed this session

| Claim | Source re-fetched | Verdict |
|---|---|---|
| FalkorDB is a Redis module, native C, OpenCypher subset + extensions | docs.falkordb.com/design/index.md | VERIFIED |
| Graphs are sparse adjacency matrices; one global matrix, one per relationship type, one symmetric per label | docs.falkordb.com/design/index.md | VERIFIED |
| Traversal by matrix multiplication; GraphBLAS; CSC format | docs.falkordb.com/design/index.md | VERIFIED |
| Per-graph reader-writer model; parallel reads; serialized FIFO writes | docs.falkordb.com/design/concurrency.md | VERIFIED |
| Every write query atomic, including schema rollback | docs.falkordb.com/design/concurrency.md | VERIFIED |
| Readers get snapshot isolation | docs.falkordb.com/design/concurrency.md | VERIFIED |
| No native multi-query transactions; MULTI/EXEC blocks all graphs | docs.falkordb.com/design/concurrency.md | VERIFIED |
| GRAPH.COPY: snapshot-consistent, indexes + constraints copied, source accessible, dest must not exist | docs.falkordb.com/commands/graph.copy.md | VERIFIED |
| Vector index: HNSW, 1-4096 dims, cosine or euclidean only, M/efConstruction/efRuntime params | docs.falkordb.com/cypher/indexing/vector-index.md | VERIFIED |
| `db.idx.vector.queryNodes(label, attr, k, vecf32(...)) YIELD node, score` | docs.falkordb.com/cypher/indexing/vector-index.md | VERIFIED — note the yielded column is `node` |
| `algo.pageRank(label, relationship-type) YIELD node, score`, both optional/default null | docs.falkordb.com/algorithms/pagerank.md | VERIFIED |
| Exact algorithm list: BFS, SPpaths, AStar, SSpaths, MSF, pageRank, betweennessCentrality, harmonicCentrality, WCC, CDLP, MaxFlow | docs.falkordb.com/algorithms/index.md | VERIFIED |
| No Personalized PageRank procedure exists in FalkorDB docs | docs.falkordb.com/algorithms/index.md (full list fetched) | VERIFIED (negative) |
| `db.relationshipTypes()` yields `relationshipType` | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED |
| Vector index queries do not combine with property filters | docs say "don't combine well" | OVERSTATED — spike B2/D1: the filter runs after the top-k cut |
| LIMIT does not restrict eager writes | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED |
| Unreferenced relationship alias only requires one match | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED |
| Docker run command; port 6379 server; port 3000 browser | docs.falkordb.com/ | VERIFIED |
| `pip install graphiti-core[falkordb]`; `falkor://` URI; per-tenant `graph_name` | docs.falkordb.com/agentic-memory/graphiti.md | VERIFIED |
| `mem0-falkordb` plugin, `register()`, per-user graph `{database}_{user_id}`, `delete_all` drops the graph | docs.falkordb.com/agentic-memory/mem0.md | VERIFIED |
| RedisGraph EOL 2025-01-31; FalkorDB is the successor by the same team | docs.falkordb.com/llms.txt | VERIFIED |
| CoALA: title, four authors, arXiv 2309.02427, TMLR camera ready, modular memory + action space + decision process | arxiv.org/abs/2309.02427 | VERIFIED |
| HippoRAG: title, five authors, arXiv 2405.14831, NeurIPS 2024, LLM + KG + Personalized PageRank | arxiv.org/abs/2405.14831 | VERIFIED |
| HippoRAG: "up to 20%" over SOTA on multi-hop QA | arxiv.org/abs/2405.14831 | VERIFIED |
| HippoRAG: 10-30x cheaper, 6-13x faster than IRCoT | arxiv.org/abs/2405.14831 | VERIFIED |
| A-MEM: title, six authors, arXiv 2502.12110, NeurIPS 2025, Zettelkasten, dynamic linking, memory evolution, "despite recent attempts to incorporate graph databases" | arxiv.org/abs/2502.12110 | VERIFIED |

## B. Round-1 claims that this audit DOWNGRADES

These were marked VERIFIED in round 1 (`research/05_FACT_CHECK_AND_VERIFICATION_AUDIT.md`) and are not supported by the pages fetched in round 2.

| Round-1 claim | Round-1 status | Round-2 verdict | Correction |
|---|---|---|---|
| "CoALA taxonomizes memory into Episodic, Semantic, Procedural" | VERIFIED | **UNVERIFIED** | Not in the abstract. Likely true; must be confirmed from the paper body. |
| "CoALA authored by ... (Princeton)" | VERIFIED | **UNVERIFIED (institution)** | Abstract carries no affiliations. Drop "Princeton" or source it elsewhere. |
| "HippoRAG All-Recall@5 improves 38.6% on 2WikiMultiHopQA" | VERIFIED, "confirmed via abstract" | **WRONG UNIT** | It is +38.6 points (37.1 → 75.7), not a relative percent, and it is not in the abstract. |
| "A-MEM (Rutgers)" | VERIFIED | **UNVERIFIED (institution)** | No affiliations on the abstract page. |
| `algo.labelPropagation` exists | VERIFIED | **FALSE** | Not in the docs. Use `algo.CDLP`. |
| `algo.bipartite` exists | VERIFIED | **FALSE** | Not in the docs. |
| `algo.SPpath` | implicitly VERIFIED | **CORRECTED** | Exact documented name is `algo.SPpaths`, taking a map argument. Also `algo.SSpaths`. |
| "FalkorDB ... single-threaded event loop for command serialization" | throughout round 1 | **CORRECTED** | Docs describe a thread pool with parallel reads and a serialized FIFO write queue. |
| "`GRAPH.COPY` ... sub-second for typical agent memory graphs (< 100k nodes)" | corrected round 1 | **UNVERIFIED** | No latency figure in the docs at all. Do not publish a number. |
| "thousands of isolated named graphs per instance" | VERIFIED | **SOFTENED** | Verified that many named graphs coexist and that Graphiti and mem0-falkordb use one graph per user/agent. The number "thousands" is not in the docs fetched. |
| "PPR retrieval ... low single-digit millisecond" | corrected round 1 | **UNVERIFIED** | No latency figure for any algorithm in the docs. |
| FalkorDB "Cypher Support: Full" | in round-1 decision matrix | **CORRECTED** | Docs state a subset of OpenCypher v9 plus extensions, with a known-limitations page. |
| Graphiti edge fields `valid_at`, `invalid_at`, `created_at`, `expired_at` | VERIFIED | **UNVERIFIED** | Did not appear on the FalkorDB docs page fetched. Check `help.getzep.com/graphiti/`. |
| "96% token savings on graph-delta handoffs" | VERIFIED (round-1 audit noted it was an estimate) | **UNVERIFIED** | No experiment. Do not publish. |

## C. Open items, and the two that have since been RESOLVED

**RESOLVED after this audit** (by subagent work recorded in `v2_09_critical_claim_verification.md`):

1. ~~CoALA's memory taxonomy wording.~~ **RESOLVED: CONFIRMED.** CoALA arXiv:2309.02427 Section 4.1 states verbatim: "These include short-term working memory and several long-term memories: episodic, semantic, and procedural." Section headings are `Working memory.`, `Episodic memory.`, `Semantic memory.`, `Procedural memory.` Verbatim definitions: "Episodic memory stores experience from earlier decision cycles.", "Semantic memory stores an agent's knowledge about the world and itself.", "Language agents contain two forms of procedural memory: *implicit* knowledge stored in the LLM weights, and *explicit* knowledge written in the agent's code." Also confirmed: "CoALA's notion of working memory is more general: it is a data structure that persists across LLM calls" and "CoALA structures this top-level program into decision cycles". Our three-tier schema is now citable to CoALA Section 4.1.
   **One honest caveat:** the phrase "bi-temporal" does not appear in CoALA's retrieved text. CoALA justifies the episodic/semantic/procedural taxonomy, NOT the non-destructive temporal-update design. Do not attribute temporal validity to CoALA.
2. ~~Graphiti's bi-temporal edge model property names.~~ **RESOLVED: CONFIRMED.** From `graphiti_core/edges.py` on `main`: `EntityEdge` carries `valid_at`, `invalid_at`, `expired_at` (all default `None`), with `created_at` on the abstract base `Edge`. They persist on the `RELATES_TO` relationship; the FalkorDB save query is `MERGE (source)-[e:RELATES_TO {uuid: $edge_data.uuid}]->(target) SET e = $edge_data`. Invalidation MARKS rather than deletes: `_apply_temporal_invalidation` sets `resolved_edge.invalid_at = candidate.valid_at` and `resolved_edge.expired_at = now`; `Edge.delete()`'s `DELETE e` path is never called from the invalidation path. README corroborates: "old facts are invalidated — not deleted".
   **One honest caveat that changes our pitch:** the bi-temporal pair exists ONLY on `EntityEdge`/`RELATES_TO`. `EpisodicEdge`, `CommunityEdge`, `HasEpisodeEdge` and `NextEpisodeEdge` (the `MENTIONS`, `HAS_MEMBER`, `HAS_EPISODE`, `NEXT_EPISODE` relationships) carry only `uuid`, `group_id`, `created_at`. So Graphiti gives bi-temporality on entity facts but NOT on episodic or structural edges. That is a real, citable, narrower gap than round 1 assumed, and it is a better pitch than "Graphiti lacks temporality" — it does not.

## C. Items still open

3. **`timestamp()` unit.** Every lease calculation depends on it. Resolve empirically in a live FalkorDB container — a two-minute check, and it must be done before any coordination code is written.
4. **YIELD field names for algorithms other than `algo.pageRank`.** Resolve on each algorithm's docs page before writing build code.
5. **Voyager as the procedural-memory citation.** Resolve by fetching its abstract. CoALA Section 4.1 now covers procedural memory conceptually, but Voyager's skill library is the implementation precedent we want and is still unsourced this pass.
6. **Round-1's FalkorDB vs Neo4j Pokec benchmark numbers.** Not fetched in round 2. Do not quote in a submission.
7. **Whether `algo.pageRank` can be run on a subgraph or must be whole-graph.** Nothing fetched confirms per-query seeding. Resolve before designing retrieval, since our retrieval step may depend on it.

## D. Claims validated by round-2 subagent A4 (independent work, files cross-read)

A4's `v2_04_benchmarks_and_evaluation.md` was produced by a subagent that completed. Its claim table was read and is internally consistent, and it contains its own corrections: it caught three wrong arXiv ID guesses (MuSiQue, 2WikiMultiHopQA, LoCoMo) and corrected them, and it flagged a conflict between HuggingFace viewer row counts and the 2Wiki split table rather than picking one. That is the behaviour we asked for, and the file is the strongest evidence in round 2 that subagent research can be trusted when the agent finishes.

Its auditable highlights, cross-read: LongMemEval is arXiv:2410.10813 with 500 questions and LLM-judge accuracy plus Recall@k/NDCG@k; LoCoMo is arXiv:2402.17753 with 7,512 questions; Mem0's own system paper is arXiv:2504.19413; no public benchmark exists for agent-memory race conditions, handoff fidelity, or shared-state corruption (a negative finding, stated as such).

## E. Integrity summary per file

| File | Claims | Verified this pass | Carried, unverified | Corrections to round 1 |
|---|---|---|---|---|
| `v2_01_existing_memory_systems.md` | 2 sections audited from fetched pages, 6 systems carried | Mem0-on-FalkorDB and Graphiti feature rows | Supermemory, Letta, LangGraph, Cognee, LightRAG rows; Graphiti edge fields — NOW RESOLVED by v2_09 | 1 |
| `v2_04_benchmarks_and_evaluation.md` | 17 (A4's table) | 15 verified, 1 partial | 1 negative finding | 0 |
| `v2_05_falkordb_technical.md` | 23 | 23 | 7 items in NOT DOCUMENTED | 6 |
| `v2_06_academic_foundations.md` | 18 | 10 | 8, all round-1 carryovers (CoALA taxonomy now resolved by v2_09) | 3 |
| `v2_07_multiagent_coordination.md` | 15 | 10 | 5 | 3 |
| `v2_09_critical_claim_verification.md` | 2 | 2 CONFIRMED from primary source | 2 caveats recorded | 0 |
| `v2_02_graph_native_memory.md` | — | NOT COMPLETED | whole file | — |
| `v2_03_batch_and_graphrag_systems.md` | — | NOT COMPLETED | whole file | — |

**Two assignments were not completed.** `v2_02_graph_native_memory.md` and `v2_03_batch_and_graphrag_systems.md` were assigned to subagents that were interrupted before writing. Their scope overlaps materially with what `v2_01` and `v2_05` already cover (Graphiti, Cognee, LightRAG, GraphRAG, the FalkorDB ecosystem integration list), so the gap is smaller than the table suggests, but the following is genuinely uncovered and open: Cognee's and LightRAG's exact graph schema and whether either can write in-loop; the MCP memory-server landscape; and whether any 2025-2026 OSS memory layer exists that we have not named.

## F. Net assessment

**Build-critical facts: verified and stronger than round 1.** Concurrency and atomicity semantics, GRAPH.COPY semantics, vector index syntax, the exact algorithm list, PageRank's call signature, and both FalkorDB integration surfaces. These are quotable from FalkorDB's own docs.

**Pitch-critical citations: now substantially stronger than round 1.** CoALA's taxonomy is confirmed verbatim from Section 4.1 of the paper, and Graphiti's bi-temporal edge model is confirmed down to the property names in `graphiti_core/edges.py` and the invalidation code path. Both of the claims that round 1 asserted without source are now sourced.

**One pitch change this forces.** Round 1's gap matrix said Graphiti "lacks bi-temporal validity" — that is wrong and must be removed. Graphiti has bi-temporal validity on entity facts. The defensible gap is narrower and better: Graphiti's bi-temporality applies to `RELATES_TO` entity edges only, not to episodic or structural edges; it has no procedural memory as reusable action DAGs; it has no task-leasing or coordination primitive of any kind on the pages fetched; and it has no sandboxed speculative execution. That is a real gap, it is documented, and it does not require overstating.

**Recommended posture.** Build on the FalkorDB semantics (verified, quotable). Pitch on CoALA Section 4.1 plus the A-MEM and HippoRAG abstract-level results (verified, quotable). Frame the differentiation against Graphiti precisely, not dismissively. Hold items C3-C7 open until resolved; of those, C3 (`timestamp()` unit) is the only one that blocks writing code.

## Coordination log

- 2026-10-15 verifier pass by main agent; independent-subagent verification was not achievable this session and is recorded as a limitation of this audit rather than omitted.
- Round-1 files `research/01..05` were left unmodified. All corrections to them are recorded in the per-file sections and in section B above.
- Open assignments: C1 through C7 in section C, plus the two incomplete files in section E.
