> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# Differentiation Research: What the 2025–2026 Literature Says Our Gap Is

**Claim prefix:** D-  **Research date:** 2026-10-15
**Purpose:** establish, from sources fetched this session, what gap Sheldon occupies and what makes it different from other entries to the same hackathon brief. Complements `PLAN_SHELDON.md`.
**Method:** arXiv abstract pages and the arXiv API listing fetched directly. All quotes below are verbatim from those pages.

**Sources fetched:**
- https://arxiv.org/abs/2304.03442 (Generative Agents)
- https://arxiv.org/abs/2601.03236 (MAGMA)
- http://export.arxiv.org/api/query?search_query=abs:"agent handoff" (`totalResults: 15`, returned 8 entries)
- https://arxiv.org/abs/2405.14831, /abs/2502.12110, /abs/2309.02427 (verified in earlier passes)

---

## 1. The gap is published, not invented

Four independent papers state, in their own words, the problem Sheldon solves. This is the strongest evidence we have that we are working on something real rather than something we talked ourselves into.

| ID | Paper | Venue / date | Verbatim statement |
|---|---|---|---|
| D-01 | **WorkflowOps: Learning Agent Collaboration Priors for Multi-Agent Workflow Orchestration** — Qi Cheng, Shengyu Chen, Wei Cheng, Zhengzhang Chen, Xiaowei Jia, Haoyu Wang, Haifeng Chen · arXiv:2610.07860 | submitted 6 Oct 2026 | "their orchestration layers remain largely **memoryless**: each new task is decomposed, assigned, and executed from scratch with no benefit from prior successful executions" |
| D-02 | **VeriMAP: Verification-Aware Planning for Multi-Agent Systems** — Tianyang Xu, Dan Zhang, Kushan Mitra, Estevam Hruschka · arXiv:2510.17109 | ARR Oct submission, 20 Oct 2025 | "Execution failures frequently arise not from flawed reasoning alone, but from subtle misalignments in task interpretation, output format, or **inter-agent handoffs**" |
| D-03 | **Veri-Sure: A Contract-Aware Multi-Agent Framework…** — Jiale Liu, Taiyu Zhou, Tianqi Jiang · arXiv:2601.19747 | 27 Jan 2026 | lists "**semantic drift as intent is reinterpreted across agent handoffs**" as a bottleneck, alongside "regressions and repair hallucinations" |
| D-04 | **OneVoice: An Intermediate Representation for Agentic Speech Pipelines** — Vipul Charugundla, Dancheng Liu, Jinjun Xiong · arXiv:2609.31673 | 16 Sep 2026 | "these signals are often produced in incompatible tool-specific formats, making **agent-to-agent handoff fragile**"; an explicit shared representation "substantially improves aggregation reliability and the preservation of temporal relationships" compared to "**implicit agent-defined handoffs**" |

**The argument this supports:** every one of these papers treats a handoff as *passing the task along*. None treats a handoff as *transferring verified accumulated state through a queryable structure*. That is Sheldon's contribution, and it is a gap named by 2025–2026 literature rather than one we invented. D-01 in particular is the sentence to put on a slide verbatim.

**A second, more specific result from D-01:** the largest gains are reported "on structured, decomposable tasks where **past agent handoff patterns transfer**." Incident response is a structured, decomposable task with a short action vocabulary. Our domain choice is in the regime where this literature reports handoff-prior transfer works best — which is a reason to be confident the approach is sound, not just a reason to pick a demo that looks good.

## 2. A published handoff metric we can compute on our own data

| ID | Paper | Verified content |
|---|---|---|
| D-05 | **Beyond Task Success: Measuring Workflow Fidelity in LLM-Based Agentic Payment Systems** — Donghao Huang, Joon Kiat Chua, Zhaoxia Wang · arXiv:2605.06457 | PAKDD 2026 workshop. States that Task Success Rate and **Agent Handoff F1-Score (HF1)** "capture only final outcomes or unordered routing decisions", and introduces the **Agentic Success Rate (ASR)**, a trajectory-fidelity metric "decomposed into **Transition Recall and Transition Precision**". Applied over 18 LLMs and 90,000 task instances. Reports "GPT-4.1 exhibits hidden workflow shortcuts despite achieving perfect TSR and HF1" |

Why this matters for us, two ways:

1. **We get defensible metric names.** Report handoff **Transition Recall / Transition Precision** on our scripted scenarios rather than inventing a metric. Cite D-05 as the source of the framing.
2. **It validates measuring state, not completion.** The reported result that a model can score perfectly on outcome and handoff-F1 metrics while still skipping checkpoints is the strongest argument for Sheldon's own metric choices: count *the state of the graph after the run*, not just whether the incident got resolved.

## 3. Generative Agents — the canonical cross-session memory architecture

| Fact | Verbatim (arXiv:2304.03442) |
|---|---|
| Title | Generative Agents: Interactive Simulacra of Human Behavior |
| Authors | Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein |
| Subjects | cs.HC; cs.AI; cs.LG |
| Architecture | "store a complete record of the agent's experiences using natural language, **synthesize those memories over time into higher-level reflections**, and **retrieve them dynamically to plan behavior**" |
| Ablation result | "We demonstrate through ablation that the components of our agent architecture—observation, planning, and reflection—each contribute critically to the belieavility of agent behavior" *(sic — typo "believability" is on the arXiv page)* |

Three consequences for Sheldon:

- The three-part decomposition **records → reflections → higher-level structure** is exactly `Event` → `Hypothesis` → `Playbook`. We sit in that lineage and should cite it as such.
- Their ablation showing each component contributes critically is a *reason to run our own ablations and expect them to show a cost*. If removing causal edges costs nothing in our eval, that is a finding, not a win.
- This paper is the reason "remember across sessions" is a solved-in-principle problem and therefore **not** what we should pitch as novel.

## 4. What the search did NOT turn up — a useful negative

The arXiv API search for `abs:"agent handoff"` returned **15 total results**. None of the 8 returned describes transferring *verified accumulated state* between agents. The closest matches are:

| Paper | What it actually does | Why it is not us |
|---|---|---|
| Autonoma (arXiv:2603.19270, Reda et al.) | Hierarchical Coordinator/Planner/Supervisor workflow automation; reports "98% successful agent handoff rate" | Handoff here means *routing* the task to the right agent. No shared state transfer, no evidence graph, no memory |
| Telephony Voice Agent for Banking (arXiv:2606.28779, Dhagat et al.) | Dialogflow CX banking bot with "smooth live agent handoff for complex and out-of-scope queries" | Human handoff over telephony. Not agent-to-agent state |
| Fashion e-commerce design principles (arXiv:2607.14429, Khan et al.) | 12 candidate UX principles incl. "accountable human to agent handoff", "evidence-scoped correspondence" | Design-principle paper, no system |
| WorkflowOps, VeriMAP, Veri-Sure, OneVoice | see §1 | Handoff is the failure source or the comparator, not the mechanism |

A single-field abstract search is not an exhaustive literature review, and this is stated as **absence of evidence in one search, not evidence of absence**. But within the query we ran, the specific thing Sheldon does has no matching prior entry.

## 5. Predicted shape of the competing field

A prediction, explicitly labelled as such, derived from what the brief selects for:

| Likely submission | Why it is the obvious reading of the brief | Why it loses |
|---|---|---|
| Chat memory wrapped on FalkorDB (mem0 or Letta + graph wrapper) | "Persistent conversation history" is the most literal bullet | Fails the central-not-decorative test: the graph stores answers, never affects them |
| Graphiti + summarisation | "Temporally-aware multi-tenant graph memory" is marketed at exactly this description | Also a vendor tutorial. Beaten on coordination, not on temporality |
| Multi-agent swarm with a shared key-value store | "Share state between agents" reads as a message bus | Fails "follow connections across data" — a KV store has no hops |
| HippoRAG-style retrieval on FalkorDB | "Episodic/semantic + multi-hop" maps onto a paper | Retrieval is not memory: nothing persists, no coordination. And FalkorDB ships **global PageRank only**, so this entry burns the weekend implementing PPR before discovering it |
| A general "agent brain" that does a bit of everything | Covers all bullets superficially | Nothing demonstrably works |

## 6. Claims table

| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| D-01 | WorkflowOps states orchestration layers are "memoryless" | https://arxiv.org/abs/2610.07860 | VERIFIED | Verbatim from abstract |
| D-02 | WorkflowOps reports largest gains on structured decomposable tasks where past handoff patterns transfer | https://arxiv.org/abs/2610.07860 | VERIFIED | Verbatim from abstract |
| D-03 | VeriMAP names inter-agent handoffs as an execution-failure source | https://arxiv.org/abs/2510.17109 | VERIFIED | |
| D-04 | Veri-Sure names "semantic drift as intent is reinterpreted across agent handoffs" | https://arxiv.org/abs/2601.19747 | VERIFIED | |
| D-05 | OneVoice: agent-to-agent handoff is fragile with tool-specific formats; explicit shared representation improves reliability | https://arxiv.org/abs/2609.31673 | VERIFIED | |
| D-06 | Agentic Success Rate decomposes into Transition Recall and Transition Precision; HF1 is a named metric | https://arxiv.org/abs/2605.06457 | VERIFIED | |
| D-07 | arXiv search abs:"agent handoff" returns 15 results | http://export.arxiv.org/api/query?search_query=abs:%22agent+handoff%22 | VERIFIED | Only 8 returned; the other 7 unseen |
| D-08 | No paper in that result set transfers verified accumulated state between agents | same query | UNVERIFIED (negative) | 7 of 15 results not inspected. Absence of evidence, not evidence of absence |
| D-09 | Autonoma reports 98% agent handoff rate | https://arxiv.org/abs/2603.19270 | VERIFIED | Handoff means routing, not state transfer |
| D-10 | Generative Agents: store experiences, synthesize into reflections, retrieve to plan; ablation shows each component contributes | https://arxiv.org/abs/2304.03442 | VERIFIED | |
| D-11 | Generative Agents authors are Stanford + Google | (abstract has no affiliations) | UNVERIFIED | Inference from author names. Do not state institutions without sourcing |
| D-12 | Predictions in §5 describe what other hackathon teams will build | (no source) | OPINION | Labelled as prediction. Do not present as fact |

## 7. What this changes about our pitch

Before this pass, our differentiation rested on comparing ourselves to Graphiti and mem0 — i.e. on *what existing systems lack*. That is the weaker argument, and it was already partly wrong because Graphiti does have bi-temporal validity.

The stronger argument, now sourced: **the 2025–2026 multi-agent literature names our exact gap as an open problem**, four times over, in its own words. We are not claiming to have invented something nobody thought of; we are claiming to build the thing that WorkflowOps says is missing, VeriMAP says causes failures, Veri-Sure says causes drift, and OneVoice says needs an explicit shared representation. That is a much more defensible position and it should lead the submission rather than the feature comparison.

## Coordination log

- 2026-10-15: file created. arXiv API search for `abs:"agent handoff"` run; 8 of 15 results retrieved and assessed. Generative Agents verified in full. Findings folded into `PLAN_SHELDON.md` §4 and §11.
- Two claims downgraded from assumption to verified, and one new limitation recorded: MAGMA's "three logical layers" and its ACL Anthology ID remain unverified; the arXiv search is a 8-of-15 sample, not exhaustive.
- Open item: fetch the remaining 7 results of the arXiv `abs:"agent handoff"` query to close D-08 properly. Cost: one API call. If any of them turns out to be a graph-based state-transfer handoff, our differentiation argument needs to change and it is much better to know that now.
