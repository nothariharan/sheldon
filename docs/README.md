# Docs

Read in this order:

1. [`plan/README.md`](plan/README.md) — product scope and wording. W1, W2, and R1 queries ran. Everything else is to build or roadmap.
2. [`facts.md`](facts.md) — the image pin, what constraints and UDFs cannot do, and the claims never to write.
3. [`engine/papers.md`](engine/papers.md) — paper corrections. Its errors section covers the personalized-PageRank design row, which cannot be built.
4. [`decisions/REPORT.md`](decisions/REPORT.md) — older scope note. The plan wins where they disagree on the product.
5. [`../AGENTS.md`](../AGENTS.md) — how to work in this repo.
6. The area `AGENTS.md` next to the code you are about to touch.

**Precedence:** `docs/plan/` wins on product scope and wording. `facts.md`, `REPORT.md`, and `engine/papers.md` override everything under `design/` and `research/` on engine limits. Those older files still contain superseded sentences. A banner on the file is the warning. The corrected line, where we changed one, is the one to follow.

## Map

| Path | What it is |
|---|---|
| `plan/` | Product scope, stations, owners, and the six quotes |
| `facts.md` | Pin, engine limits, research corrections, claims never to write |
| `decisions/REPORT.md` | Older scope note. The plan wins on the product |
| `engine/features.md` | FalkorDB feature list with doc links. Read before guessing that a command exists |
| `engine/papers.md` | Papers for the lead, with the errors that override older research |
| `design/PLAN_SHELDON.md` | Older build plan. p0–p4 names still show up. The plan in `plan/` wins |
| `design/stuff.md` | Graph model and the read/write paths the plan points at |
| `design/FALKORDB_ARCHITECTURE.md` | Engine background. The PageRank row was wrong and is corrected |
| `design/SHELDON_REPORT.md` | Longer product note from 15 Oct. The plan wins |
| `research/` | 15 Oct research ledger. Useful for citations. Not the decision log |

Spikes moved to [`/spikes`](../spikes). They are scripts, not the test suite.

## Not in this repo

Competitive notes were left out on purpose. This tree will likely be public. Do not add team names, handles, repo paths, or notes that point at a file in someone else's tree.

Earlier track explorations (SynapseOS as a personalized-PageRank design, plus the other two tracks and the decision matrix) are not here. Sheldon is Track 02 as `REPORT.md` describes it. The product name is Sheldon, not SynapseOS.

Paths inside the older files still say `research/` and `spikes/` as if they lived at the repo root. They now live at `docs/research/` and `spikes/`.
