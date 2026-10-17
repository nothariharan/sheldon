> Papers for the three-part lead. The version key at the top says which FalkorDB behavior was spiked on **4.22.1** `[S]` and which is docs-only `[D]`.
> Paper numbers motivate the design. They are never Sheldon's results.
> **Precedence:** this file, [`facts.md`](../facts.md), and [`REPORT.md`](../decisions/REPORT.md) override `docs/design/` and `docs/research/`. The errors section is why a personalized-PageRank design row cannot be built.

# paper scout: papers for sheldon (2026-10-17)
written sat 17 oct 2026, ~11:00–12:00 ist. every number below comes from the paper's abstract or results/ablation section, read on arxiv today (abs page + html full text). anything i couldn't check is marked **unverified**. ranks, "take" lines and verdicts are **opinion**.

team lead (fixed): (1) an evidence-gated refute write, ideally path-checked (the cited evidence sits within n hops), (2) one traversal that flags open tasks resting on refuted hypotheses, (3) a measured count of repeated failed steps vs plain memory.

## falkordb version key (from features.md + spike v3_00)
- **[S]** = spiked by the team on **4.22.1** (module 42201, C engine): atomic conditional `MATCH…WHERE…SET` write, multi-type var-length paths + `length(p)`, vector index (+ `WHERE` filter on the yielded node), `algo.pageRank(label,rel)`, `algo.betweenness()`, `algo.WCC()`, `algo.labelPropagation()`, `algo.BFS`, `algo.SPpaths`. the 6.0 notes say "same procedures as 4.20.7", so these should exist on 6.0 too, but **not spiked on 6.0**.
- **[D]** = docs only, not spiked. should exist on both 4.22.x and 6.0.x: full-text index (6.0 uses RediSearch 8.6.1), multigraph keys (`GRAPH.LIST/DELETE`), `GRAPH.COPY`, constraints (**MANDATORY/UNIQUE only**; UNIQUE needs an exact-match index first), JS UDFs (**read-only**; `graph.traverse` API since 4.16; 6.0.2 fixed UDF edge cases), temporal types, `GRAPH.PROFILE`, `GRAPH.RO_QUERY`+timeout.
- **not available:** personalized pagerank (none, on any version); `algo.AStar`/CCH (4.22.0+ only, **not in 6.0**, and geographic). no mapping below uses them.
- constraints are used only for required/unique fields. "cited id exists" and "within n hops" checks stay in the single conditional write query.

## does any paper back or break the evidence-gated hypothesis idea? (opinion, grounded in the numbers below)
- **backs a write-time gate:** STALE/CUPMem (#1). explicit write-time adjudication plus propagation-aware invalidation takes gpt-4o-mini from 8.7% to 68.0% on implicit-conflict memory. the best frontier model without it scores 55.2%. this is the strongest direct support for lead items (1) and (2).
- **backs keeping refuted things as memory:** ReasoningBank (#5) gets 46.5 → 49.7 SR when failures are distilled too. MAST (#3) finds step repetition is the single most frequent failure mode (15.7%).
- **partially breaks a hard binary refute:** BeliefMem (#2). collapsing memory to one deterministic conclusion per attribute drops ALFWorld SR from 59.88 to 28.71 and LoCoMo F1 from 42.38 to 22.58. Hindsight (#6) also uses graded confidence (contradict = −2α), not deletion. **implication:** keep the gate, but make a refute flip status and keep the hypothesis plus its alternatives retrievable. never delete, never let a single unverified observation drive `refuted`. sheldon's append-only design already fits this. a `confidence` property next to `status` would align with both papers.
- **nothing found that breaks path-checked citation.** no paper i read tests "evidence within n hops" as a write gate, so that part is our own design and **unvalidated**. G-Memory (#7) is the only data point on hop depth: 1-hop expansion beat 2/3-hop for retrieval. that's weak support for keeping n small (n ≤ 2).

## ranked list (rank = opinion)

### 1. STALE: can llm agents know when their memories are no longer valid? (+ CUPMem baseline)
- chao, bai, sheng, li, sun. wuhan u, cuhk, hkust. 7 may 2026. https://arxiv.org/abs/2605.06527
- **mechanism:** write-time "state adjudication". new evidence retires stale items, and a propagation-aware search also checks *structurally affected* slots (type ii: the invalidation sits elsewhere than the new evidence). at read time, items carry active/stale/unresolved markers, and a query that presupposes a stale state is blocked.
- **result:** best evaluated model (gemini-3.1-pro) 55.2% overall on 400 scenarios / 1,200 queries. CUPMem with gpt-4o-mini goes **8.7% → 68.0%** overall, and premise resistance reaches 78.0% / 75.0% (type i / ii) "compared to near-zero for most baselines" (sec 5, table 2).
- **code:** yes, https://github.com/icedreamc/STALE (link in paper; not opened).
- **falkor:** lead (2) is exactly "propagation-aware" invalidation: `MATCH (h:Hypothesis {status:'refuted'})<-[:RESTS_ON|DEPENDS_ON*1..3]-(t:Task {status:'open'}) RETURN t, length(p)` (var-length multi-type paths [S] 4.22.1). status markers = a `status` property with MANDATORY constraint [D]. read-side gate via `GRAPH.RO_QUERY` [D].
- **take:** borrow their 3-probe split (state resolution / premise resistance / policy adaptation) as sheldon's eval for the refute path. "premise resistance" = agent b proposes an action that rests on a refuted hypothesis, and sheldon must block it. that is lead (2) as a test.

### 2. BeliefMem: agent memory under partial observability
- liao, wang, zhu, du, yan, chen. mbzuai, riken aip, ut austin, wuhan u. 7 may 2026. https://arxiv.org/abs/2605.05583
- **mechanism:** store several candidate conclusions per attribute, each with a probability. supporting evidence merges by noisy-or: `p' = min(1-(1-p)(1-Δ), 0.99)`. a competitor's support sets the other candidate to 0.25. the old version is archived, and retrieval returns all candidates with their probabilities (eq 9).
- **result:** ablation "w/o belief-based memory" (one conclusion kept): ALFWorld SR **59.88 → 28.71**, LoCoMo avg F1 **42.38 → 22.58**. beats the 2nd-best (ReadAgent) by 11% on ALFWorld. with 500 samples (16.67% of corpus) it still averages 50.38% SR.
- **code:** no repo link found in the paper.
- **falkor:** the noisy-or update is one arithmetic `SET` inside the gated write ([S] atomic conditional write, 4.22.1). competing hypotheses = sibling `:Hypothesis` nodes on the same `:Question`. archive = append a new `:Event` (already the design).
- **take:** this is the paper that *qualifies* lead (1). add `h.confidence`, update it with noisy-or on each SUPPORTED_BY, and gate the move to `refuted` on cited evidence. don't drop the losing hypothesis from retrieval.

### 3. Why do multi-agent llm systems fail? (MAST)
- cemri, pan, yang, agrawal, …, zaharia, gonzalez, stoica. **uc berkeley**. 17 mar 2025 (v3). https://arxiv.org/abs/2503.13657
- **mechanism:** a 14-mode failure taxonomy built from 150 traces (kappa 0.88), then an llm annotator applied to 1,600+ traces across 7 MAS frameworks.
- **result:** failure rates of 41%–86.7% on 7 SOTA open-source MAS. **step repetition (FM-1.3) = 15.7%**, the largest single mode. also: reasoning-action mismatch 13.2%, not recognising completion 12.4%, context loss 2.8%, conversation reset 2.2%, withholding info 0.85%, incorrect verification 9.1% (sec 4).
- **code:** yes, https://github.com/multi-agent-systems-failure-taxonomy/MAST (`pip install agentdash` per paper).
- **falkor:** count FM-1.3 in Cypher: same-signature failed `:Action`s within one investigation graph, signature from a read-only JS UDF `sheldon.sameAction(a,b)` [D]. per-investigation graph keys make the count per-run [D].
- **take:** lead (3) has a citable reason: the most common MAS failure mode, measured by berkeley. borrow their annotation protocol: define "repeated failed step" up front, have 2 humans label a sample, report kappa, then automate.

### 4. TIDE: trajectory-based diagnostic evaluation of test-time improvement in llm agents
- yan, che, xu, sun, ding, cheng, zhang, qin, liu, lin. hku, xi'an jiaotong, shanghai ai lab, nanjing u. 2 feb 2026. https://arxiv.org/abs/2602.02196
- **mechanism:** the trajectory is a graph over environment states. a *cycle* returns to the same state with no progress, and a *loop* is a consecutive repeat of a cycle. **Loop Ratio = redundant loop actions / total actions** (sec 3, alg 1).
- **result:** scaling qwen3-4b → qwen3-30b-a3b cuts LR from **15.8% → 1.0%** (blocksworld) and **36.7% → 5.7%** (webshop). high LR correlates with low AUV across four models.
- **code:** yes, https://github.com/yayayacc/TIDE.
- **falkor:** the event chain is already a graph, so LR is a path query: `(s1:State)-[:NEXT*]->(s2:State)` with `s1.hash = s2.hash` [S var-length, 4.22.1], or `algo.BFS` from the current state [S]. `GRAPH.PROFILE` [D] can show it's cheap. Do not treat BFS or PROFILE as a differentiator.
- **take:** report two numbers for lead (3): raw repeated-failed-steps (MAST-style) and Loop Ratio (TIDE-style), S0 plain memory vs S3 sheldon, on a frozen seed via `GRAPH.COPY` [D].

### 5. ReasoningBank: scaling agent self-evolving with reasoning memory
- ouyang, yan, hsu, …, han, lee, pfister. **google cloud ai research**, uiuc, yale. 29 sep 2025, iclr 2026. https://arxiv.org/abs/2509.25140
- **mechanism:** distil `{title, description, content}` memory items from both self-judged successes **and failures** (llm-as-judge), retrieve by embedding, and write back after each task.
- **result:** webarena overall SR **+8.3 / +7.2 / +4.6** over memory-free across 3 backbones. failure-inclusion ablation (webarena-shopping, gemini-2.5-flash): **46.5 success-only → 49.7 with failures**, while AWM drops 44.4 → 42.2. up to 1.4 fewer steps vs no-memory. robust when judge accuracy is 70–90%.
- **code:** yes, https://github.com/google-research/reasoning-bank.
- **falkor:** a refuted hypothesis/failed action becomes a `:Lesson` node in a shared playbooks graph (separate graph key [D]). retrieve with the vector index + traversal back to the cited events [S].
- **take:** the refuted path should also emit a lesson, not just a status flip. that makes "failures are signal" measurable.

### 6. Hindsight is 20/20: building agent memory that retains, recalls, and reflects
- latimer, boschi, neeser, bartholomew, srivastava, wang, ramakrishnan. vectorize.io, washington post, **virginia tech**. 14 dec 2025, acl 2026 demo (aclanthology 2026.acl-demo.27). https://arxiv.org/abs/2512.12818
- **mechanism (a):** facts and beliefs live in separate networks. an opinion's confidence c is updated per new fact by llm-assessed relation: reinforce `+α`, weaken `−α`, **contradict `−2α`** (sec 5.5).
- **mechanism (b):** 4 parallel retrieval channels (vector, BM25, graph spreading activation = BFS from top semantic hits, temporal filter), fused by RRF, then a cross-encoder rerank.
- **result:** longmemeval-s with a 20b oss model: **39.0% (full context) → 83.6%**. 91.4% with gemini-3 pro, 89.0% with oss-120b (table 3). abstract: locomo up to 89.61% vs 75.78% for the strongest prior open system.
- **code:** yes, https://github.com/vectorize-io/hindsight (MIT).
- **falkor:** (b) is the falkordb-native read path in one query: `db.idx.vector.queryNodes` [S] + `db.idx.fulltext.queryNodes` [D] + var-length traversal / `algo.BFS` [S]. Hindsight needs postgres+pgvector+GIN to do the same. RRF can live in a read-only UDF [D] or the client.
- **take:** the asymmetric update (contradiction weighs 2×) is a cheap, cited rule for `h.confidence`. the 4-channel recall is our pitch line for "built around falkordb".

### 7. G-Memory: tracing hierarchical memory for multi-agent systems
- zhang, fu, wan, yu, wang, yan. nus, ntu, a*star, tongji, ucla. 9 jun 2025. https://arxiv.org/abs/2506.07398
- **mechanism:** 3 tiers: insight graph, query graph (task + Failed/Resolved status), per-query interaction (utterance) graph. retrieval = embedding top-k queries, then **1-hop expansion** on the query graph, upward to insights and downward to sparsified interaction graphs.
- **result:** up to **+20.89%** embodied-action success and **+10.12%** knowledge-qa accuracy. avg +6.8% / +5.5% over the best memory baselines with autogen / macnet (qwen-2.5-7b). hop study: 1-hop best (alfworld 85.82%, pddl 55.24%), 2-hop drops pddl to 49.79%.
- **code:** yes, https://github.com/bingreeky/GMemory.
- **falkor:** interaction graph per query = one graph key per investigation [D]. insight graph = shared playbooks graph. "vector top-k then 1-hop" = vector index + traversal in one query [S].
- **take:** evidence that sheldon's per-investigation split mirrors a published MAS memory design. the hop result supports a small n for the path-checked citation gate (opinion; G-Memory measured retrieval, not citation).

### 8. Agentic Context Engineering (ACE)
- zhang, hu, upasani, …, zou, olukotun. **stanford**, sambanova, **uc berkeley**. 6 oct 2025, iclr 2026. https://arxiv.org/abs/2510.04618
- **mechanism:** memory = itemized bullets, each with an id and **helpful/harmful counters**. the curator emits small delta entries merged by deterministic non-llm logic. grow-and-refine appends new ids, updates existing ones in place, and dedupes by embedding.
- **result:** +10.6% on agents (appworld) and +8.6% on finance vs baselines. **86.9% lower adaptation latency** on average. appworld offline: 82.3% lower latency and 75.1% fewer rollouts vs GEPA. appworld leaderboard (20 sep 2025): 59.4% vs top-1 ibm cuga 60.3%.
- **code:** yes, https://github.com/ace-agent/ace (sambanova announcement).
- **falkor:** bullet = `:Lesson {id, helpful, harmful}`. a delta is a `MERGE … ON MATCH SET l.harmful = l.harmful + 1` in one atomic write [S]. UNIQUE on `Lesson.id` [D]. dedupe = vector index query before insert [S].
- **take:** "non-llm deterministic merge" is the same principle as sheldon's gate (the db decides, not the llm). cite it.

### 9. Which agent causes task failures and when? (Who&When)
- s. zhang, m. yin, …, b. li, c. wang, h. wang, y. chen, q. wu. penn state, duke, u washington, ntu, meta, google deepmind. 30 apr 2025, icml 2025 (camera-ready). https://arxiv.org/abs/2505.00212
- **mechanism:** a dataset of failure logs from 127 MAS annotated with the responsible agent and decisive step. compares all-at-once, step-by-step and binary-search attribution.
- **result:** best method **53.5%** agent-level and **14.2%** step-level accuracy. o1 / r1 "fail to achieve practical usability".
- **code:** yes, https://github.com/mingyin1/Agents_Failure_Attribution.
- **falkor:** if every action→hypothesis→evidence link is written at action time, step attribution becomes a path query (`algo.SPpaths` [S], or var-length match), not an llm guess.
- **take (opinion):** a good argument for why sheldon records provenance at write time: post-hoc reconstruction from logs tops out at 14.2% step accuracy.

### 10. Sleep-time compute: beyond inference scaling at test-time
- lin, snell, wang, packer, wooders, stoica, gonzalez. **uc berkeley**, letta. 17 apr 2025. https://arxiv.org/abs/2504.13171
- **mechanism:** precompute over the context offline, before queries arrive.
- **result:** ~**5×** less test-time compute for the same accuracy (stateful gsm-symbolic, stateful aime). +13% / +18% accuracy when sleep-time compute is scaled. **2.5×** lower average cost per query when amortized across related queries. it helps most when queries are predictable.
- **code:** yes, https://github.com/letta-ai/sleep-time-compute.
- **falkor:** `GRAPH.COPY` the live investigation [D], then run `algo.betweenness()` / `algo.WCC()` [S] on the copy between agent turns ("pivot evidence", "separate lines of inquiry"), so live writes are never blocked.
- **take:** stretch only. it gives GRAPH.COPY an honest second use beyond eval resets.

## also checked (not ranked)
- **Agent Workflow Memory** (wang, mao, fried, neubig; cmu + mit; arxiv 11 sep 2024): +24.6% / +51.1% relative SR on mind2web / webarena. procedural memory. code https://github.com/zorazrw/agent-workflow-memory. arxiv date is 2024, venue **unverified** here.
- **MIRIX** (yu wang, xi chen; 10 jul 2025; https://arxiv.org/abs/2507.07957): 6 memory types. locomo 85.4%. +35% vs RAG on screenshotvqa with 99.9% less storage (abstract only).
- **Zep/Graphiti** (2501.13956): bi-temporal edge invalidation, an llm compares new vs existing edges. dmr 94.8% vs 93.4%, longmemeval up to +18.5% and −90% latency (abstract). already in team docs.
- **MEM1** (mit, 2506.15841): constant-memory rl agent, 3.5× perf and 3.7× less memory vs qwen2.5-14b on a 16-objective task. not graph, no falkor fit.
- **Evo-Memory** (google deepmind + uiuc, 2511.20857): streaming benchmark for self-evolving memory. numbers not read.
- **SagaLLM** (stanford, 2503.11951): saga transactions + compensation for multi-agent planning. abstract gives no numbers.
- **Collaborative Memory** (2505.18279): immutable provenance on memory fragments + bipartite access graphs. no numbers in abstract.
- **AgentRewardBench** (mcgill/mila, 2504.08942): 1,302 expert-labelled trajectories incl. a "repetition cycle" label. a possible annotation template; rates not read.
- **Bayesian Teaching** (qiu…linzen, van steenkiste; google research et al.; nature communications; 2503.17523): llms fall short of bayesian belief updating and fine-tuning helps. weights-level, so no falkor fit.
- **TruthKeeper** (welsch, academia.edu only): a TMS with dependency-cascade invalidation and 4 truth states. **not on arxiv, not peer-reviewed, unverified**. the idea matches lead (2), but don't cite it.

## errors found in existing research docs (with evidence)
1. **02_ACADEMIC…md §5, MIRIX: wrong arxiv id and wrong title.** arxiv 2501.02388 is "Optimization problems constrained by parameter sums" (nash & varadhan, an R optimisation note). real MIRIX = arxiv **2507.07957**, "MIRIX: Multi-Agent Memory System for LLM-Based Agents", yu wang & xi chen, 10 jul 2025. "Multi-Index Retrieval Indexer for eXpandable Agent Memory" is not the paper's title. it was marked VERIFIED.
2. **02 §6, HippoRAG "+38.6% over ColBERTv2, All-Recall@5":** the figure exists but the unit is wrong. HippoRAG table 6 (appendix) has 2wiki AR@5 ColBERTv2 **37.1 → HippoRAG 75.7 = +38.6 percentage points** (≈ +104% relative), not "+38.6%". so v2_06's "UNVERIFIED — DO NOT QUOTE" (M3-09) can be lifted if quoted as "+38.6 points AR@5 on 2wiki (table 6)".
3. **HippoRAG "10–30× cheaper":** arxiv abs-page metadata and §4 body say 10–30×, but the v3 paper's own abstract text (html/pdf v3) says **"10 - 20 times cheaper"**. the paper is inconsistent with itself. safest quote: "6–13× faster, 10–20× cheaper (v3 abstract)".
4. **02 §6 "IRCoT requires 4–6 LLM round-trips taking 5–10 seconds"** (marked VERIFIED): not found in the HippoRAG text i grepped. **unverified**, drop it.
5. **02 §8 LongMemEval "commercial chat assistants and long-context LLMs suffer 30–60%+ drops":** this mixes two results. the paper says long-context llms drop 30–60% on LongMemEval-S (fig 3b). commercial systems (chatgpt, coze) were tested on a much shorter 3–6-session history and dropped **37% and 64%** vs offline reading (fig 3a). abstract: "30% accuracy drop".
6. **v2_06 M3-03 / M3-04 (CoALA taxonomy, princeton) are now verified:** the CoALA html body names working memory plus long-term episodic, semantic and procedural memory (sec 4), and lists princeton affiliations/emails. not an error in 02, but v2_06's downgrade can be lifted.
7. **v2_06 M3-14 (A-MEM rutgers) verified:** html lists rutgers for 5 of 6 authors (one "independent researcher"). abs comment: neurips 2025. ok.
8. **02 §1 summary table "Use CALL algo.pageRank() … for associative memory activation"** (and §6 α "typically 0.15"): falkordb has **no personalized pagerank** (features.md #16, spike B1). HippoRAG 2 itself uses damping 0.5 via python-igraph (appendix g.1, table 13). the doc's design row is not implementable as written. use seeded var-length traversal / `algo.BFS` spreading activation (Hindsight-style) instead.
9. minor: 02 calls the system "SynapseOS" throughout, a leftover name from an earlier idea, not Sheldon.

## method / limits
- fetched today: arxiv abs metadata + html full text for every ranked paper. numbers grepped from results/ablation text (math alttext preserved). repos are cited from links in the papers or the official announcement; i did not open or run them.
- not done: semantic scholar/openreview venue checks beyond arxiv comments. no MAGMA/WorkflowOps/VeriMAP/OneVoice/2605.06457/2609.38021 re-checks (in team docs, out of scope this pass).
