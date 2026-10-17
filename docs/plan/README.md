# Plan

Read this before writing code. The product wording lives here, not in the older design notes.

**Sheldon blocks coding agents from retrying fixes that already failed, and from calling work done without a real test run, from the first edit to the merge, on one shared FalkorDB graph per repo.**

A claim or approval only lands if every evidence id it cites is a real executed run. Refuting evidence marks the claim refuted, and every approval and task that relied on it goes stale, in one atomic write. Nothing marks a claim stale. None we found blocks a coding agent from retrying a code fix refuted in the shared graph.

| File | What it is |
|---|---|
| [deep.md](deep.md) | Scope, stations, schema, wording. Source of truth. |
| [work-split.md](work-split.md) | Proposed owners and order. Akshat to confirm. |
| [quotes.md](quotes.md) | The five quotes this plan uses. No others. |
| [demo.md](demo.md) | Draft 3-minute demo script, step by step, with the rows each step needs and its fallback. |
| [eval-def.md](eval-def.md) | Operational definition of repeated failed steps, 7-case taxonomy, and paired eval protocol. |

## Status words

Use these words in README, `AGENTS.md`, `TASKS.md`, and stub docstrings.

| Word | Meaning |
|---|---|
| ran | The query has actually run. Today that is only **W1** (evidence gate), **W2** (refute plus stale cascade), and **R1** (PR-time recall). |
| to build | In Sunday's scope. The Python function does not do it yet. |
| roadmap | After the hackathon. Do not build it for the demo. |
| to measure | Say it only after the with/without run has numbers. |

A stub that raises `NotImplementedError` is not a working feature, including when the query behind it has run. Say "query ran; this function is to build."

## What wins

`docs/plan/` wins on product scope and wording. [`docs/facts.md`](../facts.md), [`docs/decisions/REPORT.md`](../decisions/REPORT.md), and [`docs/engine/papers.md`](../engine/papers.md) still win on engine limits when an older research note disagrees with them: the image pin, what constraints and UDFs cannot do, and the personalized-PageRank row that cannot be built.

Image pin stays `falkordb/falkordb:v4.22.1`. Do not change it in this tree to chase a UDF.

## Wording

- "None we found" for anything about what others do not do.
- Do not claim the design needs FalkorDB and nothing else. No speed number this harness has not measured.
- No cost-saving numbers. Cost stays "to measure".
- No "revolutionary". No "production-ready". The approved install phrase is "installs in one step on a real repo", once it does.
- Default quality phrase: "safer at the same quality". "Smarter" only if the with/without margin beats a 1-task gap across at least 3 runs per arm.
- Paper numbers are never Sheldon's results. The 8.7% → 68.0% staleness figure is a published STALE / CUPMem result, not ours. Caption it that way.
- Repo mapping is FalkorDB code-graph and RepoGraph. Credit them.
- Pains are what Sheldon is built for, not something it has already fixed.
- The refused fake "done" is a demo moment, not the headline.
