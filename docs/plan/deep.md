# Sheldon: the deep plan

Team SheldonAI: Akshat Bhaskar (lead), Hariharan, Amaan Khan, Satyansh Gaur. Graph Hacks (WeMakeDevs × FalkorDB), Track 02. Written Sat 17 Oct 2026. Submission closes Sun 18 Oct 2026, 11:59 PM IST.

How to read status. **Ran** means it ran. **To build** means it is in Sunday's scope and the function in this repo does not do it yet. **Roadmap** means after the hackathon. **To measure** means we state it only after our own with/without run has numbers. Paper numbers motivate the design. They are never Sheldon's results. X dates are UTC. Other times are IST.

The short index is [README.md](README.md). Owners and times are [work-split.md](work-split.md). Quotes are [quotes.md](quotes.md).

## 0. Headline

Sheldon blocks coding agents from retrying fixes that already failed, and from calling work done without a real test run, from the first edit to the merge, on one shared FalkorDB graph per repo.

A claim or approval only lands if every evidence id it cites is a real executed run. Refuting evidence marks the claim refuted, and every approval and task that relied on it goes stale, in one atomic write. Nothing marks a claim stale. None we found blocks a coding agent from retrying a code fix refuted in the shared graph.

Memory is how, not what. The three mechanisms need the graph to remember what failed, what was claimed, and what relied on what, across agents, sessions, and PRs. That memory is the mechanism. It is not the headline.

## 1. The three mechanisms

**Retry block.** Before an agent edits a file or runs a command, a preflight asks whether this action repeats a fix that executed evidence already refuted. If it does, the action is blocked and the reason is the refuting evidence id (`blocked: refuted by E-41`). Narrower retry blocks exist in other domains, so the claim stays at this wording: none we found blocks a coding agent from retrying a code fix refuted in the shared graph.

**Evidence gate.** A claim ("done", "fixed", "root cause is X") or an approval lands only if every evidence id it cites is a run that actually executed on that commit. A model can cite evidence. It cannot create it. Trusted producers (`sheldon run`, CI webhooks) write Evidence nodes. None we found requires every cited evidence id to be an executed run for a claim or an approval to land on a shared multi-agent graph.

**One-write refute plus stale cascade.** When executed evidence refutes a claim, one Cypher statement marks the claim refuted and every approval and task that relied on it (up to 3 hops) stale. Nothing is deleted. Claims are refuted, never stale. Pushing corrections to dependents is common. Doing it in one atomic write that reaches code-merge approvals is the part none we found does.

## 2. Stations

| Station | Mechanism | Status |
|---|---|---|
| Ingest and capsule | `sheldon ingest` writes the code and history graph. The capsule is re-injected at session start, after compaction, and at subagent start. | to build (ingest, capsule). code-graph structural import is roadmap |
| House standards | Gates enforce refuted-fix, done-needs-a-run, and approval-cites-evidence. | W1 query ran. The rest is to build or roadmap |
| Evidence gate W1 / W3 | "Done" and approvals land with an executed run on that sha. | W1 query ran. W3 is to build |
| Retry block R2 | Preflight through a PreToolUse hook. | to build |
| Cascade W2 | One atomic write refutes the claim and stales approvals and tasks. | W2 query ran. The function in this repo is to build |
| Claim, lease, resume, provenance | Atomic claims, a resume of what was tried, model and session on every write. | to build |
| PR check run | Last gate before merge. | R1 query ran. Webhook, pr-ingest, and the check run are to build |
| Cheaper models, safely | The gate holds whatever model is cooking. | to measure |

### 2.1 Ingest and capsule (to build)

Repo mapping is not ours. It builds on FalkorDB code-graph (MIT) and the File / Commit / `CO_CHANGED_WITH` vocabulary of FalkorDB RepoGraph (MIT). We reuse those names and credit them.

Graph written by ingest:

```text
(:Developer)-[:AUTHORED]->(:Commit {hash, message, timestamp})
(:Commit)-[:MODIFIED {additions, deletions}]->(:File {path, extension, language})
(:File)-[:CO_CHANGED_WITH {frequency}]->(:File)
(:File)-[:PART_OF]->(:Module)
(:File)-[:BELONGS_TO]->(:Repository)
```

The capsule is a short block: do-nots from refuted attempts that touch the current task, plus the command that proves the work. Claude Code hooks: `SessionStart` for startup, resume, clear, and compact, and `SubagentStart` because SessionStart context reaches the parent thread. Hook install is adapted from ponytail (MIT, notice kept). Structural calls/imports from code-graph are roadmap.

### 2.2 Evidence gate

**W1 ran** on 4.18.3 and v4.22.1. It refuses unexecuted, missing, empty, and duplicate ids, and wrong-sha ids on v4.22.1. Valid ids create 1 `FOR` and 2 `CITES`. `tests/gate/test_approve.py` shows `approve` doing that on v4.22.1.

```cypher
MATCH (pr:PR {number:$pr, head_sha:$sha})
MATCH (e:Evidence) WHERE e.id IN $ids AND e.executed = true AND e.sha = $sha
WITH pr, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
CREATE (a:Approval {id:$aid, by:$by, actor_kind:$kind, sha:$sha, status:'active',
                    at:timestamp(), model:$model, session:$session})-[:FOR]->(pr)
FOREACH (x IN ev | CREATE (a)-[:CITES]->(x))
RETURN a.id
```

**W3 is to build.** Same shape, on `Claim {kind:'done'}`, needing a `test_run` with `exit_code = 0` on the current tree sha. `$ids` are de-duplicated in the client. Zero rows means refused: missing, unexecuted, or wrong-sha evidence. `sheldon run` is to build. A Stop hook that refuses "done" is roadmap.

Trust rule: `sheldon run -- <cmd>` and CI `check_run.completed` are the Evidence writers. A model saying "all tests pass" without one of those nodes is text, and the gate returns 0 rows.

### 2.3 Retry block (to build)

R2 is read-only, through `GRAPH.RO_QUERY` with a timeout. It asks whether the action fingerprint (normalized command plus touched files) matches an `Action` on a refuted claim, and whether a touched file belongs to an open incident. The answer is `ok`, `warn`, or `block`, plus ids.

Claude Code `PreToolUse` on Edit, Write, and Bash calls `sheldon preflight`. Exit code 2 blocks the tool and puts the reason on stderr:

```text
blocked: refuted by E-41
this edit repeats the cache-TTL fix tried for INC-12; E-41 (CI run) refuted it
```

`sheldon-mcp` exposes `preflight` for hosts that call tools. Fingerprint match is exact. The `sameAction` JS UDF was tested as our own library on 4.22.1 and 6.0.1. Wiring it is roadmap. Do not change the image pin to load it. FLEX is not preloaded and is not needed. Fail-closed for commit, push, and "done". Fail-open for reads, so an outage does not freeze the agent. Other hosts are roadmap.

### 2.4 Cascade

**W2 ran** on 4.18.3 and v4.22.1. On valid executed evidence it refutes the claim and stales dependents at up to 3 hops in one statement. It refuses unexecuted evidence. `tests/belief/test_refute.py` shows `refute_claim` doing that on v4.22.1. The Cypher file `queries/refute_hypothesis.cypher` is the older sketch and stays, because a contract test locks its text. The statement that ran is `queries/refute_claim.cypher`:

```cypher
MATCH (c:Claim {id: $cid})
MATCH (e:Evidence) WHERE e.id IN $ids AND e.executed = true
WITH c, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
SET c.status = $refuted,
    c.confidence = c.confidence - $alpha,
    c.refuted_at = timestamp()
FOREACH (x IN ev |
  CREATE (c)-[:REFUTED_BY {agent: $agent, model: $model, session: $session, at: timestamp()}]->(x)
)
WITH c
OPTIONAL MATCH (c)<-[:RELIES_ON|DEPENDS_ON*1..3]-(d)
WHERE d IS NOT NULL AND NOT d:Claim AND d.status IN $live
WITH c, collect(DISTINCT d) AS deps
FOREACH (x IN deps |
  SET x.stale_because = c.id,
      x.status = CASE WHEN x:Task THEN x.status ELSE $stale END,
      x.stale = CASE WHEN x:Task THEN true ELSE x.stale END
)
RETURN c.id AS id, size(deps) AS staled
```

W2 marks an approval's status stale. A task keeps its status and gets the boolean `stale`. It does not mark a PR stale by itself. A PR whose approval went stale loses that approval at the check run. Nothing is deleted. Claims are refuted, never stale.

### 2.5 Claim, lease, resume, provenance (to build)

Claim is one conditional write: the task is open, or its lease has expired, and it has no unfinished dependencies. Heartbeat, complete, and handoff stay one statement each and affect a task this agent holds. Resume is a read: tried, failed and why, believed, next, with ids. Provenance stores the model, as the host reported it, and the session, on every Event, Claim, Evidence, Approval, and Action.

### 2.6 PR check

**R1 ran.** It returns incident, claim, and evidence rows. Webhook, pr-ingest, and the check run are to build (Akshat and Amaan).

```cypher
MATCH (pr:PR {number:$pr})-[:CHANGES]->(f:File)
OPTIONAL MATCH (f)-[:CO_CHANGED_WITH*0..1]-(g:File)<-[:TOUCHED]-(i:Incident)-[:HAS_CAUSE]->(c:Claim)
OPTIONAL MATCH (c)-[r:SUPPORTED_BY|REFUTED_BY]->(e:Evidence)
RETURN f.path, i.id, i.title, c.id, c.kind, c.status, type(r), e.id LIMIT 50
```

`*0..1` is bounded. Do not open it into an unbounded walk.

The check is silent by default. It blocks with a cited reason: an evidence id and a path. It re-checks every new sha, so an approval stamped with an older sha goes stale. It does not repeat a dismissed finding (`Finding` fingerprint). An optional cheap model may write at most one PR comment from the traversal rows. The check decision itself is Cypher, with no LLM in it.

### 2.7 Cheaper models (to measure)

Wording: "safer at the same quality". A cheaper model cannot land anything it cannot prove, and every write records which model made it. "Smarter" waits on our numbers. Until the with/without run exists, do not claim a quality or cost result.

Roadmap, not Sunday: a model allowlist on W1, escalate-on-stall, a staged harness.

## 3. Day to day

`sheldon-ai` was free on PyPI and npm on 17 Oct and is not published. The CLI command stays `sheldon`. The engine in Docker is `falkordb/falkordb:v4.22.1`. falkordblite bundles 4.18.3, so we do not claim parity with it.

`sheldon init` creates graph key `sheldon:<owner>/<repo>`, installs host hooks, and runs ingest. `sheldon run -- pytest` writes an executed Evidence node (sha, exit code, model, session). The GitHub App listens for `pull_request`, `check_run`, and review events.

Demo, about 3 minutes, five steps. Ids below are seed data, not a result.

1. Pain, then the retry block. Show the malladiphani line. Agent A tries the cache-TTL fix that INC-12's E-41 refuted. The hook exits 2.
2. The gate. Agent B claims "done, all tests pass" without running anything and cites E-52, which is not an executed test run on this sha. W3 returns 0 rows. The check stays red, citing E-52. W3 is to build, so this step waits on that row.
3. The cascade. New CI evidence refutes C-7. One W2 write marks C-7 refuted and approval A-3 and task T-9 stale.
4. With/without numbers. Pass rate and total tokens, same model, at least 3 runs per arm, with the spread. "Safer at the same quality" unless the margin clears the bar. This step is to measure.
5. If time: init and ingest in the Browser, the R1 comment on a PR touching `checkout/`, and the provenance query.

## 4. Architecture

| # | Component | Where | Status |
|---|---|---|---|
| C1 | `sheldon` Python library | everywhere | to build, except the W1, W2, and R1 queries which ran |
| C2 | CLI `init`, `ingest`, `run`, `preflight`, `incident add`, `eval` | dev machine, CI | to build |
| C3 | Claude Code hooks | Claude Code | to build. Other hosts are roadmap |
| C4 | `sheldon-mcp` stdio | local | to build. Hosted http is roadmap |
| C5 | git pre-commit | dev machine | roadmap |
| C6 | GitHub App | hosted | to build |
| C7 | Evidence producers | CLI and CI webhook | to build |
| C8 | FalkorDB `falkordb/falkordb:v4.22.1` | container | pinned. The Docker smoke test is to build beyond the module and `GRAPH.COPY` check that already runs in CI |

One graph key per repo: `sheldon:<owner>/<repo>`. Reads go through `GRAPH.RO_QUERY` with a timeout. Each gated write is one Cypher statement. No `MULTI`/`EXEC`. Constraints are a backstop. `UNIQUE` on `Claim.id` needs an exact-match index first. It rejects a duplicate `CREATE` and `SET`. `MERGE` on an existing id does not trip it, so write paths use `CREATE`. Nothing is deleted.

`GRAPH.COPY` resets the demo seed and every eval run from one frozen copy. It worked on v4.22.1. On FalkorDB Cloud it is untested. The Cloud free tier has no persistence: demo only, reseeded before judging.

Ingest, recall, the gate, the cascade, the check-run decision, and preflight use no LLM. An optional cheap model writes the one PR comment from traversal rows.

## 5. Data model

| Node or edge | Properties | Written by |
|---|---|---|
| `Developer-AUTHORED→Commit-MODIFIED→File`, `File-CO_CHANGED_WITH→File` | hash, message, timestamp, path, frequency | ingest (RepoGraph names). To build |
| `PR-CHANGES→File` | number, head_sha, status | pr-ingest. To build |
| `Incident-TOUCHED→File`, `Incident-HAS_CAUSE→Claim` | id, title, severity, at | seed and `incident add`. To build |
| `Claim` | id, text, kind (`root_cause` / `fix` / `assumption` / `done`), status (`open` / `confirmed` / `refuted`), confidence, model, session | W3 and claim. To build |
| `Claim-SUPPORTED_BY→Evidence`, `Claim-REFUTED_BY→Evidence` | Evidence: id, kind, sha, executed, exit_code, model, session | W2 ran as a query. Writers are to build |
| `Approval-FOR→PR`, `CITES→Evidence`, `RELIES_ON→Claim` | id, by, sha, status (`active` / `stale`), model, session | W1 ran as a query. Writer is to build |
| `Task-DEPENDS_ON→Claim` | id, status (`open` / `claimed` / `done` / `stale`), owner, lease_expires | claim and lease. To build |
| `Action-ATTEMPTED_FIX_FOR→Claim` | fingerprint, cmd, files | preflight. To build |
| `Finding` | fingerprint, dismissed, pr | check run. To build |

Claim status is `open`, `confirmed`, or `refuted`. A claim is never stale. Approval status is `active` or `stale`. The strings in `sheldon/schema.py` are the older set still in the file. Confirm them against this table before the demo. Do not invent a second copy in a feature branch.

Memory types, Track 02 vocabulary: incident is episodic, a confirmed cause is semantic, a refuted fix is procedural.

## 6. Eval (to build, then to measure)

Write the definition of a repeated failed step before any count is quoted. MAST-style (step repetition, FM-1.3, arXiv 2503.13657): write the rule, hand-label a sample, then automate. An optional second number is TIDE's loop ratio (redundant loop actions / total actions, arXiv 2602.02196), used as a definition only, never as a memory result. TIDE's published drop is from model scaling, not from memory.

The run: same tasks, same model, at least 3 runs per arm, each reset from one frozen `GRAPH.COPY`. Report pass rate on hidden checks, total tokens, blocked no-run claims, breakage, and refuted-fix retries, with the spread. A 1-task gap is noise. Default wording stays "safer at the same quality". Lower breakage counts when pass rate holds. A gate that blocks everything scores zero breakage and is not a win.

Published motivation, not a Sheldon result: STALE / CUPMem (arXiv 2605.06527) reports gpt-4o-mini 8.7% → 68.0% with write-time adjudication plus propagation-aware search, on the authors' own benchmark. Caption it as their number.

## 7. Honest limits

The gate is as strong as the tests it cites. Sheldon blocks evidence that is not a real executed run on that sha and makes weak evidence visible. It cannot make weak tests strong. Tamper checks are roadmap.

An agent that deletes a failing test and then runs the suite produces a real executed run. Diff-scope evidence is roadmap. See quote 5.

Hook blocking is to build for Claude Code. A git pre-commit hook can be skipped with `--no-verify`, so the PR check is the backstop. That hook is roadmap.

Most single features have equivalents in other databases. Here, variable-depth, mixed-edge-type, path-returning checks are one bounded Cypher query inside one atomic write, instead of recursive SQL over several edge tables plus application code. That is the framing. It is not a claim that the design needs FalkorDB and nothing else.

## 8. Roadmap

Stop hooks and other hosts. Many-host adapters. Diff-scope evidence. Base-fail/head-pass and a test-file hash. Callers-open evidence. code-graph structural import. Wiring `sameAction`. Model allowlist and escalate-on-stall. Staged harness. git pre-commit. Hosted MCP. FalkorDB Cloud per-repo graphs. falkordblite parity.

## 9. Wording rules

- "None we found" for anything about what others do not do.
- Do not claim the design needs FalkorDB and nothing else. No speed number we have not measured.
- No cost-saving numbers. No routing-savings claims. Cost is to measure.
- No "revolutionary". No "production-ready".
- Do not claim cheaper models match frontier models.
- Pains are what Sheldon is built for, not something it has already fixed.
- The headline is the three mechanisms, not memory.
- Credit code-graph and RepoGraph. ponytail runs alongside Sheldon.
- Recall layers advise and Sheldon enforces. They compose. Nobody is cast as the bad guy.
- Paper numbers are never Sheldon's results.
- The refused fake "done" is a demo moment, not the headline.
