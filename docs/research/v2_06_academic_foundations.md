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

# Academic Foundations for Graph-Backed Agent Memory (Round 2)

**Claim prefix:** M3-  **Research date:** 2026-10-15
**Method:** arXiv abstract pages fetched directly. Titles, author lists, dates, and abstract-level claims below are quoted from the fetched pages. Claims about a paper's internal mechanism that are NOT in the abstract are marked UNVERIFIED rather than assumed.

**Sources fetched:**
- https://arxiv.org/abs/2309.02427 (CoALA)
- https://arxiv.org/abs/2405.14831 (HippoRAG)
- https://arxiv.org/abs/2502.12110 (A-MEM)

**Sources NOT fetched this pass:** Generative Agents (arXiv:2304.03442), MemoryBank, Reflexion, Voyager, ExpeL, HippoRAG 2 (arXiv:2502.14802), AriGraph. Claims about those are carried from round 1 and flagged.

---

## 1. CoALA — Cognitive Architectures for Language Agents

**arXiv:** 2309.02427 (submitted 5 Sep 2023, v1; last revised 15 Mar 2024, v3)
**Title (exact):** Cognitive Architectures for Language Agents
**Authors:** Theodore R. Sumers, Shunyu Yao, Karthik Narasimhan, Thomas L. Griffiths
**Venue:** v3 is the TMLR camera-ready version
**Subjects:** cs.AI; cs.CL; cs.LG; cs.SC

Abstract, verbatim: "we draw on the rich history of cognitive science and symbolic artificial intelligence to propose Cognitive Architectures for Language Agents (CoALA). CoALA describes a language agent with modular memory components, a structured action space to interact with internal memory and external environments, and a generalized decision-making process to choose actions."

**CORRECTION to round 1.** Round 1 (`research/02_ACADEMIC_PAPERS_AND_BENCHMARKS.md` and the round-1 fact-check) states as VERIFIED: "CoALA taxonomizes memory into Episodic, Semantic, Procedural." **The fetched abstract does not contain the words episodic, semantic, or procedural.** The abstract specifies "modular memory components, a structured action space..., and a generalized decision-making process." The three-way taxonomy is consistent with how CoALA is conventionally described and with the framing of memory as working vs episodic vs semantic vs procedural, but it is NOT verified from the page I fetched.

Treat the taxonomy as HIGH LIKELIHOOD, UNVERIFIED FROM FETCHED PAGE. Before a submission cites "CoALA's episodic/semantic/procedural taxonomy", fetch the paper's HTML full text and confirm the exact section heading and wording. Since our entire three-tier graph schema claims CoALA as its justification, this is the most important citation in the whole pitch — it must be checked against the paper body, not the abstract.

Institution attribution also matters: Griffiths and Narasimhan are Princeton faculty, but the arXiv abstract page does not state affiliations. Round 1's "Princeton" is an inference from author names, not a verified fact from the fetched page.

## 2. HippoRAG — the retrieval-method paper

**arXiv:** 2405.14831 (submitted 23 May 2024, v1; last revised 14 Jan 2025, v3)
**Title (exact):** HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models
**Authors:** Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, Yu Su
**Venue:** NeurIPS 2024
**Subjects:** cs.CL; cs.AI

Abstract, verbatim on the mechanism: "we introduce HippoRAG, a novel retrieval framework inspired by the hippocampal indexing theory of human long-term memory to enable deeper and more efficient knowledge integration over new experiences. HippoRAG synergistically orchestrates LLMs, knowledge graphs, and the Personalized PageRank algorithm to mimic the different roles of neocortex and hippocampus in human memory."

Abstract, verbatim on results: "We compare HippoRAG with existing RAG methods on multi-hop question answering and show that our method outperforms the state-of-the-art methods remarkably, **by up to 20%**. Single-step retrieval with HippoRAG achieves comparable or better performance than iterative retrieval like IRCoT while being **10-30 times cheaper and 6-13 times faster**, and integrating HippoRAG into IRCoT brings further substantial gains."

**CORRECTION to round 1.** Round 1 states as VERIFIED: "HippoRAG All-Recall@5 improves by 38.6% on 2WikiMultiHopQA vs ColBERTv2." **The fetched abstract says "up to 20%".** The 38.6% figure may appear in a results table in the paper body, but it is not in the abstract, and round 1's fact-check marked it VERIFIED citing the abstract plus OpenReview — which cannot have come from the abstract, because the abstract contains no such number.

Use "up to 20% over state-of-the-art on multi-hop QA" as the defensible headline, and "10-30x cheaper and 6-13x faster than IRCoT" as the efficiency claim, because both are in the abstract verbatim. If we want 38.6% in the pitch, fetch the paper's tables first.

What this paper gives us, precisely: PPR over a knowledge graph as a single-step, graph-algorithm-driven retrieval step, presenting the KG as the memory substrate and PPR as the activation-spread step. That is the intellectual basis for using `algo.pageRank` (or an app-level PPR) inside our retrieval path rather than vector search alone.

**Important caveat for our build (see v2_05):** FalkorDB does not ship a Personalized PageRank procedure. Its `algo.pageRank` is global PageRank. So "we run HippoRAG's PPR on FalkorDB's built-in PPR" is not accurate. The honest framing is: HippoRAG motivates graph-structure-aware retrieval. FalkorDB supplies global PageRank only. Do not implement a personalized step. Use a bounded Cypher traversal.

## 3. A-MEM — Agentic Memory for LLM Agents

**arXiv:** 2502.12110 (submitted 17 Feb 2025, v1; last revised 8 Oct 2025, v11)
**Title (exact):** A-MEM: Agentic Memory for LLM Agents
**Authors:** Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang
**Venue:** NeurIPS 2025
**Subjects:** cs.CL; cs.HCI

Abstract, verbatim on the gap: "Current memory systems enable basic storage and retrieval but lack sophisticated memory organization, **despite recent attempts to incorporate graph databases**. Moreover, these systems' fixed operations and structures limit their adaptability across diverse tasks."

Abstract, verbatim on the mechanism: "Following the basic principles of the Zettelkasten method, we designed our memory system to create interconnected knowledge networks through dynamic indexing and linking. When a new memory is added, we generate a comprehensive note containing multiple structured attributes, including contextual descriptions, keywords, and tags. The system then analyzes historical memories to identify relevant connections, establishing links where meaningful similarities exist. Additionally, this process enables **memory evolution** - as new memories are integrated, they can trigger updates to the contextual representations and attributes of existing historical memories."

**CORRECTION to round 1.** Round 1 attributes A-MEM to Rutgers. The arXiv abstract page does not list affiliations, so Rutgers is an inference from author names (Yongfeng Zhang is at Rutgers, but that is my prior knowledge, not a fact from the fetched page). Mark affiliation UNVERIFIED and either fetch the paper body or drop the institution from the pitch.

A-MEM's value to us: it is a published, peer-reviewed statement that **even graph-based memory systems have static, non-adaptive structure**, and that new memories should restructure the existing network. That is the direct academic justification for our "memory updates over time" requirement in the Track 02 brief, and for making links first-class, mutable graph edges rather than a one-time index.

## 4. Papers carried from round 1, not re-verified this pass

| Paper | Round-1 claim | Round-2 status |
|---|---|---|
| Generative Agents | arXiv:2304.03442, Stanford + Google, UIST 2023; memory stream; recency × importance × relevance; reflections compound hallucinations | NOT RE-FETCHED. Plausible and widely cited. Re-fetch before quoting the reflection-failure claim. |
| MemoryBank | arXiv:2305.10250, Ebbinghaus curve in LLM memory | NOT RE-FETCHED |
| Reflexion | verbal reinforcement memory | NOT RE-FETCHED |
| Voyager | skill library as procedural memory | NOT RE-FETCHED. This is the one we most want, because it is the academic basis for procedural memory. Re-fetch before citing. |
| ExpeL | experiential insights | NOT RE-FETCHED |
| HippoRAG 2 | arXiv:2502.14802, "From RAG to Memory", non-parametric continual learning | NOT RE-FETCHED |
| AriGraph | associative memory graph | NOT RE-FETCHED |

## 5. Graph memory vs flat memory — the argument we can actually make

This is the load-bearing paragraph of the pitch, and here is the honest version of it:

**Verified:** HippoRAG (NeurIPS 2024) demonstrates that a knowledge graph plus Personalized PageRank outperforms state-of-the-art RAG on multi-hop QA by up to 20% and is 10-30x cheaper and 6-13x faster than iterative retrieval like IRCoT. This is a peer-reviewed result showing graph structure plus a graph algorithm beats flat retrieval on multi-hop questions.

**Verified:** A-MEM (NeurIPS 2025) states that existing memory systems lack sophisticated organization "despite recent attempts to incorporate graph databases" — i.e. graph databases alone are not the answer; the memory operations have to be adaptive.

**Fair synthesis (labelled as our inference, not a paper's claim):** graph memory is necessary but not sufficient. A memory system that stores facts in a graph but cannot (a) update them without destroying history, (b) restructure links as the world changes, (c) represent reusable procedures, and (d) coordinate multiple agents, is only a graph-shaped index. That is precisely the gap between Graphiti's documented feature set (temporal episodes + per-tenant graphs) and the Track 02 brief (persist, update over time, share between agents).

**Do not claim:** that flat-vector memory is "broken" or "fails", that any paper proves graph memory is "better" in general, or that these papers evaluated multi-agent coordination. None of those is supported by the abstracts fetched.

## Claims table

| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| M3-01 | CoALA arXiv:2309.02427, title, four authors, TMLR camera ready | https://arxiv.org/abs/2309.02427 | VERIFIED | |
| M3-02 | CoALA abstract: modular memory components, structured action space, generalized decision-making | https://arxiv.org/abs/2309.02427 | VERIFIED | |
| M3-03 | CoALA taxonomizes memory as episodic / semantic / procedural | (abstract does not say this) | UNVERIFIED | Round 1 marked VERIFIED. Needs paper body. |
| M3-04 | CoALA authors are affiliated with Princeton | (abstract has no affiliations) | UNVERIFIED | Inference from author names |
| M3-05 | HippoRAG arXiv:2405.14831, NeurIPS 2024, five authors | https://arxiv.org/abs/2405.14831 | VERIFIED | |
| M3-06 | HippoRAG orchestrates LLMs, knowledge graphs, and Personalized PageRank, inspired by hippocampal indexing theory | https://arxiv.org/abs/2405.14831 | VERIFIED | |
| M3-07 | HippoRAG outperforms SOTA on multi-hop QA by up to 20% | https://arxiv.org/abs/2405.14831 | VERIFIED | |
| M3-08 | HippoRAG single-step retrieval is 10-30x cheaper and 6-13x faster than IRCoT | https://arxiv.org/abs/2405.14831 | VERIFIED | |
| M3-09 | HippoRAG improves All-Recall@5 by 38.6% on 2WikiMultiHopQA vs ColBERTv2 | (not in abstract) | UNVERIFIED — DO NOT QUOTE | Round 1 marked VERIFIED citing the abstract; the number is not there |
| M3-10 | A-MEM arXiv:2502.12110, NeurIPS 2025, six authors | https://arxiv.org/abs/2502.12110 | VERIFIED | |
| M3-11 | A-MEM uses Zettelkasten-style dynamic linking and note generation with contextual descriptions, keywords, tags | https://arxiv.org/abs/2502.12110 | VERIFIED | |
| M3-12 | A-MEM: new memories trigger updates to contextual representations of existing memories (memory evolution) | https://arxiv.org/abs/2502.12110 | VERIFIED | |
| M3-13 | A-MEM states existing memory systems lack organization "despite recent attempts to incorporate graph databases" | https://arxiv.org/abs/2502.12110 | VERIFIED | |
| M3-14 | A-MEM authors are affiliated with Rutgers | (abstract has no affiliations) | UNVERIFIED | Inference |
| M3-15 | Generative Agents arXiv:2304.03442, Stanford + Google, UIST 2023 | (not fetched) | UNVERIFIED | Carried from round 1 |
| M3-16 | MemoryBank arXiv:2305.10250 implements Ebbinghaus forgetting | (not fetched) | UNVERIFIED | Carried from round 1 |
| M3-17 | HippoRAG 2 arXiv:2502.14802 | (not fetched) | UNVERIFIED | Carried from round 1 |
| M3-18 | Voyager's skill library is procedural memory | (not fetched) | UNVERIFIED | Needed for the procedural-memory justification; re-fetch |

## Could not verify

- CoALA's exact memory taxonomy wording and section.
- All paper affiliations.
- HippoRAG's per-dataset result numbers.
- Every round-1 citation marked UNVERIFIED above.
- Any 2025-2026 paper on graph-structured agentic memory beyond HippoRAG 2, A-MEM, AriGraph — no discovery search was run this pass.

## Coordination log

- 2026-10-15 main agent. Round-2 subagent assignments were interrupted; two wrote only a header stub. Files were built from three arXiv fetches plus round-1 material.
- Round-1 file `research/02_ACADEMIC_PAPERS_AND_BENCHMARKS.md` left unmodified. Two of its VERIFIED claims are downgraded above (M3-03 and M3-09); the 38.6% HippoRAG figure is the more serious of the two because round 1's fact-check file asserted it came from the abstract.
- Highest-value next action: fetch `https://arxiv.org/abs/2309.02427` HTML full text and confirm CoALA's memory taxonomy verbatim. If the taxonomy holds, our three-tier schema has a citable foundation. If the wording differs, we adjust the schema rationale rather than the citation.
