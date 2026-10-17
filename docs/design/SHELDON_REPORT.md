> **Precedence:** [`facts.md`](../facts.md), [`REPORT.md`](../decisions/REPORT.md), and [`papers.md`](../engine/papers.md) override this file.
>
> **Do not quote or implement these. They were disproved:**
> - "vector queries can't combine with filters" — a `WHERE` after `YIELD` runs, but only on the top-k, so recall drops. Per-investigation graphs are a choice, not a requirement (see [`facts.md`](../facts.md)).
> - "no competitor has GRAPH.COPY" — false. It is an eval-reset method, not a novelty claim.
> - MIRIX arXiv `2501.02388` — the id is **`2507.07957`** ("MIRIX: Multi-Agent Memory System for LLM-Based Agents").
> - HippoRAG "+38.6%" — it is **+38.6 points** AR@5 on 2Wiki (37.1 → 75.7), not a relative percent.
> - any personalized-PageRank design — `algo.pageRank` is global only. Personalized PageRank does not exist.
>
> The product name is **Sheldon**. SynapseOS was an earlier name.

# Sheldon — Product Report & One-Year Build Plan

**Team:** SheldonAI — Akshat Bhaskar (lead), hariharann, Amaan Khan, Satyansh Gaur
**Origin:** Graph Hacks: Give Your AI Agents Real Context (WeMakeDevs × FalkorDB), Track 02 — Agent Memory and Coordination, Oct 15–18 2026
**Report written:** 15 Oct 2026
**Research basis:** `research/` — 94 claims, every one carrying a URL fetched this week

> **What this document is.** The hackathon builds a 48-hour proof. This document is the longer view: what Sheldon is supposed to *become*, why the research says it is worth building, and a risk-ordered plan for the twelve months after the hackathon. The MVP plan lives in `PLAN_SHELDON.md`; this file is the parent document.

---

# Part I — The Idea

## 1. One line

**Sheldon is the layer that makes an AI agent's work survive the agent.**

Agents today are amnesiac by construction. Start a new session and everything the previous one learned — what was tried, what failed, what was ruled out, what was left half-done — is either re-derived from scratch or, worse, re-introduced as a stale assumption. The handoff between two agents is a prompt dump: unstructured, unverifiable, and lossy in exactly the places where fidelity matters.

Sheldon replaces the prompt dump with a **shared, queryable, evidence-grounded graph**. An agent's work is not a transcript; it is a set of observations, actions, results, beliefs, and open tasks, each carrying the provenance of who recorded it, when, and from what source. Agent B does not receive a summary of Agent A's work. Agent B *queries* it, gets back the path behind every answer, and continues from where it stopped.

## 2. Why this is a real problem and not a feature

Four independent 2025–2026 papers state the gap in their own words. Quoted verbatim, all fetched on 15 Oct 2026:

| Source | Verbatim |
|---|---|
| **WorkflowOps** (arXiv:2610.07860, Oct 2026) | "their orchestration layers remain largely **memoryless**: each new task is decomposed, assigned, and executed from scratch with no benefit from prior successful executions" |
| **VeriMAP** (arXiv:2510.17109) | "Execution failures frequently arise not from flawed reasoning alone, but from subtle misalignments in task interpretation, output format, or **inter-agent handoffs**" |
| **Veri-Sure** (arXiv:2601.19747) | names "**semantic drift as intent is reinterpreted across agent handoffs**" as a core bottleneck |
| **OneVoice** (arXiv:2609.31673) | "agent-to-agent handoff fragile" with tool-specific formats; an explicit shared representation "substantially improves aggregation reliability and the preservation of temporal relationships" versus "**implicit agent-defined handoffs**" |

Every one of these papers treats a handoff as *passing the task along*. Not one treats a handoff as *transferring verified accumulated state through a queryable structure*. That is the space Sheldon occupies, and it is a gap named by the literature rather than one we talked ourselves into.

The hackathon brief names the same problem from the other direction: *"Agents see pieces, not the whole picture. They lose track of what happened in earlier sessions, miss how people, systems, and records relate, and can't explain why they made a choice."*

## 3. The mechanism — four ideas

### 3.1 Evidence is ground truth; everything else is a labelled inference

Observations, actions, and results are recorded **verbatim** and never rewritten. Causal links, hypotheses, and playbooks are *proposed* until validated, and are always presented as proposals.

This single rule is what prevents Veri-Sure's "semantic drift as intent is reinterpreted across agent handoffs." Agent B never reconstructs Agent A's work from prose. It reads the events. Inferences are attached to them and carry their confidence.

Concretely: a causal edge is born `proposed` with cited evidence event IDs, and is promoted to `confirmed` only by an explicit rule or an agent's sign-off. Nothing auto-promotes. The answer composer must label an unconfirmed link as inferred.

### 3.2 The graph is the index, the coordination surface, and the audit log at once

Most agent-memory systems store memory in one place and coordinate in another — a vector store plus a Redis lock, a LangGraph checkpointer plus a task queue. Sheldon puts them in one structure, because they are the same structure:

- A **task** and the **evidence it produced** are one traversal apart.
- A **lease** and the **events recorded while holding it** are one traversal apart.
- An **answer** and the **path it was derived from** are the same query.

This is why "the graph has to shape what the agent does, not sit on the side" is achievable here. The graph is not a persistence detail bolted onto the agent loop; it is the retrieval index, the shared workspace, and the provenance record simultaneously.

### 3.3 Multi-view memory

A memory is stored once and reachable through several relational views, following the multi-graph agentic memory architecture validated by **MAGMA** (arXiv:2601.03236, ACL 2026 Main): *"represents each memory item across orthogonal semantic, temporal, causal, and entity graphs"* and *"formulates retrieval as policy-guided traversal over these relational views."*

In Sheldon these are edge families over one event log: temporal (`NEXT`), entity (`INVOLVES`), semantic (`RELATED_TO`), causal (`CAUSED_BY`/`RESULTED_IN`), provenance (`IN_SESSION`), belief (`SUPPORTED_BY`/`REFUTED_BY`), coordination (`DEPENDS_ON`, `PRODUCED`). One event, many reachable paths, and the retrieval engine picks which view to traverse based on query intent.

### 3.4 Handoff as a first-class artifact

`resume(investigation, agent)` is not a summary call. It is a query that returns, with citations:

- **what was tried** — every `action` event and its `result`
- **what failed and why** — failed actions plus the hypothesis they were testing
- **what is currently believed** — open hypotheses with `SUPPORTED_BY`/`REFUTED_BY` evidence
- **what is next** — open tasks, their dependencies, and what is unblocked

This is the product. Everything else is in service of making this query correct, fast, and honest.

## 4. What the domain is, and why incident response

The field domain is **software incident response**. Agent A investigates a checkout latency spike; Agent B picks up cold, mid-session.

Why this domain:

1. **It is structured and decomposable** — which is precisely the regime where WorkflowOps (arXiv:2610.07860) reports the largest transfer gains: *"the largest gains on structured, decomposable tasks where past agent handoff patterns transfer."* The domain choice is not arbitrary; it is the regime where the literature says handoff-prior transfer works.
2. **The task vocabulary is short** — query a metric, read a log, check a deploy, form a hypothesis, test it. Short vocabularies make "did you already try this?" answerable, which is what makes the no-repeated-work metric possible.
3. **Traceability is genuinely required** — nobody accepts an incident postmortem without evidence. The product's honesty requirement matches a real professional standard, so the evaluation is not a hackathon invention.
4. **It is multi-session and multi-agent by nature** — an incident spans shifts and people.

The domain is an *entry point*, not the ceiling. Part III of this document describes generalizing past it.

## 5. Research basis

Every row below was fetched and verified on 15 Oct 2026. Nothing is recalled from memory.

| Source | Verified content | What it justifies in Sheldon |
|---|---|---|
| **MAGMA** — arXiv:2601.03236, ACL 2026 Main, Jiang/Li/Li/Li | four orthogonal views (semantic, temporal, causal, entity); "policy-guided traversal"; LoCoMo + LongMemEval | The multi-view edge families and intent-routed traversal |
| **CoALA** — arXiv:2309.02427, TMLR, Sumers/Yao/Narasimhan/Griffiths | §4.1: "short-term working memory and several long-term memories: episodic, semantic, and procedural" | The three memory tiers the hackathon brief explicitly asks for |
| **A-MEM** — arXiv:2502.12110, NeurIPS 2025, Xu et al. | memory systems lack sophistication "despite recent attempts to incorporate graph databases"; new memories "trigger updates to the contextual representations of existing historical memories" | Links are mutable, first-class, and restructured as the world changes |
| **HippoRAG** — arXiv:2405.14831, NeurIPS 2024 | "orchestrates LLMs, knowledge graphs, and the Personalized PageRank algorithm"; "up to 20%" over SOTA; "10-30 times cheaper and 6-13 times faster" than IRCoT | Why one graph traversal beats iterative retrieval, and why a single step is enough |
| **Generative Agents** — arXiv:2304.03442, Park et al. | "store a complete record of the agent's experiences… synthesize those memories over time into higher-level reflections… retrieve them dynamically to plan"; ablation shows each component contributes | The `Event` → `Hypothesis` → `Playbook` decomposition, and the obligation to ablate |
| **WorkflowOps** — arXiv:2610.07860 | orchestration layers are "memoryless"; largest gains on structured, decomposable, pattern-transferring tasks | The existence of the gap, and the domain choice |
| **VeriMAP** — arXiv:2510.17109 | failures arise from task interpretation, output format, or inter-agent handoffs | The handoff-fidelity requirement |
| **Veri-Sure** — arXiv:2601.19747 | "semantic drift as intent is reinterpreted across agent handoffs" | Design Rule 1 — record verbatim, never reconstruct |
| **OneVoice** — arXiv:2609.31673 | explicit shared representation beats "implicit agent-defined handoffs" | The graph as the explicit handoff substrate |
| **Agentic Success Rate** — arXiv:2605.06457, PAKDD 2026 | ASR decomposes into Transition Recall and Transition Precision; GPT-4.1 "exhibits hidden workflow shortcuts despite achieving perfect TSR and HF1" | Our handoff metric, and why we count graph state not just completion |
| **LongMemEval** — arXiv:2410.10813, ICLR 2025 | 500 questions, 7 question types, LLM-judge + Recall@k | Benchmark participation in Phase 3, with caveats |
| **LoCoMo** — arXiv:2402.17753 | 50 conversations, 7,512 questions, human 87.9 F1 vs best system 41.4 | Same |
| **MemoryAgentBench** — arXiv:2507.05257 | four competencies: accurate retrieval, test-time learning, long-range understanding, selective forgetting | Framing for the forgetting problem, which the MVP does not solve |

**Engine facts, from `docs.falkordb.com`, fetched 15 Oct 2026:** per-graph reader-writer model with parallel reads and serialized writes; every write query atomic; no native multi-query transactions; `GRAPH.COPY` gives a consistent snapshot and copies indexes and constraints; vector index is HNSW, 1–4096 dims, cosine/euclidean only; vector queries don't combine well with property filters (overstated: a post-filter runs on the top-k; see [`facts.md`](../facts.md)); the documented algorithm list contains no Personalized PageRank; `LIMIT` does not restrict eager write operations; indexes do not optimise `<>` filters; `MULTI`/`EXEC` serialises across all graphs. Full detail: `research/v2_05_falkordb_technical.md`.

## 6. What already exists, and what that means

**Taken — do not claim as novel:**

| System | What it already does | Source |
|---|---|---|
| **Graphiti on FalkorDB** (`graphiti-core[falkordb]`) | Temporally-aware knowledge graph. `EntityEdge` carries `valid_at`, `invalid_at`, `expired_at` (default `None`); `created_at` on the base `Edge`; persisted on `RELATES_TO` via `SET e = $edge_data`. Invalidation **marks, never deletes** — `_apply_temporal_invalidation` sets the properties and never calls the `DELETE e` path | `graphiti_core/edges.py`, `graphiti_core/utils/maintenance/edge_operations.py` on `main` |
| **mem0 on FalkorDB** (`mem0-falkordb`) | Per-user graph isolation, graphs named `{database}_{user_id}`, `delete_all()` drops the user graph, runtime-patched via `register()` | docs.falkordb.com/agentic-memory/mem0 |
| **GraphRAG SDK** | First-party FalkorDB GraphRAG with a vendor benchmark of 71.48 on GraphRAG-Bench vs 55.39 for vector RAG | docs.falkordb.com (vendor-published) |

**The precise, defensible gap.** Graphiti's bi-temporal model is real and we do not claim it lacks temporality. But its bi-temporality applies **only to entity-fact edges**. Its `EpisodicEdge`, `CommunityEdge`, `HasEpisodeEdge` and `NextEpisodeEdge` relationships carry only `uuid`, `group_id`, `created_at` — so the episodic layer has no validity interval. More importantly, on every page we fetched Graphiti has **no procedural memory, no coordination primitive, no task leasing, and no speculative execution**. And no fetched system transfers verified accumulated state between agents.

## 7. What is genuinely ours

1. **Continuation as a first-class artifact** — `resume()` returns tried / failed-and-why / believed / next, every item citing its events. No fetched system does this.
2. **Coordination and memory in one graph** — the task board is the same structure as the memory. Every fetched system separates them.
3. **Proposed → confirmed inference with mandatory citation** — inferences are born labelled and never auto-promote.
4. **The engine guarantee underneath it** — FalkorDB serializes writes per graph and makes every write query atomic, so a single conditional `MATCH … WHERE … SET … RETURN` *is* a task lease. No external lock, no separate coordination service. Documented engine fact; our contribution is noticing it settles the problem.

---

# Part II — Where the hackathon fits

The 48-hour build is **Phase 0**, not a prototype of the final product. Its job is to retire the riskiest assumption as cheaply as possible: *does the core mechanism work at all?*

**What Phase 0 must prove** (full plan in `PLAN_SHELDON.md`):

- The graph demonstrably changes retrieval — S1 beats S0 on held-out questions, and the ablation is reported whether or not it favours us.
- Cross-agent continuation works — Agent B resumes without repeating a failed step, and the count of duplicated steps is the headline number.
- Single-query atomic task leasing holds under concurrent claims, proven by test, not asserted.
- Answers are traceable and inference-labelled, with an explicit abstention path.

**What Phase 0 explicitly does not settle:** consolidation quality on real noisy data, procedural transfer between investigations, behaviour past two agents, and any scale claim. Those are Phases 1 and 2, and no amount of extra weekend work will settle them.

---

# Part III — The One-Year Plan

Sequenced by **risk retired**, not by feature list. Each phase has a gate; do not start the next phase until the gate passes.

## Phase 1 — Months 1–3 (Nov 2026 – Jan 2027): The substrate meets real data

**Thesis being tested:** the mechanism survives real, streaming, noisy data. Synthetic seeded data flatters every design.

| Deliverable | Detail |
|---|---|
| **Sheldon Core as a standalone library** | Memory substrate, retrieval engine, coordination board, and evaluation harness separated from the incident-response application. The hackathon build will not have this separation; making it is Phase 1's first job |
| **Real ingestion sources** | Git commits and PR events, CI/CD logs, deploy events, alert/paging streams. Replaces the synthetic seeded incident |
| **Entity resolution** | The main unsolved technical problem: aliasing (`checkout-svc` / `checkout` / `chk-svc`), dedup across sources, merging identities. The MVP punted on this with a `MERGE` and a name |
| **Contradiction handling** | What happens when two sources disagree about the same fact within minutes. A-MEM (arXiv:2502.12110) says memories must "trigger updates to the contextual representations of existing historical memories" — this is where that becomes a real implementation problem |
| **Architecture debt cleared** | The three verified Cypher fixes (event-chain fork race, claim-query blocker count, `MULTI`/`EXEC` trap) become tests, not fixes |
| **Second domain** | Port to one non-incident domain to prove generality. Candidates: customer-support escalation (two support agents across shifts), or codebase archaeology (who changed this and why) |

**Gate:** Sheldon Core ingests a real incident from live sources without manual seeding; entity resolution is measured (precision/recall against a hand-labelled set); the S1 > S0 result survives the switch from synthetic to real data. **If it does not survive, stop and fix retrieval before adding anything.**

**Risk retired:** does consolidation hold up on noisy data? This is the biggest single unknown in the project.

## Phase 2 — Months 4–6 (Feb – Apr 2027): Coordination depth and procedural transfer

**Thesis being tested:** coordination generalises past two agents, and procedural memory actually transfers.

| Deliverable | Detail |
|---|---|
| **N-agent coordination** | Delegation graphs, not a pairwise pair. Agent rosters, capability matching, and WorkflowOps-style collaboration priors (arXiv:2610.07860) as soft guidance for task assignment |
| **Handoff fidelity as a measured property** | Transition Recall / Transition Precision (arXiv:2605.06457) on scripted handoff scenarios, computed on our own suite. The 2026 finding that a system can score perfectly on outcome and handoff-F1 metrics while still skipping checkpoints is the reason we count **state**, not completion |
| **Procedural transfer** | The research question: does a playbook distilled from a resolved incident improve the next one? Must be measured against a control with no playbook. If it does not transfer, say so and shrink the claim |
| **Learned vs hand-scored traversal policy** | The hand scorer is a documented stand-in for MAGMA's policy-guided traversal. This is where a learned router becomes the headline ablation: does it beat the intent classifier we hard-code in the MVP? |
| **Forgetting** | MemoryAgentBench (arXiv:2507.05257) names *selective forgetting* as one of four competencies. The MVP appends forever. This month adds decay, consolidation, and a measured answer to "when should Sheldon forget?" |

**Gate:** an N-agent investigation completes on real data; handoff fidelity is measured with the Transition Recall/Precision metric; procedural transfer shows a measurable delta against a no-playbook control (positive or negative, reported honestly); the learned-policy ablation has a result.

**Risk retired:** does coordination generalise, and does procedural memory transfer? If procedural transfer fails, Sheldon is still a memory and coordination substrate — it just is not a learning system, and that is a much smaller claim.

## Phase 3 — Months 7–9 (May – Jul 2027): Evaluation at scale, publication, open source

**Thesis being tested:** the work holds up under other people's scrutiny.

| Deliverable | Detail |
|---|---|
| **Honest benchmark participation** | Run LongMemEval (arXiv:2410.10813) and LoCoMo (arXiv:2402.17753) with the documented harness and judge configuration. Report with the caveats the literature demands — arXiv:2609.38021 shows re-judging the same answers changes labels, and arXiv:2610.10265 shows final-answer scores hide stale-memory failures. Never claim a leaderboard position we did not earn |
| **Public evaluation suite** | Our own fixed scenarios, gold answers, and harness, published so others can reproduce. The inability to reproduce is why so many agent-memory claims are noise |
| **Open source the core** | Memory substrate, retrieval engine, coordination board, harness. The incident-response application can stay closed |
| **Technical write-up** | The blog post or paper. Lead with the four verbatim literature quotes and the handoff-fidelity result, not with a feature list |
| **Community** | FalkorDB Discord and the wider graph-RAG community. FalkorDB is small enough that a genuinely novel integration gets seen |

**Gate:** Holden-Core repo is public with a passing test suite and a reproducible evaluation; benchmark participation is reported with limitations stated; at least one external person has run it.

**Risk retired:** does it hold up to outside scrutiny? Everything before this phase is self-reported.

## Phase 4 — Months 10–12 (Aug – Oct 2027): Production hardening and integrations

**Thesis being tested:** it can be deployed and depended on.

| Deliverable | Detail |
|---|---|
| **Multi-tenancy and auth** | Per-tenant graphs, access control, isolation guarantees. The MVP's graph-per-investigation scoping is a choice. A vector filter runs after the top-k cut (see [`facts.md`](../facts.md)); it does not force a graph per investigation. At scale this still needs a deliberate answer |
| **Scale characterisation** | FalkorDB's documented model serializes writes per graph — a verified, structural ceiling. Characterise the real throughput ceiling on Sheldon's write pattern, batch where possible, and publish the number rather than discovering it in production |
| **Cost model** | LLM calls sit in the consolidation worker, not the hot path. Quantify cost per investigation and make it a measured, reportable number |
| **SDK and integrations** | MCP server, LangGraph/LlamaIndex adapters, and the client libraries for the languages our users actually use |
| **Deployment** | Self-host Docker, Helm chart, and a hosted option. FalkorDBLite for embedded use |
| **Observability** | Query profiling via `GRAPH.PROFILE`/`GRAPH.EXPLAIN` surfaced as first-class product telemetry, not a debugging afterthought |

**Gate:** a multi-tenant deployment runs for two weeks unattended; the throughput ceiling is characterised and published; an outside team can install it from documentation alone.

---

## Risk register

| Risk | Likelihood | Why it matters | Mitigation / phase |
|---|---|---|---|
| Consolidation quality collapses on real data | **High** | LLM extraction errors compound: a wrong entity edge is worse than no edge because it silently poisons retrieval | Phase 1 measures entity resolution explicitly; deterministic regex extraction runs *before* the LLM |
| Procedural memory does not transfer | Medium | It is one of three required memory tiers in the brief | Phase 2 measures it against a control; shrink the claim if it fails |
| Hand scorer does not scale | Medium | The intent-routed traversal is hand-tuned on ~40 questions | Phase 2 learns the routing policy and ablates it against the hand scorer |
| Write throughput ceiling | **High** | FalkorDB serializes writes per graph — a documented structural limit, not a bug to work around | Phase 4 characterises it; batch consolidation into single queries |
| Benchmark results show no gain over simpler systems | Medium | Plausible: the field's own audit literature says final-answer metrics hide memory failures | Phase 3 reports our own handoff-fidelity and state-correctness metrics, which is where the mechanism should show |
| Cost per investigation is unacceptable | Medium | LLM calls in the consolidation path | Consolidation is off the hot path; measure cost per investigation in Phase 4 |
| Scope drift into "general agent OS" | **High** | Kills every project this shape | Phase gates; the out-of-scope list in `PLAN_SHELDON.md` is binding |
| The evaluation is not trusted | Medium | Every claim is self-reported until Phase 3 | Publish the harness, gold data, and judge configuration in Phase 3 |

## What would make us stop

Stated now, so the decision is made calmly rather than in month seven:

- **If S1 does not beat S0 on real data in Phase 1.** The graph is not doing work. Fix it or stop.
- **If handoff fidelity shows no delta against a no-memory control in Phase 2.** The product's central claim is unmeasured.
- **If procedural transfer fails *and* the coordination story does not carry a submission on its own.** That leaves a competent conventional system, which is not worth a year.

---

## Milestone summary

| Phase | Months | Core question | Gate artefact |
|---|---|---|---|
| **0 — Hackathon** | Oct 2026 (48h) | Does the mechanism work at all? | Working demo, S0–S3 numbers, resumption + race test passing |
| **1 — Real data** | 1–3 | Does consolidation survive noise? | Core library, real ingestion, entity-resolution precision/recall |
| **2 — Depth** | 4–6 | Does coordination generalise? Do playbooks transfer? | N-agent run, Transition Recall/Precision, procedural delta |
| **3 — Scrutable** | 7–9 | Does it survive outside scrutiny? | Public repo, reproducible harness, reported benchmark participation |
| **4 — Deployable** | 10–12 | Can it be depended on? | Multi-tenant deployment, characterised throughput ceiling, docs |

## The one number that decides everything

Across all four phases the metric that matters is **handoff fidelity measured as graph state, not task completion**: after Agent B resumes, does the graph contain the same facts, the same open hypotheses, and the same set of not-yet-tried actions that Agent A left?

Agentic Success Rate (arXiv:2605.06457) exists precisely because outcome metrics hide this. If that number is good at Phase 2, Sheldon is a real contribution. If it is not, nothing else in this plan rescues it.

---

## Appendix — File map

| File | Contents |
|---|---|
| `PLAN_SHELDON.md` | The 48-hour MVP plan: problem-statement checklist, competing-field prediction, build gates P0–P7 |
| `research/00_RESEARCH_INDEX.md` | Master ledger — 10 research files, 94 sourced claims |
| `research/v2_05_falkordb_technical.md` | FalkorDB ground truth, every command quoted from a fetched page |
| `research/v2_10_differentiation_research.md` | The gap the literature names; predicted competing field |
| `research/v2_09_critical_claim_verification.md` | CoALA taxonomy and Graphiti bi-temporal model verified to source |
| `research/v2_04_benchmarks_and_evaluation.md` | Benchmarks, their instability, and the honest 48-hour evaluation plan |
| `research/v2_08_verification_audit.md` | Audit of every claim, including round-1 errors caught and corrected |

### Verified sources

**Papers:** MAGMA arXiv:2601.03236 · CoALA arXiv:2309.02427 · A-MEM arXiv:2502.12110 · HippoRAG arXiv:2405.14831 · Generative Agents arXiv:2304.03442 · WorkflowOps arXiv:2610.07860 · VeriMAP arXiv:2510.17109 · Veri-Sure arXiv:2601.19747 · OneVoice arXiv:2609.31673 · Agentic Success Rate arXiv:2605.06457 · LongMemEval arXiv:2410.10813 · LoCoMo arXiv:2402.17753 · MemoryAgentBench arXiv:2507.05257 · MultiAgentBench arXiv:2503.01935

** FalkorDB docs:** `/design/concurrency` · `/cypher/cheat-sheet` · `/cypher/known-limitations` · `/cypher/indexing/vector-index` · `/algorithms/` · `/commands/graph.copy` · `/agentic-memory/graphiti` · `/agentic-memory/mem0`

**Two claims flagged unverified and not to be repeated until checked:** MAGMA's "three logical layers (query process, data structure, write/update)" and its ACL Anthology ID `2026.acl-long.1709`. Neither is in the abstract; the identifier comes from `stuff.md`, not from a fetched page.

*All sources above were fetched 15 Oct 2026. Re-verify anything before publishing it.*
