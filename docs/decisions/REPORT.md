# Sheldon: final Graph Hacks report (team SheldonAI)

Written Sat 17 Oct 2026. Deadline: Sun 18 Oct 2026, 11:59 PM IST.

This file is the source of truth for product scope. [`docs/facts.md`](../facts.md) is the short list of engine limits and claims that are wrong. [`docs/engine/papers.md`](../engine/papers.md) is the paper check, including the personalized-PageRank row that cannot be built. Those three override `docs/design/` and `docs/research/`.

Team names, handles, repo paths, and overlap notes from the validation pass are not in this tree.

## 1. What this is

Multi-agent incident-investigation memory on FalkorDB: an append-only event chain, hypothesis and decision nodes, a task board on the same graph, one graph per investigation, and answers that cite evidence with the path.

**Lead**

- **(a)** A hypothesis changes status only inside one atomic conditional Cypher write. The write `MATCH`es every cited evidence id. If any id is missing it returns 0 rows and is rejected. No LLM decides.
- **(b)** That same write marks dependent open tasks stale (bounded `*1..3`) and sets `confidence`. Refuted hypotheses are never deleted.
- **(c)** Repeated failed steps, Sheldon vs plain memory, raw counts. Every run is reset from one frozen `GRAPH.COPY`.

**Scope is frozen at p0–p4 plus that eval.** Ship: event memory, task board with atomic claim and lease, `resume()` with evidence paths, the concurrent-claim race, the gated refute plus stale mark, Q\*, and the S0-vs-S3 count.

**Cut:** label-as-vector-filters, the MCP server, BeliefMem's multi-candidate machinery, ablations, playbooks, the `GRAPH.COPY` branch-and-merge stretch (the copy reset stays), A\*/CCH/point/maxFlow, Bolt, replication, GraphRAG-SDK, and `MULTI`/`EXEC`.

**Version pin:** `falkordb/falkordb:v4.22.1` (module 42201), the image the spikes effectively ran on. Move to `falkordb/falkordb:6.0.2` only if a JS UDF ships. Never `latest` or `edge`. 4.x tags start with `v`. 6.x tags do not.

## 2. The three-part lead

### (a) Cited evidence, one write

The refute is one conditional Cypher write. It matches every cited evidence id. Dedupe ids in the client. Spike the `FOREACH` / `collect` shape on the pinned image.

A successful refute still has to return the hypothesis when nothing downstream is open. A bare `MATCH` of dependent tasks makes "no tasks" look like "rejected".

Backstop, not the gate: `MANDATORY` on `Hypothesis.status` and on the `REFUTED_BY` properties `agent` and `at`. `UNIQUE` on `Event.id` and `Hypothesis.id` (exact-match index first). Constraints can only require a property or make it unique. They cannot require an edge or check that a cited id exists. Say "service-plus-query enforcement backed by db constraints".

Optional, and off until the basic gate is green: cited evidence must sit within n ≤ 2 hops. That hop check is our own design. No paper tests it. G-Memory's 1-hop result is about retrieval and only weakly supports a small n.

BeliefMem (arXiv 2605.05583): a refute flips `status` and never deletes. Keep the hypothesis retrievable with `status` and `confidence`. One simple confidence rule is enough. Do not build the noisy-or multi-candidate machinery. Cite BeliefMem only for "a single hard conclusion hurts" (ALFWorld SR 59.88 → 28.71 when one conclusion is kept).

### (b) Dependent tasks, same write

Downstream spread on its own is not the claim. The claim is the combination: a refute gated on cited evidence ids that, in the same atomic write, flags the dependent open tasks. Say "none we found". Never "reaching the task board is ours".

Keep the depth bounded (`*1..3`). Never use unbounded `*0..`, because `LIMIT` does not restrict eager operations.

Demo question, Q\*:

> Which open tasks are still blocked by, or justified by, a hypothesis whose supporting evidence traces back to an action that was later refuted, and what's the chain?

Show it with S0 (vector + keyword) failing live, and show the Cypher.

Published motivation, not a Sheldon result (STALE / CUPMem, arXiv 2605.06527): gpt-4o-mini 8.7% → 68.0% overall with write-time adjudication plus propagation-aware invalidation. The best frontier model without it scores 55.2%. CUPMem is the authors' own method on their own benchmark.

### (c) Repeated failed steps

Report raw counts on written scenarios, at least 3 runs each, S0 (plain memory) vs S3 (Sheldon). Every run resets from one frozen `GRAPH.COPY`. That sentence is a methods line, not a novelty claim.

Write the definition of "repeated failed step" before automating it (MAST-style: label a sample by hand, then count).

MAST (UC Berkeley, arXiv 2503.13657): step repetition (FM-1.3) is 15.7% of multi-agent failures.

TIDE (arXiv 2602.02196) defines loop ratio as redundant loop actions / total actions. TIDE's 15.8% → 1.0% drop is from model scaling (Qwen3-4B → 30B), not from memory. Never pitch it as a memory effect.

A read-only `sameAction` check is conditional. UDFs are JavaScript and read-only, and the UDF fixes we would want are on 6.0.2. Do not assume FLEX is loaded on v4.22.1. Python is the fallback. UDFs cannot write, so the refute gate stays Cypher.

Wording: "we measured", "none we found". Never "nobody else measures this".

## 3. Engine position

Pitch "one query, one key per investigation", and show the Cypher next to the answer. Almost every single feature has a Postgres or Neo4j equivalent. Do not say "only possible on FalkorDB".

| Feature | Why Sheldon uses it | How to talk about it |
|---|---|---|
| Atomic single-query write (claim, gated refute + stale mark) | Lease and gate in one query. No `MULTI`/`EXEC` | Generic. The combination is the point |
| One graph per investigation | Create, drop, or snapshot an investigation as one key | A good choice. Not forced by vector filters |
| `GRAPH.COPY` | Frozen seed before every eval run | Methods line. Not a novelty claim |
| Multi-type var-length paths `*1..3` | Q\* and the stale mark | Speed is unmeasured. Do not claim it |
| Vector + full-text + traversal in one query | Anchored retrieval in one round trip | The composition is the useful part |
| `MANDATORY` / `UNIQUE` | Backstop for the gate | Weaker than a foreign key. The write is the gate |
| JS UDF `sameAction` | Optional repeated-step check | Read-only. 6.0.2 only. Off on the current pin |
| `localdatetime` / `duration` | Leases and `refuted_at`, if used | Generic. `$now` still comes from the service clock |
| `RO_QUERY` + timeout, `PROFILE`, `GRAPH.MEMORY` | Safe reads, the plan, per-investigation size | Use them in the demo |

Do not reach for personalized PageRank (it does not exist), A\*, or CCH. A\* and CCH are 4.22-only and geographic, and they are cut anyway. `algo.pageRank` is global.

Vector post-filters run, and they run after the top-k cut. An empty result can mean "outside the window". Per-investigation graphs avoid that cliff. They are not required by a hard ban.

Reads that agents issue should go through `RO_QUERY` with a timeout once that path exists. The demo audit is: hypotheses with status `refuted` and no `REFUTED_BY` edge to an `Event` return 0 rows.

The image's default query timeout is 1000ms (`TIMEOUT` on the `graph` module). See `docs/engine/features.md` before raising it.

## 4. Papers worth citing

Paper numbers motivate the design. They are never Sheldon's results.

| Paper | arXiv | Number | Use |
|---|---|---|---|
| STALE (+ CUPMem) | 2605.06527 | gpt-4o-mini 8.7% → 68.0%; best model without it 55.2% | (a), (b) |
| BeliefMem | 2605.05583 | one conclusion kept: ALFWorld SR 59.88 → 28.71 | keep refuted hypotheses, add confidence |
| MAST | 2503.13657 | step repetition FM-1.3 = 15.7% | (c) |
| TIDE | 2602.02196 | loop-ratio definition only | not the 15.8% → 1.0% drop |
| ReasoningBank | 2509.25140 | failure-inclusion 46.5 → 49.7 | failures are signal |

More papers, each marked with the FalkorDB version it was checked against: [`docs/engine/papers.md`](../engine/papers.md).

## 5. Claims that must leave the pitch

- "only possible on FalkorDB", and any speed number that has not been measured on our harness
- "no competitor has GRAPH.COPY" / "no other graph DB has an equivalent"
- "vector queries can't be combined with filters, so per-investigation graphs are forced"
- "coordination and memory on one graph is our gap" — lease, handoff, and resume are table stakes
- "we track hypotheses" as a differentiator
- "refutations propagate downstream" as novel, on its own
- "reaching the task board is ours"
- "nobody else measures repeated steps"
- personalized PageRank, or `algo.pageRank` described as personalized
- TIDE's loop-ratio drop as a memory effect
- MIRIX arXiv `2501.02388` (the id is `2507.07957`)
- HippoRAG "+38.6%" (it is +38.6 points AR@5 on 2Wiki, 37.1 → 75.7)
- HippoRAG "10–30× cheaper" (the v3 abstract says 10–20×; safest quote is "6–13× faster")
- "IRCoT needs 4–6 LLM round-trips, 5–10 s" (not found; drop it)
- "Mandatory MATCH can't follow OPTIONAL MATCH" and "MERGE on a whole path duplicates nodes" — not on the known-limitations page. Test them or don't say them
- the product name SynapseOS

The short list is [`docs/facts.md`](../facts.md). The paper corrections are in [`docs/engine/papers.md`](../engine/papers.md).

## 6. Build notes

- Pin the tag in `sheldon/schema.py`, `docker-compose.yml`, and `.github/workflows/ci.yml` together. Re-run `spikes/` once on whatever tag you pin.
- `latest` and `v4.22.1` shared one digest on 17 Oct 2026 (`sha256:b0bdcac…`). `latest` can move. `edge` moves daily. Neither belongs in the demo.
- Habits: Cypher shown next to the answer, the audit query above, and a 10–50 way claim race with exactly one winner.
- An investigation is the tenant unit.

## Verdict

Go, with the fixes already in this file. Freeze to p0–p4 plus the eval, keep the image pin, build the refute as one gated write, and produce (c) as raw counts from a frozen copy.
