# Demo script

Draft for the `demo-submit` row (Akshat). About 3 minutes, five steps, from [deep.md](deep.md) §3. Recording is Sun 18 Oct, 6–9 PM IST. Submit by 11:00 PM IST.

Ids on screen (INC-12, E-41, E-52, C-7, A-3, T-9) are seed data, not a result. Say so once, on the first id.

Each step lists the rows it needs. If a row has not landed by Sun 1 PM (eval freeze), use that step's fallback. Do not show a stub as if it ran.

## Before recording

- [ ] Every row in each step's "Needs" list is merged, or that step uses its fallback.
- [ ] Re-open the malladiphani quote's link ([quotes.md](quotes.md) #1). The wording and date match the live post, or the quote is cut.
- [ ] Reset the demo graph from the frozen seed with `GRAPH.COPY`. Same seed for every take.
- [ ] FalkorDB is `falkordb/falkordb:v4.22.1`. The Browser is on `localhost:3000`.
- [ ] The step 4 numbers match the eval table exactly, or the slide says "to be measured".
- [ ] Read the narration against the wording rules in [README.md](README.md). No speed or cost number. No "revolutionary". No "production-ready".

## 0. Title (0:00–0:10)

**On screen:** the headline.

**Say:** "Sheldon blocks coding agents from retrying fixes that already failed, and from calling work done without a real test run, from the first edit to the merge, on one shared FalkorDB graph per repo."

## 1. Retry block (0:10–0:45)

**Needs:** seed (INC-12, E-41), preflight, the Claude Code `PreToolUse` hook.

**On screen:**

1. The quote card: "it kept trying the same fix and failing the same way" (@malladiphani, 5 Oct 2026).
2. Agent A in Claude Code, on the checkout repo, about to raise the cache TTL.
3. The hook's stderr:

   ```text
   blocked: refuted by E-41
   this edit repeats the cache-TTL fix tried for INC-12; E-41 (CI run) refuted it
   ```

**Say:** "Agent A is about to try the cache-TTL fix again. A CI run, E-41, already refuted that fix for INC-12. These ids are seed data. The preflight finds it in the graph and the hook blocks the edit, with the evidence id as the reason. None we found blocks a coding agent from retrying a code fix refuted in the shared graph."

**Fallback:** if the hook is not wired, run `sheldon preflight` by hand and show it returning `block` with E-41. Say "the hook is to build" out loud.

## 2. Evidence gate (0:45–1:25)

**Needs:** W3 (`claim_done`), evidence-run (`sheldon run`), the check-run webhook, pr-ingest.

**On screen:**

1. Agent B opens a PR and writes "Done, all tests pass." with `Evidence: E-52` in the PR body. It ran nothing.
2. The W3 call returning no id (0 rows).
3. The PR's `sheldon` check, red:

   ```text
   blocked: E-52 not executed
   ```

4. Agent B runs `sheldon run -- pytest`, which writes a real executed run. Agent B cites that id instead, and the check turns green.

**Say:** "Agent B says it's done and cites E-52. E-52 is not an executed test run on this commit. A model can cite evidence. It can't create it. So the claim does not land, and the check stays red, citing E-52. After a real `sheldon run`, the cited id is an executed run on this sha, and the check passes."

**Fallback:** if W3 has not landed, show only the check run going red on E-52. Do not show a W3 call. If the webhook is not live, call `decide_check` from a terminal and show the same `blocked:` line.

## 3. One-write refute and stale cascade (1:25–2:05)

**Needs:** W2 (`refute_hypothesis`), seed (C-7, A-3, T-9).

**On screen:**

1. The Browser: C-7 with approval A-3 and task T-9 relying on it.
2. New CI evidence arrives. One W2 call.
3. Its one Cypher statement next to the result: C-7 `refuted`, A-3 `stale`, T-9 `stale`. C-7 is still in the graph.
4. The PR's check now reports `stale: A-3 marked stale`.

**Say:** "New CI evidence refutes C-7. One Cypher statement marks the claim refuted and every approval and task that relied on it stale, in one atomic write. Nothing is deleted. Claims are refuted, never stale. The approval that rested on C-7 no longer counts at the check."

**Fallback:** none. W2 is critical path. If it has not landed, move this step's time to step 2.

## 4. With and without (2:05–2:40)

**Needs:** eval-def, eval-count. At least 3 runs per arm, each reset from one frozen `GRAPH.COPY`.

**On screen:** one table: pass rate and total tokens, same model, with and without Sheldon, with the spread.

**Say:** "Same tasks, same model, at least three runs per arm, each from the same frozen copy." Then read the result with the approved phrase. Say "safer at the same quality" unless the margin beats a 1-task gap across at least 3 runs per arm.

**Fallback:** if there are fewer than 3 runs per arm, the slide says "to be measured", and the line is "safer at the same quality: a cheaper model cannot land anything it cannot prove." Do not show a partial number.

## 5. If time: under the hood (2:40–3:00)

**Needs:** ingest, R1 recall (merged), the provenance read.

**On screen:** the repo graph in the Browser. A PR touching `checkout/cache.py` with the R1 line `refuted: C-7 by E-41 (INC-12, via checkout/session.py)`. The provenance query showing the model and session on each write.

**Say:** "Repo mapping builds on FalkorDB code-graph and RepoGraph. At PR time, one bounded read walks from the changed file to the incident, the claim, and the evidence that refuted it. Every write records the model and session that made it."

**Fallback:** cut this step first if time runs short (work-split.md).

## Close (last 5 seconds)

**On screen:** repo URL and team name, SheldonAI.

**Say:** nothing new. No claim that is not in steps 1–4.
