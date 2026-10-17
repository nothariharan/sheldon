> **Precedence:** [`facts.md`](../facts.md), [`REPORT.md`](../decisions/REPORT.md), and [`papers.md`](../engine/papers.md) override this file.

# Agent Memory Benchmarks and Evaluation (Round 2)

**Claim prefix:** M4-

Research target: what agent-memory evaluation actually exists, and what a 48-hour hackathon build (Track 02, Agent Memory and Coordination on FalkorDB, WeMakeDevs x FalkorDB Graph Hacks, Oct 15-18 2026) can honestly run. All numbers below are marked "reported in <source>"; nothing here is our own measurement.

## LongMemEval

- What it measures: five core long-term memory abilities of chat assistants, tested through seven question types: information extraction (single-session-user, single-session-assistant, single-session-preference), multi-session reasoning (MR), knowledge updates (KU), temporal reasoning (TR), and abstention (ABS, built from 30 "false premise" questions modified from other types). Requires online processing of a length-configurable user-assistant history, then answering.
- Dataset size: 500 curated questions embedded in freely scalable chat histories. Two standard settings reported in the paper: LongMemEvalS (~115k tokens per problem, roughly 50 sessions) and LongMemEvalM (500 sessions, ~1.5M tokens). Questions were human-filtered/rewritten; ontology of 164 user attributes.
- Models or systems tested: pilot commercial systems ChatGPT (GPT-4o, GPT-4o-mini) and Coze (GPT-4o, GPT-3.5-turbo) on 97 questions with 3-6 session histories; long-context LLMs GPT-4o, Llama 3.1 Instruct 70B and 8B, Phi-3 128k Instruct (14B), Phi-3.5 Mini Instruct (4B) on LongMemEvalS; more LLMs in Appendix E; dense retriever Stella V5 1.5B used in their memory design experiments.
- Exact metric names: QA accuracy judged by an LLM evaluator (gpt-4o-2024-08-06 via OpenAI API, reported in the paper as >97% agreement with human experts); retrieval metrics Recall@k and NDCG@k where k is the number of retrieved items.
- Reported baseline numbers (all "reported in arXiv:2410.10813v2"): offline reading with full history: GPT-4o 0.9184 accuracy; online-memory ChatGPT GPT-4o 0.5773 (37% drop vs offline), ChatGPT GPT-4o-mini 0.7113; Coze GPT-4o 0.3299 (64% drop), Coze GPT-3.5-turbo 0.2474. Long-context LLMs on LongMemEvalS, oracle (evidence sessions only) vs full-history (S): GPT-4o 0.870 -> 0.606 (30.3% drop); Llama 3.1 70B 0.744 -> 0.334 (55.1%); Llama 3.1 8B 0.710 -> 0.454 (36.1%); Phi-3 128k 0.702 -> 0.380 (45.9%); Phi-3.5 Mini 0.660 -> 0.342 (48.1%). With Chain-of-Note: GPT-4o 0.924 -> 0.640 (30.7%); Llama 70B 0.848 -> 0.286 (66.3%). Abstract headline: commercial assistants and long-context LLMs show a 30% accuracy drop on memorizing information across sustained interactions; intro states 30-60% performance drop on LongMemEvalS for long-context LLMs. Their design optimizations: fact-augmented key expansion +9.4% recall@k and +5.4% QA accuracy; time-aware query expansion +6.8-11.3% temporal-reasoning recall; Chain-of-Note plus structured format up to +10 QA accuracy points.
- Source URL: https://arxiv.org/abs/2410.10813 (ICLR 2025; code at https://github.com/xiaowu0162/LongMemEval as cited in the paper)

## LoCoMo

- What it measures: very long-term conversational memory of LLM agents, via three tasks: (1) QA with five reasoning categories, single-hop, multi-hop, temporal reasoning, open-domain knowledge, and adversarial (unanswerable questions where the correct behavior is abstaining); (2) event summarization against the grounding temporal event graph; (3) multi-modal dialogue generation. Conversations grounded in personas and temporal event graphs, human-verified/edited.
- Dataset size: 50 long-term dialogues; average 304.9 turns, 19.3 sessions, 9,209.2 tokens per conversation (up to 35 sessions). Benchmark QA totals 7,512 questions: 2,705 single-hop (36%), 1,104 multi-hop (14.6%), 1,547 temporal (20.6%), 285 open-domain (3.9%), 1,871 adversarial (24.9%), as reported in the paper's Appendix B dataset statistics. Event summarization: average 24.2 ground-truth events per conversation. License CC BY-NC 4.0 (non-commercial).
- Models or systems tested: base LLMs Mistral-Instruct-7B (8K), Llama-2-Chat-70B (4,096), GPT-3.5-turbo (4,096), GPT-4-turbo (4,096); long-context GPT-3.5-turbo-16K at 4K/8K/12K/16K effective dialog; RAG variants (DRAGON retriever, gpt-3.5-turbo-16k reader) over dialog, observation, and summary retrieval units with top-k 5/10/25/50 (summary: 2/5/10); a human reference row; MiniGPT-5 variants for the multimodal task.
- Exact metric names: answer-prediction F1 (per category and overall); Recall@k for retrieval context accuracy; event summarization: ROGUE-1, ROGUE-2, ROGUE-L and FactScore precision, recall, F1 (paper writes "ROGUE"; the standard metric is ROUGE, the paper's table header says ROGUE); multimodal: MMRelevance plus other NLG metrics.
- Reported baseline numbers (all "reported in arXiv:2402.17753v1"): human overall QA F1 87.9. Best base model GPT-4-turbo overall 32.1 (text says 32.4; Table 2 value is 32.1). Long-context GPT-3.5-turbo-16K overall 37.8 at 16K, but adversarial F1 collapses to 2.1 (vs 70.2 for GPT-4-turbo 4K, 22.1 Llama-2-Chat-70B). Best RAG (observation-based, top-5) overall F1 41.4; dialog RAG top-50 overall 34.8 with recall@50 84.8; summary RAG top-10 F1 31.5 with recall 90.7. Headline findings reported in the paper: long-context LLMs/RAG improve QA 22-66% over base but still lag human by 56% (temporal by 73%); long-context models are 83% lower than base on adversarial questions; event summarization best FactScore F1: GPT-3.5-turbo incremental 45.9, GPT-4-turbo 45.1; long-context summarization declines vs base (precision -3.0, recall -8.7 per the paper text).
- Source URL: https://arxiv.org/abs/2402.17753 (project page https://snap-research.github.io/locomo/ as cited in the paper)

## Mem0 (system evaluation on LoCoMo)

- What it measures: a memory architecture (extract/consolidate/retrieve) and a graph-based memory variant, evaluated on four LoCoMo question categories: single-hop, temporal, multi-hop, open-domain.
- Models or systems tested: six baseline categories, memory-augmented systems, RAG with varying chunk sizes and k-values, a full-context approach, an open-source memory solution, a proprietary model system, and a dedicated memory management platform, per the abstract.
- Exact metric names: LLM-as-a-Judge (as named in the abstract); p95 latency; token cost.
- Reported baseline numbers (all "reported in arXiv:2504.19413"): Mem0 achieves 26% relative improvement in the LLM-as-a-Judge metric over OpenAI; Mem0 graph variant about 2% higher overall score than base Mem0; Mem0 attains 91% lower p95 latency and saves more than 90% token cost vs the full-context method.
- Source URL: https://arxiv.org/abs/2504.19413

## MemoryAgentBench

- What it measures: four core competencies of memory agents, accurate retrieval, test-time learning, long-range understanding, and selective forgetting, in incremental multi-turn interaction format (existing long-context datasets plus newly constructed datasets converted to multi-turn form).
- Dataset size: UNVERIFIED exact question counts from this pass (abstract does not state a total; the paper transforms existing datasets). Submitted 7 Jul 2025, last revised 28 Jun 2026.
- Models or systems tested: "context-based and retrieval-augmented generation (RAG) systems to advanced agents with external memory modules and tool integration", per the abstract (exact roster not captured).
- Exact metric names: UNVERIFIED beyond the four competency framing (metric table not fetched).
- Reported baseline numbers: no headline numbers captured; paper conclusion reported in the abstract is that current methods fall short of mastering all four competencies.
- Source URL: https://arxiv.org/abs/2507.05257

## MultiAgentBench (closest public work to multi-agent coordination evaluation)

- What it measures: collaboration and competition of LLM agents across interactive scenarios, with milestone-based KPIs; also compares coordination protocols (star, chain, tree, graph topologies) and strategies (group discussion, cognitive planning). It does NOT measure race conditions, shared-state corruption, or handoff fidelity.
- Dataset size: UNVERIFIED in this pass.
- Models or systems tested: various LLM agents; gpt-4o-mini reported as reaching the average highest task score.
- Exact metric names: task score; milestone achievement rates (milestone-based KPIs, per abstract).
- Reported baseline numbers (reported in arXiv:2503.01935): graph structure performs best among coordination protocols in the research scenario; cognitive planning improves milestone achievement rates by 3%.
- Source URL: https://arxiv.org/abs/2503.01935 (code https://github.com/MultiagentBench/MARBLE)

## HotpotQA

- What it measures: diverse, explainable multi-hop QA over Wikipedia; sentence-level supporting facts for explainability; comparison questions.
- Dataset size: 113k Wikipedia-based question-answer pairs (reported in the abstract).
- Models or systems tested: EMNLP 2018-era QA systems (not relevant to agents; listed for dataset provenance).
- Exact metric names: answer EM/F1 and supporting-fact EM/F1 (metric names standard for the dataset; the abstract does not enumerate them, so treat as dataset convention).
- Source URL: https://arxiv.org/abs/1809.09600 (data page https://hotpotqa.github.io/)

## MuSiQue

- What it measures: multi-hop QA built by composing single-hop questions to make disconnected reasoning shortcuts ineffective; includes unanswerable contrast questions (MuSiQue-Full).
- Dataset size: MuSiQue-Ans, 25K 2-4 hop questions (reported in the abstract); TACL 2022.
- Models or systems tested: reported in the paper: 3x increase in human-machine gap vs existing datasets; a single-hop model drops 30 F1 points (reported in the abstract).
- Exact metric names: F1 (and human-machine gap framing), per the abstract.
- Source URL: https://arxiv.org/abs/2108.00573

## 2WikiMultiHopQA

- What it measures: multi-hop QA with explicit evidence information and reasoning paths, built from structured (Wikidata) and unstructured (Wikipedia) data.
- Dataset size: HuggingFace dataset viewer for the repackaged dataset reports 192,606 total rows (train ~167k, validation ~12.6k, test ~12.6k). The same HuggingFace card's split table lists 113,284 train / 12,981 validation / 12,995 test, which conflicts with the viewer row counts; treat exact split sizes as approximate, total ~192.6k corroborated by the viewer.
- Models or systems tested: used as an evaluation dataset in many multi-hop papers, e.g. reported in arXiv:2210.03350 with Davinci-002: direct prompting 25.4 accuracy, chain-of-thought 29.8, self-ask 30.0, self-ask + search 40.1 (2Wiki column, exact match).
- Exact metric names: exact match / F1 for QA; supporting-facts metrics for evidence; question types bridged as comparison, bridge_comparison, compositional, inference (per the HF card field docs).
- Source URL: paper https://aclanthology.org/2020.coling-main.580/ (COLING 2020); data repo https://github.com/Alab-NII/2wikimultihop; HF card https://huggingface.co/datasets/framolfese/2WikiMultihopQA

## Criticisms of these benchmarks

- Direct audit of long-term memory evaluation: arXiv:2609.38021 ("Auditing Long-Term Memory Evaluation: Repeated Judging, Reader Variation, and Negative Controls", submitted 1 Oct 2026) re-judges the same answers on LongMemEval-S and reports that re-judging changed labels (479/475/478 on the 500 dev questions across repeated GPT-4o rubric runs), that reader lanes span 93 to 479 on fixed packets, that paired tests between strong historical lanes establish neither superiority nor equivalence, and that in recovered LoCoMo data token-F1 gains do not survive answer-line extraction. All reported in that paper.
- Final-answer scores hide pre-generation failures: arXiv:2610.10265 reports that without update resolution 70.3% of prompts expose a superseded (stale) value, that open-domain merge recall on LongMemEval never exceeds 0.062, and that misattribution between identically named speakers in LoCoMo cannot be resolved by an entity posterior; it argues for evaluating stored-state validity, identity resolution, abstention, and serving latency separately. All reported in that paper.
- Multi-hop annotation vs observed evidence dependence: arXiv:2609.36984 (REALHOP) reports panel-mean Behavioral Necessity Rate of 16.6% to 48.9% across five existing benchmarks, i.e. correct answers often do not depend on the intended evidence hops; on 790 paired MuSiQue questions their reconstruction raises BNR from 27.4% to 94.4%. All reported in that paper.
- Benchmark-scope criticism by newer benchmarks themselves: MemoryAgentBench (arXiv:2507.05257) states existing benchmarks rely on limited context lengths or static long-context settings and that no existing benchmark covers all four of their competencies (accurate retrieval, test-time learning, long-range understanding, selective forgetting). Mem0 (arXiv:2504.19413) positions LoCoMo LLM-as-a-Judge comparisons against six baseline categories as its evidence basis, implicitly treating LoCoMo as the field reference point. LongMemEval (arXiv:2410.10813v2) states prior benchmarks including LoCoMo fail to evaluate recall of assistant-provided information or reasoning with updated user information, and characterizes LoCoMo as ~10k context depth vs its own 115k/1.5M settings (Table 1 in that paper).
- Practical criticism relevant to us: LoCoMo is CC BY-NC licensed (non-commercial), so any public-facing commercial reuse of the dataset itself is restricted; running LoCoMo-style evals in a hackathon demo is fine, republishing the data is not.

## Claims table

| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| M4-01 | LongMemEval has 500 questions, 7 question types, 5 abilities, settings S (~115k tokens) and M (500 sessions, ~1.5M tokens) | https://arxiv.org/abs/2410.10813 | VERIFIED | v2 revised 4 Mar 2025; ICLR 2025 |
| M4-02 | LongMemEval metrics are LLM-judge QA accuracy (gpt-4o-2024-08-06 evaluator) plus Recall@k and NDCG@k | https://arxiv.org/html/2410.10813v2 | VERIFIED | Evaluator-human agreement reported >97% |
| M4-03 | LongMemEval headline drops: ChatGPT GPT-4o 0.5773 vs offline 0.9184 (37%); Coze GPT-4o 0.3299 (64%); long-context LLMs 30-60% drops on S | https://arxiv.org/html/2410.10813v2 | VERIFIED | Tables in Figure 3 |
| M4-04 | LoCoMo is arXiv:2402.17753, 50 conversations, avg 300 turns / 9K tokens / up to 35 sessions | https://arxiv.org/abs/2402.17753 | VERIFIED | Project page snap-research.github.io/locomo |
| M4-05 | LoCoMo QA has 7,512 questions: 2,705 single-hop, 1,104 multi-hop, 1,547 temporal, 285 open-domain, 1,871 adversarial | https://arxiv.org/html/2402.17753v1 | VERIFIED | Appendix B Table 5 |
| M4-06 | LoCoMo metrics: F1 per category, Recall@k, FactScore P/R/F1, ROUGE (paper writes ROGUE), MMRelevance | https://arxiv.org/html/2402.17753v1 | VERIFIED | See also typo note |
| M4-07 | LoCoMo numbers: human 87.9 F1; best GPT-4-turbo base 32.1; long-context best 37.8 with adversarial 2.1; best RAG (observation, top-5) 41.4 | https://arxiv.org/html/2402.17753v1 | VERIFIED | Text body also cites 32.4 for GPT-4-turbo |
| M4-08 | Mem0 reports 26% relative LLM-as-a-Judge improvement over OpenAI on LoCoMo, ~2% graph variant gain, 91% lower p95 latency, >90% token savings | https://arxiv.org/abs/2504.19413 | VERIFIED | System paper, not a benchmark |
| M4-09 | MemoryAgentBench covers accurate retrieval, test-time learning, long-range understanding, selective forgetting; current methods fall short | https://arxiv.org/abs/2507.05257 | VERIFIED | Exact dataset size not captured, UNVERIFIED |
| M4-10 | HotpotQA: 113k QA pairs, EMNLP 2018 | https://arxiv.org/abs/1809.09600 | VERIFIED | |
| M4-11 | MuSiQue: 25K 2-4 hop questions, TACL 2022, arXiv:2108.00573 | https://arxiv.org/abs/2108.00573 | VERIFIED | |
| M4-12 | 2WikiMultiHopQA: ~192,606 questions total (HF viewer); split sizes conflict on HF card | https://huggingface.co/datasets/framolfese/2WikiMultihopQA | PARTIAL | Paper COLING 2020 https://aclanthology.org/2020.coling-main.580/ |
| M4-13 | MultiAgentBench exists for multi-agent collaboration/competition with milestone KPIs; graph topology best in research scenario; cognitive planning +3% milestone achievement | https://arxiv.org/abs/2503.01935 | VERIFIED | Dataset size not captured |
| M4-14 | No public benchmark for agent-memory race conditions, shared-state corruption, or handoff fidelity was found in these searches | (searches: arXiv listing for LoCoMo/memory benchmarks) | UNVERIFIED (negative finding) | Absence of evidence, not evidence of absence; see Could not verify |
| M4-15 | LongMemEval/LoCoMo judge and metric instability documented by an audit paper | https://arxiv.org/abs/2609.38021 | VERIFIED | Re-judging changed labels; reader lanes 93-479 |
| M4-16 | Stale/misattributed memory failures dominate pre-generation; merge recall on LongMemEval <= 0.062 | https://arxiv.org/abs/2610.10265 | VERIFIED | |
| M4-17 | Multi-hop answer correctness often does not depend on annotated hops (BNR 16.6-48.9% across 5 benchmarks) | https://arxiv.org/abs/2609.36984 | VERIFIED | |

## Evaluation plan for a 48-hour build

The honest unit of evaluation for a 48-hour hackathon build is a small, hand-built, deterministic suite plus latency measurement, not a published benchmark leaderboard. Proposed plan, with limits stated:

- Build 20-50 hand-authored session cases per track-relevant capability (e.g. 10 multi-hop retrieval over the graph, 10 knowledge-update/temporal ordering, 10 cross-agent handoff fidelity), each with ground-truth answers and ground-truth evidence nodes/edges. Cases are tiny by design: total effort must stay under roughly a quarter of the build window. Limits: hand-built cases are biased toward what we thought to write; 20-50 cases give very wide confidence intervals, so report raw counts (e.g. 34/42) and never percentages alone; do not compare against published LongMemEval/LoCoMo numbers as if the suites were commensurable.
- Metric 1, retrieval hit rate: fraction of cases where the ground-truth evidence node/edge appears in the top-k retrieved context, reported as raw counts with k stated. This mirrors LongMemEval's Recall@k and LoCoMo's "recall accuracy of correct context" concept (both reported in arXiv:2410.10813v2 and arXiv:2402.17753v1), computed on our own data.
- Metric 2, answer correctness on the same cases, checked by a simple rubric (exact match for closed answers, manual or LLM-judge for open ones). If an LLM judge is used, state the judge model and prompt and accept the audit paper's warning (arXiv:2609.38021) that re-judging changes labels; fix answers once and freeze the judged set.
- Metric 3, multi-agent coordination correctness: for Track 02, define 5-10 scripted concurrent-write scenarios (two agents writing conflicting facts about the same entity; handoff where agent B must continue from agent A's memory) with deterministic expected final graph state; check the graph state after each run. Limits: this is a self-made correctness check, not a published benchmark (M4-14); call it a scenario suite, not a benchmark.
- Metric 4, latency percentiles (p50/p95) for retrieval and write paths, measured with a fixed local stack and reported with the hardware and dataset size stated; Mem0's reported p95 framing (arXiv:2504.19413) is the precedent for reporting p95 latency, but our numbers are ours and only comparable to our own baselines.
- Baselines to run on the same suite: a no-memory or direct-LLM arm and a plain vector-RAG arm on the identical cases, so any graph advantage claim is a within-suite delta, which is the only comparison a 48-hour suite can support.
- State limits explicitly in the README: suite size, hand-authored bias, single backbone model, no statistical power, evaluation code frozen before final numbers are quoted.

## Claims we must not make

- Do not claim "state-of-the-art on LongMemEval" or "SOTA on LoCoMo" from a 48-hour build; those suites are 500 and 7,512 question-scale with specific harnesses and judge prompts, and the audit literature shows even their reported numbers are judge-sensitive (arXiv:2609.38021).
- Do not claim percentage-point superiority over Mem0, LongMemEval, or LoCoMo published numbers; our suite is not the same data, same judge, or same protocol.
- Do not claim the graph database "improves memory accuracy by X%" without an identical-protocol baseline on the same cases (e.g. same LLM, same retrieval budget, with vs without graph edges).
- Do not claim race-condition safety, handoff fidelity, or multi-agent correctness "verified" unless the scripted scenario suite actually ran; no public benchmark certifies this (M4-14), so any such claim is ours to defend with our own evidence.
- Do not republish or bundle LoCoMo data (CC BY-NC) in the demo repo; reference it, do not ship it.
- Do not present measured latency without hardware, dataset size, and percentile definition; do not compare latency across different machines.
- Do not claim long-horizon (100k+ token) capability from 20-50 short hand-built cases.

## Could not verify

- MemoryAgentBench exact dataset size, metric table, and full system roster (only the abstract and title were fetched).
- MultiAgentBench dataset size and exact KPI definitions (only the abstract was fetched).
- 2WikiMultiHopQA exact train/dev/test split sizes (HuggingFace viewer row counts vs the card's split table disagree).
- HotpotQA metric names from its abstract (EM/F1 convention not stated in the abstract itself).
- Any benchmark specifically for agent-memory race conditions, shared-state consistency, or handoff fidelity; searched arXiv listings for LoCoMo/memory benchmarks and multi-agent coordination (found MultiAgentBench only). This is a negative result, not a claim that none exists anywhere.
- LongMemEvalM results beyond the setting definition (I captured the setting, not the full M-scale results table).
- Zep/Graphiti and other vendor memory eval reports (out of scope this pass).

## Coordination log

- Round 2 file created at C:\Users\HARIHARAN\Desktop\SheldonAI\research\v2_04_benchmarks_and_evaluation.md per task spec; claim prefix M4- reserved for this file.
- First-pass arXiv ID guesses for MuSiQue (2108.11818) and 2WikiMultiHopQA (2210.11850) were WRONG (they resolved to a blockchain paper and a quantum paper); both were re-verified via arXiv search (MuSiQue = 2108.00573; 2Wiki source paper = ACL Anthology 2020.coling-main.580 / arXiv:2011.01060). A wrong first guess for LoCoMo (2404.17136, an NL2Vis paper) was likewise corrected to 2402.17753.
- All numbers transcribed from fetched arXiv/ACL/HuggingFace pages on 2026-10-15; given the hackathon build window, re-check any number before quoting it publicly.
