> Team-level competitive notes (repo names, handles, file paths, overlap maps) were removed before commit. `learnings.md` is not in this repo. This file and `REPORT.md` override `docs/design/` and `docs/research/`.

# Sheldon: idea check, FINAL PASS (v5)
**Written:** Sat 17 Oct 2026, about 11:20 AM IST (session time). **Deadline:** Sun 18 Oct 2026, 11:59 PM IST, about 36 h away. Phase is still research/validation only (BRIEF.md).
**Previous versions kept:** check-20261017-1100IST.md (v4), -1050IST (v3), -1030IST (v2), -1040IST (v1).
**Inputs:**
- BRIEF.md, including the 10:50 IST direction update: build around FalkorDB, ground the idea in recent pains and papers
- pain-finder/pains.md and eggbot-summary.md
- paper-scout/papers.md
- sponsor-intel/features.md and intel.md
- field notes (not committed; team names were stripped)
- idea-validator/native-test-draft.md
- check.md v4

Secondary sources are cited as such. Everything I re-verified myself is marked "(re-checked today)".

## 1. Verdict: GO WITH FIXES

**Final headline (3 lines):**
- **(a)** A hypothesis is refuted only by one atomic Cypher write that checks that every cited evidence event exists. Otherwise the write returns 0 rows and is rejected. No LLM decides.
- **(b)** One traversal flags every open task resting on a refuted hypothesis, before an agent acts on it.
- **(c)** Repeated failed steps, Sheldon vs plain memory, reported as raw counts on a stated scenario set (N scenarios × ≥3 runs).

**What I adjusted, and why:**
- (b) is **not novel as a mechanism**. Downstream invalidation already shows up in the field, and STALE/CUPMem calls the idea "propagation-aware invalidation".
- The defensible part of (b) is the *source and target*: a refute gated on cited evidence ids that, in the same write, flags open tasks. Say "none we found". Never "nobody else", and never "reaching the task board is ours".
- (a) stays: none we found gates confirm/refute by a rule that checks cited ids, with no LLM in the decision.
- (c) stays: none we found reports a with/without-memory repeated-steps count. Say "we measured".

**Positioning line (opinion):** "Lease, handoff and resume are table stakes. Sheldon's contribution is that a refute only lands if its cited evidence ids exist and flags dependent tasks in the same write (none we found do both), and we measured the effect."

## 2. FalkorDB-native test
Full table in native-test-draft.md. Condensed, with the doc for each verdict:

| Feature Sheldon uses | Postgres / Neo4j just as well? | FalkorDB-native? |
|---|---|---|
| Atomic single-query claim/refute ([concurrency](https://docs.falkordb.com/design/concurrency)) | **Yes**: `UPDATE…WHERE…RETURNING` / `SKIP LOCKED`; Neo4j single-statement tx | No, generic. Other systems use the same single-query pattern |
| Serialized per-graph writes + snapshot reads (same) | PG/Neo4j MVCC is finer-grained | Simpler, and a throughput limit. Pair it with per-investigation keys |
| One graph per investigation as a key ([graph.list](https://docs.falkordb.com/commands/graph.list)) | PG schema-per-tenant is heavier. Neo4j multi-DB I believe is Enterprise-only (unverified) | **Yes, advantaged.** FalkorDB pushes it ("81,500 graphs", intel.md, secondary) |
| `GRAPH.COPY` ([graph.copy](https://docs.falkordb.com/commands/graph.copy)) | PG `CREATE DATABASE … TEMPLATE` is heavier. Neo4j equivalent unverified | **Advantaged, not novel.** Other submissions already use it. Methods line only. Never say "no competitor has it". |
| Multi-type var-length paths (spike A2) | PG recursive CTE works but is verbose. Neo4j: yes | Advantaged vs PG only. GraphBLAS sparse matrices (repo description https://github.com/FalkorDB/FalkorDB). **Speed is unmeasured at ~300 events, so don't claim it** |
| Vector HNSW + full-text ([vector](https://docs.falkordb.com/cypher/indexing/vector-index), [fulltext](https://docs.falkordb.com/cypher/indexing/fulltext-index)) | **Yes** (pgvector, tsvector; Neo4j both) | Only the **composition** is native: anchors + traversal in one Cypher query. Hindsight needs PG+pgvector+GIN for the same (papers.md #6, secondary) |
| Constraints ([constraint-create](https://docs.falkordb.com/commands/graph.constraint-create)) | **PG is stronger** (FKs, CHECK) | No. Backstop only (see §5) |
| JS UDFs ([udfs](https://docs.falkordb.com/udfs)) | plv8 / APOC exist | Advantaged: loaded at runtime with `GRAPH.UDF LOAD`, called inside Cypher. The docs show only read-side graph access. A sameAction-style UDF: none we found |
| Temporal `localdatetime`/`duration` ([datatypes](https://docs.falkordb.com/datatypes)) | **Yes**, and PG is richer (timezones) | No. Use it anyway; it's cheap |
| Algorithms: BFS, WCC, betweenness, pageRank ([algorithms](https://docs.falkordb.com/algorithms/)) | PG: no (AGE/pgRouting partly). Neo4j: GDS plugin | Advantaged: built in, same query. BFS and PROFILE: none we found using them this way |
| `RO_QUERY` + timeout, `GRAPH.PROFILE`, `GRAPH.MEMORY` | Equivalents exist | Generic. Sponsor-praised habits (intel.md) |

**Bottom line (opinion):** Sheldon *could* run on Postgres. Every core operation is one FalkorDB query against one investigation key versus multi-table recursive SQL. Pitch "one query, one key", show the Cypher, and don't say "only possible on FalkorDB".

**GRAPH.COPY eval reset: KEEP, but as a methods line, not a novelty claim.** It makes (c) reproducible: every S0/S3 run starts from an identical frozen seed. It is documented, and it is not ours to claim. Pitch wording: "every run starts from a GRAPH.COPY of the frozen seed". Never say "no competitor has it" (claim #5 stays wrong).

## 3. People test
**Does the headline match pain clusters?** Yes, for (c) strongly, (a) moderately, and (b) via its symptom only. Counts are from pains.md (secondary): cluster 2 "re-tries what already failed" has 15 quotes, cluster 4 "runaway loops" has 10, cluster 6 has 12 with thin first-person "can't explain" quotes, cluster 5 "stale memory acted on" has 13.

- **(c) repeated failed steps. Strong.** Quotes re-checked today against the X API (text exact, dates in window, links resolve):
  - "the agent stuck in a loop running the same git status command 1435 times for the last 5 hours" — @lavaze_, https://x.com/lavaze_/status/2102597283531673838, 2026-09-23 ✔
  - "we lost a day once because the second agent retried the same broken approach without that trail." — @sunsetsyntax, https://x.com/sunsetsyntax/status/2104832764407087549, 2026-09-29 ✔
- **(a) reframed as "done with no evidence", per pain-finder:**
  - "It ran the tests at some point, kept editing, then wrote "all tests pass" from memory." — @neil_xbt, https://x.com/neil_xbt/status/2102220336456724960, 2026-09-22 ✔
  - "Told an agent the layout looked wrong and it confidently said it was fixed. Never opened the preview." — @Erica_Codes_NJ, https://x.com/Erica_Codes_NJ/status/2110414801495056841, 2026-10-14 ✔
  - "An AI SRE that can't show its reasoning trail is just a faster way to be confidently wrong at 3am." — @_malcolmadams, https://x.com/_malcolmadams/status/2108748636498858140, 2026-10-10 ✔
  - Note: this one replies to Elastic's "nightshift AI SRE" launch, which advertises "ruling out dead ends and showing you how it got there". That is a commercial incumbent making a similar promise. Know it exists.
- **(b) refutation → tasks. Symptom only.** Pain-finder itself notes nobody describes the mechanism. Not re-checked by me (Reddit is blocked from the box), so use them as **UNVERIFIED** until checked:
  - "The agent isn't wrong about what it remembers — it's wrong about what it's still true." — u/Lopsided_Manner_7602, https://www.reddit.com/r/AI_Agents/comments/1wmh2lg/why_your_agent_keeps_bringing_up_things_you/
  - "the only evidence was the agent’s own sentence" — u/Medium-Lie8127, Reddit
- Don't cite @mikecane's "$8,000" (hypothetical, per pains.md).

## 4. Paper checks (re-checked today on the arXiv HTML full text)
| Claim for slides | Status | Exact source text |
|---|---|---|
| STALE/CUPMem: gpt-4o-mini 8.7% → 68.0% | **V** | "under the same backbone model (GPT-4o-mini), this explicit adjudication paradigm improves overall accuracy from 8.7% to 68.0%" https://arxiv.org/abs/2605.06527 (Table 2) |
| STALE: best frontier model without it = 55.2% | **V** | "Even the strongest model, Gemini-3.1-pro, achieves only 55.2% overall accuracy" (same). Caveat: CUPMem is the authors' own method on their own benchmark |
| MAST: step repetition = 15.7% of failures | **V** | "step repetitions (FM-1.3, 15.7%)" https://arxiv.org/abs/2503.13657 . Paper-scout says it is the largest single mode; that's consistent with the other FM figures I saw (11.8, 12.4, 2.8, 1.5), but I didn't check every mode |
| TIDE: Loop Ratio | **V** | Defined as "the proportion of these redundant loop actions relative to the total actions". "mitigates the average LR from 15.8% to 1.0% in BlocksWorld … WebShop, from 36.7% to 5.7%" https://arxiv.org/abs/2602.02196 . That reduction comes from **model scaling** (Qwen3-4B → 30B), not memory. Don't imply memory did it |
| BeliefMem: ALFWorld 59.88 → 28.71 | **V** | "success rate on ALFWorld drops from 59.88 to 28.71, and average F1 on LoCoMo falls from 42.38 to 22.58" when "only the single most likely conclusion is kept" https://arxiv.org/abs/2605.05583 |
| MIRIX id = 2507.07957 | **V** | https://arxiv.org/abs/2507.07957 title "MIRIX: Multi-Agent Memory System for LLM-Based Agents" |
| HippoRAG +38.6 | **V as points** | Appendix table AR@5: ColBERTv2 37.1, HippoRAG 75.7 https://arxiv.org/abs/2405.14831 |

**Slide rule:** paper numbers motivate the design. They are never Sheldon's results (PLAN §5.2 rule 3).

## 5. Rulings (opinion, against the P0–P4 freeze and about 36 h)
- **Pick #3, path-checked citations within n ≤ 2 hops inside the gate: CONDITIONAL GO, and the default is OFF.**
  - Build the existence-check gate (P3/P4) first.
  - Add the hop check only if the refute query is green with time left. It's one extra `WHERE` with a bounded path pattern in the same atomic query.
  - Label it "our design, untested by any paper". Papers.md found none; G-Memory's 1-hop result is about retrieval, not citation (secondary).
- **Pick #6, marking stale tasks in the same write: GO.**
  - This *is* headline (b) done at write time: the refute query also `SET`s `stale=true` on open tasks within the bounded traversal, atomically ([concurrency](https://docs.falkordb.com/design/concurrency): compound clauses are atomic).
  - Keep the depth bounded (`*1..3`). Never use `*0..` unbounded: LIMIT doesn't restrict eager ops ([known-limitations](https://docs.falkordb.com/cypher/known-limitations)).
  - Still expose the read-only Q* so the demo can show the path.
- **Pick #1, labels as vector filters: CUT (defer).** It means a second vector index per label, and the spike already showed post-filtering works at demo scale (research/v3_00 B2). Not headline-critical.
- **Read-only "same action" JS UDF: CONDITIONAL GO, time-boxed to 1.5 h.**
  - Benefit: it makes (c) computed in Cypher, and none we found has one.
  - Requirement: needs ≥6.0.2 per features.md (UDF fixes, secondary). **Whether FLEX is in the image is UNVERIFIED.** I couldn't run Docker in this pass, so check with `GRAPH.UDF LIST` on the pinned image.
  - Conflict: the team spiked on 4.22.1, not 6.0. **Pick one image tag now.** If they stay on 4.22.1, write the UDF in plain JS without FLEX, or compute sameAction in Python.
  - Fallback: Python normalisation.
- **BeliefMem's point: GO, partially.**
  - Refute flips `status` and never deletes. Refuted hypotheses stay retrievable and labelled. This is already the append-only design (PLAN §5.2).
  - Add a `confidence` float property, updated in the same gated write. Use one simple rule (e.g. Hindsight's contradict = −2α, papers.md, secondary).
  - Do **not** build BeliefMem's full noisy-or multi-candidate machinery. That's out of scope. Cite BeliefMem ([2605.05583](https://arxiv.org/abs/2605.05583)) only for "a single hard conclusion hurts".
- **MCP server: stays CUT** unless P0–P4 is green.

## 6. Top 3 fixes
1. **Freeze to P0–P4 + the eval, and pin the image tag today.** Docker Hub (checked 11:07 IST): `latest` and `v4.22.1` share digest sha256:b0bdcac… (pushed Oct 15), so `latest` is 4.22.1, not 6.0 (correction: earlier text said 6.0). 6.0 is `falkordb/falkordb:6.0.2` (no `v`, pushed Oct 8). Pin `6.0.2` if the same-action UDF ships, else `v4.22.1`; never `latest` or `edge`. Re-run the spike once on the pinned tag.
2. **Build the refute as one gated write + stale-mark (picks #6 + BeliefMem status/confidence), and name Q\*** as the demo question, with S0 failing it live and the Cypher shown.
3. **Produce (c) honestly:**
   - stated scenarios
   - a written definition of "repeated failed step" (MAST-style; optionally report TIDE loop ratio too)
   - S0 vs S3 raw counts over ≥3 runs from a `GRAPH.COPY`-reset seed

## Claims that must leave the pitch (carried forward and updated)
- "no competitor / no other graph DB has GRAPH.COPY's equivalent" (#5, wrong)
- "vector queries can't be combined with filters, so per-investigation graphs are forced" (#7, overstated)
- "coordination + memory on one graph / handoff-as-state is our gap" (#32, wrong: other submissions already ship it)
- "we track hypotheses" as a differentiator (#34)
- "refutations propagate downstream" as **novel**, and "reaching the task board is ours". Claim only the combination: evidence-gated refute + same-write task flagging, "none we found".
- "nobody else measures repeated steps" (#33): say "none we found"
- "only possible on FalkorDB" / any unmeasured speed claim (GraphBLAS, blog p99 figures)
- research/02's MIRIX id 2501.02388, HippoRAG "+38.6%", and "IRCoT 4–6 round-trips" (#35–38)
- TIDE's LR drop presented as a memory effect (it's model scaling)
- "Mandatory MATCH can't follow OPTIONAL MATCH" / "MERGE path duplicates" (#13): unverified, test or drop

## Claims table (carried from v4, with paper-scout corrections appended)
Status key: V = verified, W = wrong or overstated, U = unverifiable.

| # | Claim (from PLAN_SHELDON.md unless noted) | Status | Source / note |
|---|---|---|---|
| 1 | Per-graph reader-writer model: writes serialized FIFO, every write query atomic including schema rollback | V | https://docs.falkordb.com/design/concurrency |
| 2 | No native multi-query transactions; MULTI/EXEC "serializes all enclosed commands across all graphs" | V (verbatim FAQ) | same page |
| 3 | So a single conditional MATCH…SET works as a race-free lease | V by inference from 1; team spike says proven on the engine (research/v3_00) | same page. Inference, not a doc statement. Re-run the race test on the build you demo |
| 4 | GRAPH.COPY: consistent snapshot, copies indexes and constraints, source stays accessible, errors if dest exists, no latency documented | V | https://docs.falkordb.com/commands/graph.copy |
| 5 | "No competitor has it" / "no competing graph DB has an equivalent" to GRAPH.COPY sandboxing | **W. Remove** | Other submissions already use GRAPH.COPY. The "no other database" half has no primary source either. Do not name those submissions in the pitch |
| 6 | Vector index: HNSW, 1–4096 dims, cosine/euclidean only, `queryNodes(...) YIELD node, score` | V | https://docs.falkordb.com/cypher/indexing/vector-index |
| 7 | "Vector index queries do not combine with property filters", which forces graph-per-investigation | **W (overstated)** | The docs say "No support for filtering: Vector queries don't combine well with property filters" (same page). Your spike B2 shows `YIELD node,score WHERE node.team=...` runs. Accurate version: post-filtering works, but the filter runs on the top-k, so recall drops. Per-investigation graphs are a *good choice*, not a forced one |
| 8 | Docs' algorithm list (BFS, SPpath, A*, SSpath, MSF, PageRank, Betweenness, Harmonic, WCC, CDLP, MaxFlow) | V | https://docs.falkordb.com/algorithms/ . The docs name "CDLP", while the engine procedure is `algo.labelPropagation` (the repo has it in graph/src/runtime/functions/algo_procedures.rs and tests/flow/test_cdlp.py, https://github.com/FalkorDB/FalkorDB). This matches spike B1 |
| 9 | No native Personalized PageRank | V (absence) | Not in the algorithms page. GitHub code search for "personalized" in FalkorDB/FalkorDB returned 0 hits (17 Oct) |
| 10 | Relationship-uniqueness limitation; alias the relationship to get correct counts | V | https://docs.falkordb.com/cypher/known-limitations |
| 11 | Indexes don't handle `<>` | V | same |
| 12 | LIMIT doesn't restrict eager ops | V | same |
| 13 | "Mandatory MATCH cannot follow OPTIONAL MATCH"; "MERGE on a whole path duplicates nodes" | U | Not on the known-limitations page as of 17 Oct. Test it or drop it |
| 14 | Multi-type var-length `[:CAUSED_BY\|RESULTED_IN*1..3]` works | V by team spike only | research/v3_00 A2. No doc page fetched. Note intel.md: FalkorDB 6.0 (Rust engine, 29 Sep 2026) is the current major version, so **record which image/version the spike ran on** and demo on that same one |
| 15 | MAGMA arXiv:2601.03236: semantic/temporal/causal/entity graphs, policy-guided traversal, LoCoMo + LongMemEval, ACL 2026 Main | V | https://arxiv.org/abs/2601.03236 (abstract plus comments field "ACL 2026 Main"). "Three logical layers" and the ACL Anthology ID remain U, as the team already flagged |
| 16 | HippoRAG: PPR, "up to 20%", "10-30 times cheaper and 6-13 times faster", NeurIPS 2024 | V | https://arxiv.org/abs/2405.14831 |
| 17 | A-MEM quotes, NeurIPS 2025 | V | https://arxiv.org/abs/2502.12110 |
| 18 | CoALA: episodic/semantic/procedural, TMLR | V for venue (comments field). Section 4.1 quote is U, because I read the abstract only | https://arxiv.org/abs/2309.02427 |
| 19 | Generative Agents abstract quote + ablation claim | V | https://arxiv.org/abs/2304.03442 |
| 20 | WorkflowOps: "memoryless" + "largest gains on structured, decomposable tasks where past agent handoff patterns transfer" | V (quotes) | https://arxiv.org/abs/2610.07860 . Framing caution: its experiments are code/math/QA suites, not incident response. "Incident response is the regime they measured" is *your* inference |
| 21 | VeriMAP: "inter-agent handoffs" quote | V | https://arxiv.org/abs/2510.17109 |
| 22 | Veri-Sure: "semantic drift as intent is reinterpreted across agent handoffs" | V (quote), but a stretched context | https://arxiv.org/abs/2601.19747 is about **RTL/Verilog code generation**. Say so if you cite it |
| 23 | OneVoice quotes | V | https://arxiv.org/abs/2609.31673 (speech pipelines, same caveat) |
| 24 | arXiv:2605.06457: HF1, ASR, Transition Recall/Precision, 18 LLMs, 90,000 instances, GPT-4.1 shortcut, PAKDD 2026 workshop | V | https://arxiv.org/abs/2605.06457 . The paper uses Huang et al., but I did not check the author list |
| 25 | LongMemEval: 500 questions, ICLR 2025 | V. "7 question types", "S ~115k / M ~1.5M tokens" are U from the abstract (it says *five core abilities*) | https://arxiv.org/abs/2410.10813 |
| 26 | LoCoMo: 50 conversations, avg 300 turns, 7,512 questions, human 87.9 F1 vs 41.4 | Partial: "300 turns" V. The rest is U from the abstract | https://arxiv.org/abs/2402.17753 . You're not using these numbers, so leave them out of the pitch |
| 27 | MemoryAgentBench four competencies | V | https://arxiv.org/abs/2507.05257 |
| 28 | arXiv:2609.38021: re-judging changes labels | V ("re-judging the same pass-1 answers changes three labels") | https://arxiv.org/abs/2609.38021 |
| 29 | arXiv:2610.10265: final-answer scores hide stale/misattributed memory | V | https://arxiv.org/abs/2610.10265 |
| 30 | Graphiti EntityEdge has valid_at/invalid_at/expired_at; Episodic/Community/HasEpisode/NextEpisode edges are separate classes; "invalidated — not deleted" | V | https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py ; https://github.com/getzep/graphiti/blob/main/README.md . I did not re-check the claim that the episodic edges lack temporal fields field by field |
| 31 | mem0-falkordb: per-user graph `{database}_{user_id}` | V | https://docs.falkordb.com/agentic-memory/mem0 |
| 32 | "In every system we fetched, coordination and memory are separate" / handoff-as-state is our gap | **W in this field** | Other submissions already put tasks, handoffs, and memory on one graph. Lease, handoff, and resume are table stakes |
| 33 | "Duplicated steps is the metric no competing entry measures" | U | Say "we measure", not "nobody else does". At least one other submission already reports a measured eval of a different metric |
| 34 | "We track hypotheses" as a differentiator | **W as a headline** | Hypothesis graphs already exist in this event. Do not pitch "we track hypotheses" as the contribution |

**Must leave the pitch:** #5 (wrong), #7 (overstated), #32 (wrong), and #34 as a headline. #33 needs rewording.


| 35 | MIRIX arXiv id in research/02 = 2501.02388 | **W** | The real MIRIX is https://arxiv.org/abs/2507.07957 ("MIRIX: Multi-Agent Memory System for LLM-Based Agents"; title confirmed on the HTML page today). Per paper-scout, 2501.02388 is an unrelated optimisation paper (I didn't open it) |
| 36 | HippoRAG "+38.6% over ColBERTv2 AR@5" (research/02) | **W unit**: it's +38.6 **points** | https://arxiv.org/html/2405.14831 appendix table: ColBERTv2 AR@5 37.1 vs HippoRAG 75.7 (the 2Wiki column), so +38.6 pp. Quote it as points |
| 37 | HippoRAG "10–30× cheaper" | V on the abs page (#16). Paper-scout says the v3 abstract text says 10–20× | I did not re-check v3 wording. Safest is to quote "6–13× faster" only |
| 38 | "IRCoT needs 4–6 LLM round-trips, 5–10 s" (research/02) | U | Paper-scout couldn't find it in HippoRAG. Drop it |
## Traversal-question analysis
- **What the docs actually commit to:** "a question whose answer is 2–3 hops from any text match", with timeline questions excluded. **No concrete question is named anywhere** (grep of PLAN, stuff.md, REPORT, research). The design's own test is not yet passed.
- **Candidates in the docs, and how they could be answered without a graph:**
  - "Why did the pool-size increase not help?" / "Why did the rollback fail?" Vector search finds the action event, and one join to its result event answers it. That's a 1-hop lookup, so it fails the test.
  - `resume()` / `state` ("what do we believe, what's next"). In SQL this is `hypotheses WHERE status` plus `tasks LEFT JOIN deps WHERE status<>'done'`: 2–3 fixed joins. Valuable, but not impossible without a graph.
  - "Everything about checkout-svc" (2 hops via INVOLVES/RELATED_TO). Fixed-depth joins.
- **Honest position:** at ~300 events, *nothing* is impossible without a graph. A recursive CTE in Postgres can do variable-depth traversal. "Impossible" will not survive a sharp judge. The defensible claim is: **variable-depth, mixed-edge-type, path-returning questions are one bounded Cypher query here, versus recursive CTEs over N edge tables, and vector search alone cannot answer them at all.**
- **Proposed Q\*** (adapt it to your seeded incident):
  > "Which open tasks are still blocked by, or justified by, a hypothesis whose supporting evidence traces back to an action that was later refuted, and what's the chain?"
  - Pattern: `(t:Task {status:'open'})-[:DEPENDS_ON*0..2]->(:Task)-[:JUSTIFIED_BY]->(h:Hypothesis)-[:SUPPORTED_BY]->(e:Event)<-[:RESULTED_IN|CAUSED_BY*1..3]-(a:Event {type:'action'})-[:REFUTED_BY]->()` returning the path.
  - Why it is graph-shaped: the depth is unknown in advance, there are 4+ edge types, and the answer is the path itself. Vector search cannot do it, because the refuted action shares no text with the open task. SQL needs recursive CTEs across several edge tables.
  - Seed the incident so the right answer is ≥3 hops from any text match, with one semantically similar decoy (already in PLAN §9).
  - Ask S0 the same question live and show it fail.

## Sources
- **FalkorDB docs:**
  - https://docs.falkordb.com/design/concurrency
  - https://docs.falkordb.com/commands/graph.copy
  - https://docs.falkordb.com/commands/graph.list
  - https://docs.falkordb.com/commands/graph.constraint-create
  - https://docs.falkordb.com/udfs
  - https://docs.falkordb.com/datatypes
  - https://docs.falkordb.com/cypher/indexing/vector-index
  - https://docs.falkordb.com/cypher/indexing/fulltext-index
  - https://docs.falkordb.com/algorithms/
  - https://docs.falkordb.com/cypher/known-limitations
  - https://docs.falkordb.com/agentic-memory/mem0
- **FalkorDB repo:** https://github.com/FalkorDB/FalkorDB
- **arXiv (abs and HTML, re-checked today):**
  - 2605.06527, 2503.13657, 2602.02196, 2605.05583, 2507.07957, 2405.14831
  - the v1 set: 2601.03236, 2502.12110, 2309.02427, 2304.03442, 2610.07860, 2510.17109, 2601.19747, 2609.31673, 2605.06457, 2609.38021, 2610.10265, 2410.10813, 2402.17753, 2507.05257
- **X posts re-checked today:**
  - https://x.com/lavaze_/status/2102597283531673838
  - https://x.com/sunsetsyntax/status/2104832764407087549
  - https://x.com/neil_xbt/status/2102220336456724960
  - https://x.com/Erica_Codes_NJ/status/2110414801495056841
  - https://x.com/_malcolmadams/status/2108748636498858140
- Hackathon-team repositories were read during validation and left out of this tree on purpose.
- **Secondary (bot outputs kept here):** `docs/engine/papers.md`, `docs/engine/features.md`. Competitive notes were not committed.
