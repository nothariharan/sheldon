# Docs

Read in this order:

1. [`decisions/REPORT.md`](decisions/REPORT.md) — what Sheldon is, the frozen scope, the three-part lead, the image pin.
2. [`decisions/check.md`](decisions/check.md) — the claims table and the drop list.
3. [`../AGENTS.md`](../AGENTS.md) — how to work in this repo.
4. The area `AGENTS.md` next to the code you are about to touch.

**Precedence:** `REPORT.md` and `check.md` override everything under `design/` and `research/`. Those older files still contain superseded sentences. A banner on the file is the warning. The corrected line, where we changed one, is the one to follow.

## Map

| Path | What it is |
|---|---|
| `decisions/REPORT.md` | 17 Oct 2026 verdict. Source of truth for scope |
| `decisions/check.md` | Claims table (verified / wrong / unverified) and the drop list |
| `engine/features.md` | FalkorDB feature list with doc links. Read before guessing that a command exists |
| `engine/papers.md` | Papers for the lead. Each one notes the FalkorDB version it was checked against |
| `design/PLAN_SHELDON.md` | Build plan. p0–p4 are in scope. p5–p7 and the copy sandbox are cut |
| `design/stuff.md` | Graph model and the read/write paths the plan points at |
| `design/FALKORDB_ARCHITECTURE.md` | Engine background. The PageRank row was wrong and is corrected |
| `design/SHELDON_REPORT.md` | Longer product note from 15 Oct. Scope in `REPORT.md` wins |
| `research/` | 15 Oct research ledger. Useful for citations. Not the decision log |

Spikes moved to [`/spikes`](../spikes). They are scripts, not the test suite.

## Not in this repo

`learnings.md` and the other competitive notes were left out on purpose. This tree will likely be public. Do not add team names, handles, repo paths, file/line notes, or overlap maps.

Earlier track explorations (SynapseOS as a personalized-PageRank design, plus the other two tracks and the decision matrix) are not here. Sheldon is Track 02 as `REPORT.md` describes it. The product name is Sheldon, not SynapseOS.

Paths inside the older files still say `research/` and `spikes/` as if they lived at the repo root. They now live at `docs/research/` and `spikes/`.
