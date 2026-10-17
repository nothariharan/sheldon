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

# Sheldon — Build Plan

**Hackathon:** Graph Hacks: Give Your AI Agents Real Context (WeMakeDevs × FalkorDB), Oct 15–18 2026
**Track:** 02 — Agent Memory and Coordination
**Team:** SheldonAI — Akshat Bhaskar (lead), hariharann, Amaan Khan, Satyansh Gaur
**Status:** v1, written 15 Oct 2026 against the verified research in `research/`

> **Why this file exists.** `stuff.md` is a good architecture draft. This file is the answer to three questions it does not answer: *what does the problem statement actually demand*, *what research makes us confident this works*, and *what makes us different from the other 7,000 teams given the same brief.*

---

## 1. The problem statement, resolved into a checklist

The brief: **"Build an agent that acts on connected data, remembers what it learns, and can show how it got to each answer."**

The named problem: *"Agents see pieces, not the whole picture. They lose track of what happened in earlier sessions, miss how people, systems, and records relate, and can't explain why they made a choice."*

| # | The graph must… | Sheldon's answer | Where |
|---|---|---|---|
| 1 | Follow connections across data | Intent-adaptive traversal. Anchors from vector + full-text + time, then **the graph decides what enters context** | §6 |
| 2 | Remember across sessions | Append-only `Event` chain with `NEXT` edges, `Session` nodes, per-agent provenance | §5.1 |
| 3 | Share state between agents | Shared task board **on the same graph as the memory**: atomic claim, lease, handoff | §7 |
| 4 | Connect people, projects, and decisions | `Agent`, `Investigation`, `Hypothesis`, `Decision` events, `PRODUCED`/`DEPENDS_ON` edges | §4 |
| 5 | Show the path behind an answer | Every answer cites event IDs and returns the path; proposed inferences labelled as inferences | §8 |

Track 02's five focus areas:

| Focus | Coverage |
|---|---|
| Episodic, semantic, procedural memory | `Event` / `Entity`+`Hypothesis` / `Playbook` (procedural deliberately thin, P6) |
| Persistent conversation history | Append-only event log, `IN_SESSION` provenance |
| Shared state and handoffs between agents | Task board + `resume()` — **our primary contribution** |
| High-concurrency reads and writes | Serialized writes = single-query atomic claim. Verified engine behaviour |
| Separate memory per user or tenant | One FalkorDB graph per investigation |

**The test we will be judged on:** *"The graph has to shape what the agent does, not sit on the side."* `stuff.md` §0 rule 2 is the correct read: if you could swap the graph for a flat table and get the same answer, the submission fails.

**Our operational version of that test:** in the demo, Agent B must answer at least one question that is *impossible* without traversal — a question whose answer is 2–3 hops from any text match. Timeline questions are excluded, because `ORDER BY ts` answers them without a graph. If we cannot name such a question when we write the eval set, the design has failed its own test.

---

## 2. What everyone else will build

Given the same brief, the field will cluster. This is a prediction, not a claim about any specific team — but it is what the brief selects for, and it tells us where to spend the 48 hours.

| Likely submission | Why it's the obvious reading | Why it loses |
|---|---|---|
| Chat memory wrapped on FalkorDB (mem0/Letta + graph wrapper) | "Persistent conversation history" is the most literal bullet | **Fails the central-not-decorative test.** The graph stores the answer; it never affects it |
| Graphiti + summarisation | "Temporally-aware knowledge graph memory" is marketed at exactly this | Same failure, and it's a vendor tutorial. Judges have seen it |
| Multi-agent swarm with a shared key-value store | "Share state between agents" reads as a message bus | Fails "follow connections across data" — a KV store has no hops |
| HippoRAG-style retrieval on FalkorDB | "Episodic/semantic + multi-hop" maps onto a paper | Retrieval is not memory. Nothing persists across sessions, no coordination. Also: **FalkorDB has no native Personalized PageRank**, so this entry burns hours implementing PPR before discovering it |
| A generic "agent brain" that does a bit of everything | Covers all bullets superficially | No single thing demonstrably works |

**Two entries to expect and to beat explicitly:**

1. **The Graphiti wrapper.** It will be a competent, temporal, multi-tenant graph memory. We beat it on coordination, not on temporality — Graphiti's bi-temporal model is real and confirmed (see §5).
2. **The retrieval paper implementation.** It will look impressive and be thin. We beat it by *shipping persistence and coordination*, which is what Track 02 actually asks for.

**Where we will not be different:** per-tenant graph isolation and temporal memory. Both already exist. Both are already on the FalkorDB docs page. Claiming either as novel is the fastest way to lose a judge's trust.

---

## 3. What is actually ours

Four things, none of which exists in any system we could fetch:

1. **Continuation as a first-class artifact.** Agent B does not "get a summary"; it runs a `state` query that returns *what was tried, what failed and why, what is currently believed, and what is next*, with every item citing the event IDs it came from. This is our thesis.
2. **Coordination and memory in one graph.** The task board and the event log are the same structure. A task's lease, dependencies, outputs, and the evidence it produced are all queryable in one traversal. In every system we fetched, these are two separate systems.
3. **Proposed → confirmed inference with mandatory citation.** Causal edges are born `proposed` with cited evidence event IDs. Promotion requires an explicit rule or agent sign-off. The composer must label unconfirmed links as inferred. Nothing auto-promotes.
4. **The engine guarantee underneath #2.** FalkorDB serializes writes per graph and makes every write query atomic (verified, `docs.falkordb.com/design/concurrency`). So a single conditional `MATCH … WHERE … SET … RETURN` **is** a task lease. No external lock, no Redis `SETNX`, no separate coordination service. This is a documented engine fact, not our invention — our invention is noticing it settles the whole coordination problem.

**What to call this in the submission:** *"we take the multi-graph memory representation that the MAGMA paper validates, and add the two things a long-running investigation needs that a QA benchmark setting never exercises — cross-agent continuation and coordination."* `stuff.md` §11 already anticipated this risk; it is the right answer.

---

## 4. Research basis — every design choice and the source behind it

Verified 15 Oct 2026. Each entry was fetched, not recalled. Anything not fetched is marked.

### Representation and retrieval

| Source | Verified fact | Design choice it justifies |
|---|---|---|
| **MAGMA** — arXiv:2601.03236, *MAGMA: A Multi-Graph based Agentic Memory Architecture for AI Agents*, Jiang, Li, Li, Li, **ACL 2026 Main** | Abstract verbatim: "represents each memory item across orthogonal **semantic, temporal, causal, and entity graphs**"; "formulates retrieval as **policy-guided traversal** over these relational views, enabling query-adaptive selection"; evaluated on LoCoMo and LongMemEval | §4.2's edge families, and §6's intent-routed traversal. **This is the load-bearing citation for our architecture.** |
| **HippoRAG** — arXiv:2405.14831, NeurIPS 2024 | "synergistically orchestrates LLMs, knowledge graphs, and the Personalized PageRank algorithm"; "**up to 20%**" over SOTA on multi-hop QA; single-step retrieval "**10-30 times cheaper and 6-13 times faster**" than IRCoT | Why graph structure beats flat retrieval on multi-hop questions, and why a **single traversal step** is enough. See the caveat below. |
| **A-MEM** — arXiv:2502.12110, NeurIPS 2025 | Existing memory systems lack sophisticated organization "**despite recent attempts to incorporate graph databases**"; new memories "can trigger updates to the contextual representations of existing historical memories" | Why the graph must be *mutable*, not just a store: links are first-class and get restructured as the world changes. Justifies making edges part of the consolidation worker's job. |
| **CoALA** — arXiv:2309.02427, TMLR | Section 4.1 verbatim: "These include short-term working memory and several long-term memories: **episodic, semantic, and procedural**." Also: "Working memory maintains active and readily available information as symbolic variables for the current decision cycle" | The exact taxonomy Track 02's brief asks for. Our three memory tiers are citable to it directly. |

**Caveat on MAGMA, to be honest about:** the claims we rely on are the four views and policy-guided traversal, both in the abstract. `stuff.md` §1 #1 also claims "three logical layers are query process, data structure, write/update" — **not in the abstract, unverified**. Do not repeat the three-layer claim until someone reads the paper body. Same for the ACL Anthology ID `2026.acl-long.1709`; the arXiv page says only "ACL 2026 Main".

**Caveat on HippoRAG, and a design consequence:** FalkorDB ships **global PageRank only** — there is no Personalized PageRank procedure in its documented algorithm list. So "we run HippoRAG's PPR" would be false. The honest framing: HippoRAG motivates graph-structure-aware retrieval. FalkorDB has no personalized PageRank on any version. Do not implement PPR, and do not call `algo.pageRank` personalized. Use a bounded Cypher traversal. Ablations are cut.

### Memory across sessions

| Source | Verified fact | Design choice it justifies |
|---|---|---|
| **Generative Agents** — arXiv:2304.03442, Park, O'Brien, Cai, Morris, Liang, Bernstein | Abstract verbatim: "store a complete record of the agent's experiences using natural language, **synthesize those memories over time into higher-level reflections**, and **retrieve them dynamically to plan behavior**." Also: "by ablation… observation, planning, and reflection each contribute critically" | The three-part decomposition `Event` (records) → `Hypothesis` (reflections) → `Playbook` (higher-level). And it is the reason we **must ablate** — they showed each component matters, and we should too. |

### Coordination, handoff, and the gap we fill

This is where the research is strongest, and it was not in `stuff.md` at all. All four below were found and verified 15 Oct 2026:

| Source | Verified fact | What it means for Sheldon |
|---|---|---|
| **WorkflowOps** — arXiv:2610.07860, Cheng et al., 6 Oct 2026 | "their orchestration layers remain largely **memoryless**: each new task is decomposed, assigned, and executed from scratch with no benefit from prior successful executions." Largest gains "on structured, decomposable tasks where **past agent handoff patterns transfer**" | **Published statement of exactly our gap.** Our task board + playbooks are the opposite of this. Incident response is structured and decomposable — the regime they report the largest transfer gains in. |
| **VeriMAP** — arXiv:2510.17109, Xu, Zhang, Mitra, Hruschka | "Execution failures frequently arise not from flawed reasoning alone, but from subtle misalignments in task interpretation, output format, or **inter-agent handoffs**" | Handoff is a named failure source. Our `check_prior_attempts` and the `resume()` briefing address it directly. |
| **Veri-Sure** — arXiv:2601.19747, Liu et al. | Names "**semantic drift as intent is reinterpreted across agent handoffs**" as a bottleneck, and targets "repair hallucinations" | This is the exact failure our Design Rule 1 prevents: record events verbatim, never let Agent B reconstruct them from prose. |
| **OneVoice** — arXiv:2609.31673, Charugundla et al. | "these signals are often produced in incompatible tool-specific formats, making **agent-to-agent handoff fragile**"; an explicit shared intermediate representation "substantially improves aggregation reliability and the preservation of temporal relationships" versus "implicit agent-defined handoffs" | Independent support for **an explicit shared state structure** rather than prompt-passing. Our graph *is* that explicit structure. |

**The differentiating argument, in one paragraph:** every one of these papers treats a handoff as *passing the task along*. None of them treats a handoff as *transferring verified accumulated state*. That is the gap Sheldon fills, and it is a gap stated by the 2025–2026 literature, not one we invented.

### Evaluation

| Source | Verified fact | Use |
|---|---|---|
| **Agent Handoff F1 / Agentic Success Rate** — arXiv:2605.06457, Huang et al., PAKDD 2026 workshop | Introduces `Agent Handoff F1-Score (HF1)` and the trajectory-level `Agentic Success Rate (ASR)` decomposed into **Transition Recall and Transition Precision**; 18 LLMs, 90,000 task instances; reports "GPT-4.1 exhibits hidden workflow shortcuts despite achieving perfect TSR and HF1" | **Gives us a published handoff metric name to compute on our own data.** Report transition recall/precision for our scripted handoff scenarios. Note their caution: outcome metrics alone hide shortcuts — which is why our §9 counts *state*, not just task completion. |
| **LongMemEval** — arXiv:2410.10813 (ICLR 2025) | 500 questions, 7 question types, LLM-judge QA accuracy + Recall@k/NDCG@k; S ~115k tokens, M ~1.5M tokens | Reference only. **Do not run it and do not compare to its numbers** — 500-question scale with a specific harness, and the audit literature shows judge instability. |
| **LoCoMo** — arXiv:2402.17753 | 50 conversations, avg 300 turns, 7,512 questions; human 87.9 F1 vs best system 41.4 | Same. Also CC BY-NC — reference, never republish. |
| **MemoryAgentBench** — arXiv:2507.05257 | Four competencies: accurate retrieval, test-time learning, long-range understanding, selective forgetting | Useful framing for our question mix if time allows. |

**Verified benchmark instability, for honesty:** arXiv:2609.38021 reports re-judging the same LongMemEval answers changes labels; arXiv:2610.10265 reports final-answer scores hide stale/misattributed memory failures. This is why our eval is on our **own fixed synthetic set**, reported as raw counts, and why we never claim a leaderboard number. (All three verified in `research/v2_04`, sourced there.)

### FalkorDB engine — all from docs.falkordb.com, fetched 15 Oct 2026

| Fact | Consequence |
|---|---|
| Per-graph reader-writer model: parallel reads, **writes serialized FIFO**, **every write query atomic** (incl. schema rollback) | Single-query task lease is correct. Also fixes the event-chain fork (§5.1) |
| **No native multi-query transactions**; `MULTI`/`EXEC` "serializes all enclosed commands **across all graphs**" | **Never use MULTI/EXEC for coordination** — it stalls every investigation. Multi-step atomicity must be one query |
| `GRAPH.COPY <src> <dest>`: consistent snapshot, copies **indexes and constraints**, source stays readable, errors if dest exists. **Latency not documented** | Eval reset only. Not a novelty claim. Do not quote a copy-time number. Branch-and-merge sandboxing is cut |
| Vector index: HNSW, 1–4096 dims, `cosine`/`euclidean` only; `CALL db.idx.vector.queryNodes(label, attr, k, vecf32(...)) YIELD node, score` | Embeddings on `Event`. Note the yielded column is `node`, not `entity` |
| **Vector filters are a top-k post-cut, not a ban** | Spike B2: `WHERE` after `YIELD` runs, and recall drops outside the window. Per-investigation graphs are a good choice, not a forced one. See check.md claim 7 |
| Algorithm list is exactly BFS, SPpaths, AStar, SSpaths, MSF, pageRank, betweenness, harmonicCentrality, WCC, labelPropagation, maxFlow. `algo.CDLP` and `algo.betweennessCentrality` **do not exist on the running engine**; `algo.labelPropagation` **does**. Whole-graph algos take **no args** — `algo.WCC('S','L')` fails silently with `[]` | **EXECUTED & CORRECTED — see `research/v3_00_p0_engine_spike_findings.md`.** Use `algo.labelPropagation()` for label propagation, `algo.betweenness()` for bridging, `algo.WCC()` with no args. `algo.SPpaths` takes a map with **node references** (not ID strings). `algo.AStar` needs lat/long — it is geographic, not general A* |
| **Relationship-uniqueness limitation:** a relation not referenced elsewhere "will only verify that at least one matching relation exists" | Breaks `count()` over unaliased relationship patterns. Alias every relationship you count through |
| Indexes do **not** handle `<>` (not-equal) filters | `WHERE d.status <> 'done'` is a full scan. Fine at demo scale; know before tuning |
| **`LIMIT` does not restrict eager operations** (CREATE/SET/DELETE/MERGE/aggregations) | Never write `UNWIND … CREATE … RETURN … LIMIT n` and expect n writes |
| A mandatory `MATCH` cannot follow an `OPTIONAL MATCH` | Shapes the claim query's clause order |
| `MERGE` on a whole path duplicates nodes when the relationship is missing | One `MERGE` per clause |
| Introspection: `db.labels()`, `db.relationshipTypes()`, `db.propertyKeys()`, `db.indexes()`, `db.meta.stats()` | Schema health checks + graph stats for the demo |
| Full-text index with RediSearch syntax: `db.idx.fulltext.queryNodes(label, query)`; `%term%distance` for fuzzy | Keyword anchors for exact error strings, hostnames, IDs |

Full detail with every command quoted: `research/v2_05_falkordb_technical.md`.

### Prior art — what already exists (do not claim as novel)

**Graphiti on FalkorDB** (`graphiti-core[falkordb]`) — confirmed from `graphiti_core/edges.py` on `main`: `EntityEdge` carries `valid_at`, `invalid_at`, `expired_at` (default `None`), with `created_at` on the base `Edge`, persisted on the `RELATES_TO` relationship via `SET e = $edge_data`. Invalidation **marks, never deletes** — `_apply_temporal_invalidation` sets `resolved_edge.invalid_at` and `.expired_at`; the `DELETE e` path is never called from it. README: "old facts are invalidated — **not deleted**."

**Implication for our pitch, and this changes `stuff.md` §11:** Graphiti *does* have bi-temporal validity. Do not claim it lacks it. The defensible gap is narrower and better: **Graphiti's bi-temporality applies to entity-fact edges only.** Its `EpisodicEdge`, `CommunityEdge`, `HasEpisodeEdge` and `NextEpisodeEdge` relationships carry only `uuid`, `group_id`, `created_at` — so the episodic layer has no temporal validity interval. And it has no procedural memory, no coordination primitive, no task leasing, no speculative execution, on any page we fetched.

**mem0 on FalkorDB** (`mem0-falkordb`) — confirmed from FalkorDB docs: per-user graph isolation named `{database}_{user_id}`, `register()` runtime patch, `delete_all()` drops the user graph. So per-tenant isolation is taken too.

---

## 5. Architecture

Same as `stuff.md` §3–§4, with the three verified-fact fixes applied. The fixes are marked ⚠️ their detail is in `research/REVIEW_synapseos_architecture.md`.

### 5.1 The three fixes (all small, all load-bearing)

**Fix 1 — the event-chain fork race.** `stuff.md` §5.1 passes `$prev_seq` as a parameter. If any client computes it from a prior read, two concurrent `record_event` calls both create `NEXT` from the same event and the chain forks. Our own design guarantees concurrency (§9 specifies 2 agents, ≥3 sessions), so this will happen.

Because writes are serialized per graph and each query is atomic, the fix is to **derive `prev` from the graph inside the query**. That is race-free; a client-supplied sequence is not:

```cypher
MATCH (inv:Investigation {id: $inv})
OPTIONAL MATCH (inv)<-[:IN_INVESTIGATION]-(p:Event)
WITH inv, p ORDER BY p.ingest_seq DESC LIMIT 1
CREATE (e:Event {
  id: $id, type: $type, text: $text, ts: $ts, agent_id: $agent,
  session_id: $session, source: $source, ingest_seq: $seq,
  embedding: vecf32($embedding)
})
CREATE (e)-[:IN_INVESTIGATION]->(inv)
RETURN e.id
```
Verify the `ORDER BY … LIMIT 1` over an empty `OPTIONAL MATCH` in the P0 spike.

**Fix 2 — the claim query's blocker count.** Two documented FalkorDB limitations bite `stuff.md` §7.2:
- The relationship `DEPENDS_ON` is unaliased and feeds `count(d)`. Per the relationship-uniqueness limitation, `count(d)` can return **1 when there are 3 unfinished deps**.
- The gate still *works*: 0 deps → `count = 0` → passes; ≥1 → `≥1` → fails. **No task can be falsely claimed.** But the number is wrong, so never display it or threshold on it.

Cheap, correct form per the docs' own workaround:

```cypher
MATCH (t:Task {id: $tid})
WHERE (t.status = 'open' OR (t.status = 'claimed' AND t.lease_expires < $now))
OPTIONAL MATCH (t)-[dep:DEPENDS_ON]->(d:Task)
WHERE d.status <> 'done' AND ID(dep) >= 0
WITH t, count(d) AS blockers
WHERE blockers = 0
SET t.status = 'claimed', t.owner = $agent,
    t.lease_expires = $now + $ttl, t.version = t.version + 1
RETURN t.id, t.version
```
`d.status <> 'done'` is a `<>` filter, which indexes do not optimise — a full scan of `DEPENDS_ON` per claim. Fine at demo scale.

**Fix 3 — never `MULTI`/`EXEC` across graphs.** `stuff.md` offers it as a fallback. Docs: it "serializes all enclosed commands across all graphs". With one graph per investigation that stalls every investigation. Correct fallback for a two-step atomic need is two sequential writes, not a Redis transaction.

### 5.2 Design rules (unchanged — these are the good part)

1. **Events are ground truth; everything else is a labelled inference.** Observations, actions and results are recorded verbatim. Causal links, hypotheses, playbooks are *proposed* until validated and always shown as such. *(Supported by Veri-Sure's "semantic drift as intent is reinterpreted across agent handoffs" — verbatim reconstruction is what prevents drift.)*
2. **The graph must change what the agent receives.** Anchors from vector/keyword/time; traversal decides what enters context. Swap the graph for a flat table and get the same answer → we have failed.
3. **Measure, don't claim.** Every number in the demo comes from our own harness (§9), never from a paper or a vendor benchmark.

---

## 6. Read path

Intent → anchors → **bounded traversal** → scoring → evidence bundle → answer.

| Intent | Example | Anchors | Edge priority | Max hops |
|---|---|---|---|---|
| `timeline` | "What did we try, in order?" | time window + session | `NEXT` → `IN_SESSION` | 2–4 along `NEXT` |
| `entity` | "Everything about `checkout-svc`" | full-text / entity match | `INVOLVES` → `RELATED_TO` | 2 |
| `causal` | "Why did the rollback fail?" | vector + full-text | `CAUSED_BY`/`RESULTED_IN` → `NEXT` | 3 |
| `recall` (default) | "What do we know about the DB pool?" | vector + full-text | `RELATED_TO` → `INVOLVES` → `NEXT` | 2 |
| `state` (overlay) | "What do we believe? What's next?" | `Hypothesis` + open `Task` | `SUPPORTED_BY`/`REFUTED_BY`, `DEPENDS_ON` | 2 |

`state` is our overlay and the resumption query. It is the one no baseline can answer at all.

**The P0 question that decides whether §6 works:** can FalkorDB run `[:CAUSED_BY|RESULTED_IN*1..3]` — a multi-relationship-type variable-length pattern — at all? The cheat sheet documents single-type `[:KNOWS*1..3]`. This is the single query most likely to fail, and if it does the fallback is per-type matching unioned in application code. Spike it on day 1, before anything else is built on it.

Also fix `stuff.md` §6.4: it filters `WHERE NOT (b)-[:REJECTED]-()`, but §4.2 models rejection as `status` on the `CAUSED_BY` edge, not a `REJECTED` edge type. Use the edge status, or per-type queries.

---

## 7. Coordination

Task board lives on the **same graph** as the memory. That is the point.

- `claim_task` — the single-query atomic lease in §5.1 Fix 2. **Prove it:** N concurrent claims on one task, exactly one wins. Rehearse it before the demo; the demo's race moment is the pitch.
- `heartbeat(task)` — extend lease, conditional on `owner = $agent`.
- `complete(task, findings)` — record result `Event`s, link `PRODUCED`, update `Hypothesis`, set `done`.
- `handoff(task, to_agent, note)` — write a `decision` event with a summary, release the lease.
- `resume(investigation, agent)` — runs the `state` intent. Returns: attempted / failed-and-why / believed / next. **This is the demo's centrepiece.**
- `check_prior_attempts(task)` — causal/timeline retrieval over the task's entities, returns prior `action → result` pairs. The harness counts a *duplicated* attempt when an agent performs a semantically equal action to a prior failure without stated reason to retry.
- `$now` always comes from the service clock, never an agent's. This also sidesteps `timestamp()`'s unit being unknown.

---

## 8. What we will not claim

- "SOTA on LongMemEval / LoCoMo" — different data, different harness, and the audit literature shows judge instability.
- "Improves memory accuracy by X%" without an identical-protocol baseline on the same cases.
- "Graphiti lacks bi-temporal validity" — false.
- "Native Personalized PageRank" — FalkorDB has none.
- "Eliminates hallucinations."
- "96% token savings on graph-delta handoffs" — an unverified estimate. Measure it or drop it.
- "`GRAPH.COPY` completes in N ms" — no documented figure.
- Any number from a vendor benchmark (including GraphRAG-Bench) as if independent.
- "Memorable (YC 2026)" or any system we could not verify exists.

---

## 9. Evaluation

A fixed seeded synthetic incident: ~150–300 events, ≥3 sessions, 2 agents, ≥3 failed hypotheses with recorded reasons, a time-dependent finding, ≥1 misleading semantically-similar event, task dependencies, a confirmed resolution, and unanswerable questions. ~40 questions, split dev / held-out. Gold answers and gold evidence IDs written **before** running any system.

Systems: **S0** vector+keyword only (baseline) · **S1** + all edges, fixed traversal, no intent routing · **S2** + intent-adaptive · **S3** + task board and handoff (full Sheldon).

Metrics: answer correctness (rubric, human spot-check) · evidence-path precision/recall vs gold IDs · unsupported-claim rate · abstention accuracy · **duplicated steps** · **handoff Transition Recall / Transition Precision** (naming from arXiv:2605.06457) · latency split graph-query vs end-to-end · tokens per query.

Ablations: no causal edges · no temporal edges · no intent routing · proposed edges excluded · hand scorer vs Python PPR-style scoring. Generative Agents (arXiv:2304.03442) showed by ablation that each component contributes critically — so report what each removal costs, and expect it to cost something.

**Reporting rules:** the dataset is synthetic and small. Repeat LLM-dependent runs ≥3× and report variance. Report raw counts (`34/42`), never a bare percentage. Never cite published benchmark numbers as comparison.

---

## 10. Build gates

| Phase | Deliverable | Exit check |
|---|---|---|
| **P0 — Spike (day 1)** | FalkorDB up; indexes created; one vector, one full-text, one multi-type variable-length, one atomic-claim query all run | Every ⚠️ fact in §4 resolved or replaced. **Do not build on an unproven query.** |
| **P1 — Event memory** | Schema, ingestion with Fix 1, embeddings, `NEXT`; seeded incident; S0 baseline | Recall by timeline and similarity works; baseline numbers recorded |
| **P2 — Graph retrieval** | Entity/semantic edges, intent classifier, bounded traversal, scorer, evidence bundle | S1 > S0 on dev questions |
| **P3 — Answers with evidence** | Composer with citations, abstention, path highlighting | Unanswerable questions handled; citation checker passes |
| **P4 — Coordination** | Task board, atomic claim, lease, handoff, `resume` | **Concurrency test passes; Agent B resumes without repeating failed steps** |
| **P5 — Consolidation & causal** | Async worker, proposed causal edges, validation rules, hypotheses | Causal questions improve, or we report that they did not |
| **P6 — Procedural (thin)** | Playbook distillation + second incident | One convincing playbook retrieval |
| **P7 — Eval & demo** | S0–S3 results, ablations, README, 3-min demo | Held-out results in hand; limitations section written |

**Cut order:** P6 → P5 ablations → UI polish → MCP wrapper. **Never cut P4 or the eval.**

**Cut:** speculative branch-and-merge via `GRAPH.COPY`. The copy stays only as the eval reset (every run starts from one frozen copy). It is not a novelty claim.

---

## 11. The demo, and the one number that carries it

3 minutes: show the incident and the graph → Agent A works, records a failed hypothesis and a failed fix, a proposed causal edge appears → kill A → Agent B calls `resume()` and answers *what have we tried / why did it fail / what do we believe / what's next*, each with a highlighted evidence path, plus one "insufficient evidence" answer → two agents race for the same task, one wins → one results slide.

The results slide needs one number above all others: **duplicated steps, S0 vs S3.** "Agent B repeated 6 failed actions with plain memory, 1 with Sheldon" is the clearest possible statement of what we built, report the count we measured. Never write "nobody else measures this". It is the gap WorkflowOps (arXiv:2610.07860) names: orchestration layers that are "**memoryless**".

---

## 12. Open decisions

1. Graph scoping: per-investigation graphs (recommended, forced by the vector-filter limitation) vs one shared graph with post-filtering.
2. Embedding model and dimension — lock before creating any vector index; re-embedding means rebuilding.
3. Promotion rule for causal edges: agent-confirmed, deterministic rule, or two independent evidence events.
4. Incident scenario: non-obvious root cause, plausible-but-wrong first hypothesis.
5. Judge policy: which model, what rubric, how much human spot-checking.
6. Whether `GRAPH.COPY` sandboxing is a stretch item or dropped.
7. Verify before kickoff: hackathon rules (does main work have to start after kickoff?), schedule, and whether continuing pre-existing work is allowed.

## 13. References

- MAGMA — arXiv:2601.03236 · HippoRAG — arXiv:2405.14831 · A-MEM — arXiv:2502.12110 · CoALA — arXiv:2309.02427 · Generative Agents — arXiv:2304.03442 · WorkflowOps — arXiv:2610.07860 · VeriMAP — arXiv:2510.17109 · Veri-Sure — arXiv:2601.19747 · OneVoice — arXiv:2609.31673 · Agentic Success Rate / Agent Handoff F1 — arXiv:2605.06457 · LongMemEval — arXiv:2410.10813 · LoCoMo — arXiv:2402.17753 · MemoryAgentBench — arXiv:2507.05257
- FalkorDB docs: `docs.falkordb.com/design/concurrency`, `/cypher/cheat-sheet`, `/cypher/known-limitations`, `/cypher/indexing/vector-index`, `/algorithms/`, `/algorithms/pagerank`, `/commands/graph.copy`, `/agentic-memory/graphiti`, `/agentic-memory/mem0`
- Full research ledger and the fact-check audit: `research/00_RESEARCH_INDEX.md` and `research/v2_08_verification_audit.md`

*Everything cited above was fetched on 15 Oct 2026. Two claims are flagged as unverified and must not be repeated until checked: MAGMA's "three logical layers" and its ACL Anthology ID.*
