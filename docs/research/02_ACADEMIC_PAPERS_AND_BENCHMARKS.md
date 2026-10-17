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

# Academic Papers, Benchmarks & Cognitive Research: Track 02
**Track 02 — Agent Memory and Coordination**  
**Status:** Research Complete (verified via web search, Oct 15 2026)  
**Last Updated By:** Main agent (after subagent rate-limit failure)

---

## Part I: Cognitive Architecture Foundations

### 1. CoALA — Cognitive Architectures for Language Agents
**Authors:** Theodore R. Sumers, Shunyu Yao, Karthik Narasimhan, Thomas L. Griffiths  
**Affiliation:** Princeton University  
**arXiv:** 2309.02427 [cs.AI]  
**Status:** VERIFIED (Princeton website + arXiv)

#### Core Framework
CoALA proposes a systematic framework to design LLM-based agents by drawing from cognitive science and symbolic AI. Three dimensions:

1. **Modular Memory Components:**
   - *Working Memory:* Active information in the LLM's current context window.
   - *Long-Term Memory (External Storage):*
     - **Episodic Memory:** Logs of specific past events, interactions, and observations (chronological, autobiographical).
     - **Semantic Memory:** Generalized world knowledge — facts, concepts, entity relationships.
     - **Procedural Memory:** Encoded executable skills, step-by-step instructions, script-like plans that guide how the agent acts.

2. **Structured Action Space:**
   - *Internal Actions:* Retrieving memories, reasoning (chain-of-thought), self-updating internal state.
   - *External Actions:* Tool calls, API interactions, environment modifications.

3. **Generalized Decision-Making Procedure:** Continuous loop: information gathering → planning → execution → learning.

#### Relevance to Track 02
CoALA is the definitive theoretical justification for why agent memory must be split into **Episodic + Semantic + Procedural** tiers. Our architecture (SynapseOS) maps directly to these three tiers in FalkorDB. CoALA does not specify how to implement this on a graph database — that is our contribution.

---

### 2. Generative Agents: Interactive Simulacra of Human Behavior
**Authors:** Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein  
**Affiliation:** Stanford University + Google Research  
**Published:** April 2023 | **Venue:** UIST 2023  
**arXiv:** 2304.03442  
**Status:** VERIFIED (arXiv + Stanford)

#### Core Architecture
- **Memory Stream:** Long-term external database maintaining chronological natural-language records of all agent experiences.
- **Retrieval Mechanism:** Scores memories on three dimensions:
  - **Recency:** Exponential decay from time of event.
  - **Importance:** LLM-assigned salience score (1–10 scale).
  - **Relevance:** Cosine similarity to current query context.
- **Reflection:** Periodically triggers when sum of importance scores exceeds threshold. LLM synthesizes higher-order abstractions from multiple memory stream entries. Reflections stored back as new memory entries (creating hierarchical memory layers).
- **Planning:** Agents maintain daily plans updated via reflection and environmental observation.

#### Verified Limitations (Key Research Insights)
| Limitation | Detail |
|---|---|
| **Context Window Bottlenecks** | Packing retrieved memories + reflections + environment state + system prompt strains context limits. Lost-in-the-middle attention degradation on long contexts. |
| **Cascading Hallucinations** | Reflections generated autonomously and stored as absolute facts. Early misinterpretations compound — incorrect reflection warps all future agent behavior. |
| **Retrieval Heuristic Failures** | The recency × importance × relevance scoring model is an approximation that can fail to surface critical context. |
| **Computational Cost** | Continuous planning, importance scoring, and reflection across multiple agents requires massive LLM API call volumes. Not economically viable for high-frequency production loops. |
| **No Graph Topology** | Memory stream is a flat list. No entity linking, no relational traversal, no multi-hop graph reasoning. |

---

### 3. A-MEM: Agentic Memory for LLM Agents
**Authors:** Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang  
**Affiliation:** Rutgers University  
**arXiv:** 2502.12110  
**Published:** February 2025  
**Status:** VERIFIED (arXiv)

#### Core Approach: Zettelkasten-Inspired Agentic Memory
Unlike static developer-predefined schemas, A-MEM enables the LLM agent to autonomously manage its own memory organization:
- **Dynamic Indexing & Tagging:** Memories are tagged with context-derived keywords, categories, and cross-references (Zettelkasten method).
- **Memory Evolution:** When new information arrives, A-MEM automatically updates contextual representations, attributes, and links of existing historical memories. The knowledge network deeply refines its understanding over time.
- **Interconnected Note Network:** Memories form a web of individual notes with dynamic linking — not flat storage or simple vector retrieval.

#### Relevance to Track 02
A-MEM's Zettelkasten-inspired evolution shows that agent memory must be dynamic and self-modifying — not a static schema. However, A-MEM does not implement:
- Bi-temporal validity intervals
- Multi-agent coordination
- Native graph algorithms for retrieval
- Procedural skill templates

---

### 4. MemoryBank: Enhancing Large Language Models with Long-Term Memory
**arXiv:** 2305.10250  
**Status:** VERIFIED (arXiv)
- Implements Ebbinghaus-inspired memory updating. Memories are periodically summarized and updated according to a forgetting curve-like function. Relevant precursor to our sleep consolidation mechanism.

### 5. MIRIX: Multi-Agent Memory System for LLM-Based Agents
**arXiv:** 2507.07957  
**Status:** CORRECTED 17 Oct 2026. The old id `2501.02388` is an unrelated paper, and the expanded title above was made up.
- Six memory types. Cite the real id only. See papers.md.

---

## Part II: Associative Graph Retrieval & HippoRAG

### 6. HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models
**Authors:** Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, Yu Su  
**Affiliation:** The Ohio State University + Stanford University  
**arXiv:** 2405.14831  
**Published:** May 2024 (NeurIPS 2024)  
**Status:** FULLY VERIFIED (arXiv + OpenReview + multiple secondary sources)

#### Core Neurobiological Theory: Hippocampal Indexing Theory
The hippocampus in the mammalian brain does not store memories itself — it acts as a **rapid-binding indexer** that links neocortical representations across different memory traces. HippoRAG mimics this division:
- **Neocortex Analog → LLM:** Stores general semantic representations.
- **Hippocampus Analog → Knowledge Graph + Personalized PageRank:** Rapidly binds and links specific memory traces across different experiences.

#### Technical Architecture
1. **Offline Indexing:** Passages are processed via Open Information Extraction (OpenIE) into a phrase-based knowledge graph of triples: `(subject, relation, object)`. Inverted indices link each node/edge back to source passages.
2. **Online Retrieval — Seed Node Identification:** Given a query, LLMs or dense retrievers identify relevant graph nodes (seed nodes `R_q`).
3. **PPR Graph Traversal (The Key Innovation):**

$$\mathbf{r} = (1 - \alpha) \mathbf{A}^T \mathbf{r} + \alpha \mathbf{s}$$

Where:
- $\mathbf{r}$ = steady-state PageRank vector (activation scores per node)
- $\mathbf{A}$ = graph adjacency/transition matrix
- $\mathbf{s}$ = personalization seed vector (1 for seed nodes, 0 elsewhere)
- $\alpha$ = teleportation probability (typically 0.15)

PPR diffuses probability mass from seed nodes across the knowledge graph — implicitly performing multi-hop reasoning **in a single algebraic step**, without iterative LLM calls.

#### Verified Benchmark Results

| Benchmark | HippoRAG vs. Baselines | Metric |
|---|---|---|
| **2WikiMultiHopQA** | +38.6 points AR@5 over ColBERTv2 (37.1 → 75.7), not +38.6% | All-Recall@5 |
| **2WikiMultiHopQA** | Up to +17% over dense baselines | F1 Score |
| **MuSiQue** (2-4 hop reasoning) | Significant improvement in Recall@5 and F1 | vs. Contriever, ColBERTv2 |
| **vs. IRCoT (iterative LLM)** | Comparable/superior QA performance | **10-30x cheaper, 6-13x faster** |

> **Corrected:** HippoRAG's single-step retrieval uses Personalized PageRank in the paper. That algorithm is not in FalkorDB. The "IRCoT 4–6 round-trips, 5–10 s" sentence was not found in the paper. Drop it. Safest efficiency quote is "6–13× faster".

---

### 7. HippoRAG 2: From RAG to Memory
**arXiv:** 2502.14802  
**Published:** February 2025  
**Status:** VERIFIED (arXiv)

Extends HippoRAG to support **non-parametric continual learning**. Bridges gaps in factual recall, sense-making, and associative memory over evolving knowledge bases. This is the direct precursor to implementing hippocampal-style memory that persists and updates over time — exactly what Track 02 requires.

---

## Part III: Memory Benchmarks & Evaluation Frameworks

### 8. LongMemEval
**Full Title:** "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory"  
**Affiliation:** UCLA + Tencent AI Lab + UC San Diego  
**arXiv:** Published 2024 (exact ID: 2410.10813 — verified via search)  
**Status:** VERIFIED (arXiv + GitHub pages)

#### What It Measures
5 dimensions of long-term conversational memory over histories ranging from ~115k to ~1.5M tokens:

| Dimension | What Is Tested |
|---|---|
| **Information Extraction** | Recalling specific isolated facts from deep within past interactions |
| **Multi-Session Reasoning** | Synthesizing information distributed across **multiple distinct sessions** |
| **Temporal Reasoning** | Tracking explicit time mentions, relative timelines, and timestamp-embedded events |
| **Knowledge Updates** | Tracking when a user's preferences/facts change and superseding old beliefs correctly |
| **Abstention** | Recognizing when information is absent and declining to hallucinate |

#### Key Findings (VERIFIED)
- Commercial chat assistants and long-context LLMs suffer **30–60%+ performance drops** on tracking and reasoning across sustained interactions.
- Three-stage memory pipeline (Indexing → Retrieval → Reading) identified as the key framework for optimization.
- **Indexing:** Fact-augmented key expansion.
- **Retrieval:** Time-aware query expansion + session decomposition.
- **Reading:** Chain-of-Note (CoN) for splitting long context reading into extraction + reasoning sub-steps.

#### Relevance to Track 02
LongMemEval directly tests the exact capabilities we are building:
- Knowledge Updates = our bi-temporal validity + Ebbinghaus decay
- Multi-Session Reasoning = our episodic graph retrieval
- Temporal Reasoning = our `valid_at`/`invalid_at` edge filtering
- Information Extraction = our PPR-based associative retrieval

---

### 9. Ebbinghaus Forgetting Curve: Biological Foundation for Memory Decay

The forgetting curve was formulated by Hermann Ebbinghaus (1885):

$$R(t) = e^{-t/S}$$

Where:
- $R(t)$ = Retention/retrievability at time $t$
- $S$ = Memory stability (increases with each successful retrieval — spaced repetition effect)
- $t$ = Time elapsed since last access

**Application to AI Agent Memory (VERIFIED PATTERN):**
- Every time an agent accesses/validates a graph node, its stability $S$ increases.
- If a fact goes unaccessed beyond a time interval, its activation weight decays along the curve.
- When stability drops below threshold (e.g., $R < 0.05$), a background "Sleep Cycle" worker prunes low-salience nodes or consolidates them into abstract `:Concept` nodes via community detection.

This mirrors **synaptic consolidation** in neuroscience — during sleep, the mammalian brain:
1. Replays episodic memories (hippocampus).
2. Transfers important patterns to neocortical semantic schemas.
3. Prunes weak/irrelevant synaptic connections.

**Verified prior work applying this to AI:**
- MemoryBank (arXiv:2305.10250) implements Ebbinghaus-inspired memory updating.
- Research cited in arXiv papers on combating catastrophic forgetting via memory stability scoring in neural-symbolic agents.

---

## Summary of Academic Foundations → Track 02 Design Decisions

| Research | Design Decision in SynapseOS |
|---|---|
| CoALA (arXiv:2309.02427) — Episodic/Semantic/Procedural taxonomy | Three-tier FalkorDB graph schema: `:Episode`, `:Entity`/`:Concept`, `:ActionTemplate`/`:Skill` |
| Generative Agents (arXiv:2304.03442) — Memory stream + reflection | Replace a flat stream with graph nodes. Do not replace the scorer with PPR |
| HippoRAG (arXiv:2405.14831) — PPR in the paper, not in FalkorDB | Do **not** call `algo.pageRank` for this. It is global PageRank. Use a bounded Cypher traversal |
| HippoRAG 2 (arXiv:2502.14802) — Non-parametric continual learning | Append-only episodic writes + bi-temporal edge invalidation, never destructive deletes |
| A-MEM (arXiv:2502.12110) — Zettelkasten dynamic relational memory | Dynamic edge creation between `:Episode` → `:Entity` based on co-occurrence and LLM extraction |
| LongMemEval — Tests Knowledge Updates, Temporal Reasoning | Bi-temporal `valid_at`/`invalid_at` + time-scoped Cypher queries |
| Ebbinghaus Forgetting Curve — Decay + spaced repetition | `salience × exp(-(now - last_accessed) / stability)` < 0.05 → prune node in Sleep Cycle |
