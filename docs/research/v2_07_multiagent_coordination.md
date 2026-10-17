> **Precedence:** [`REPORT.md`](../decisions/REPORT.md) and [`check.md`](../decisions/check.md) override this file. They are the 17 Oct 2026 verdict.

# Multi-Agent Coordination and Shared State on FalkorDB (Round 2)

**Claim prefix:** M6-  **Research date:** 2026-10-15
**Method:** Built on FalkorDB facts fetched from `docs.falkordb.com/design/concurrency.md` and `docs.falkordb.com/commands/graph.copy.md` on this date. Coordination-pattern sources (Hearsay-II, blackboard architecture) were not re-fetched this pass; those rows are carried from round 1 and marked.

---

## 1. The one engine fact that matters most

Fetched from https://docs.falkordb.com/design/concurrency.md:

> "FalkorDB uses a per-graph reader-writer model: many read queries can run in parallel against the same graph, while write queries are serialized so that only one write executes at a time on a given graph."

> "Every query that modifies the graph — using any combination of `CREATE`, `SET`, `DELETE`, or `MERGE` — is **atomic**. The entire query either succeeds completely or fails without applying any partial changes."

Combined, these two sentences mean: **a single `GRAPH.QUERY` that reads a task's lease field and writes a claim to it cannot be double-claimed by two concurrent agents.** Write serialization gives us a line of execution shared per graph, and single-query atomicity gives us indivisibility. No external lock, no Redis `SETNX`, no distributed lease service.

This is a stronger and more defensible claim than anything in round 1, because it is quoted from the engine's own docs rather than inferred from Redis folklore.

### The precise atomicity boundary

Round 1 claimed the task-lease query is atomic "via Redis's single-threaded event loop". Correct in outcome, wrong in mechanism. The docs describe a **thread pool with parallel reads and a serialized FIFO write queue**, not a single-threaded event loop.

More importantly, the docs state the boundary explicitly:

> "FalkorDB does not natively support multi-query transactions. For cases where multiple independent queries must all succeed or fail together, use Redis `MULTI`/`EXEC` blocks. Note that this serializes all enclosed commands across all graphs."

**Design rule:** anything that must be a transaction has to be ONE Cypher query. Read-check-write, lease-then-renew, checkout-then-commit, and "is this edge already claimed" patterns that span two queries are NOT protected and can race. Design every coordination primitive so it is a single query with parameters.

## 2. Atomic task leasing — verified-correct pattern

Because writes are serialized and each query is atomic, the lease query below is genuinely safe. Note it must be sent as ONE query.

```cypher
MATCH (t:Task {status: 'READY'})
WHERE t.lease_expiry < timestamp() OR t.lease_expiry IS NULL
WITH t ORDER BY t.priority DESC LIMIT 1
SET t.status = 'IN_PROGRESS',
    t.claimed_by = $agent_id,
    t.lease_expiry = timestamp() + $lease_duration_ms
RETURN t.id AS task_id, t.spec AS spec
```

**Correctness argument (grounded in the fetched docs):** two agents issuing this concurrent write queries are serialized. The first runs to completion, setting `status = 'IN_PROGRESS'`. The second then executes against the post-write state, so its `MATCH (t:Task {status: 'READY'})` no longer matches the claimed node and it either returns a different task or no rows. Atomicity guarantees the `MATCH`+`SET` pair cannot interleave.

**Verified gotcha that affects this query:** from the cheat sheet, "When a relationship in a pattern is never referenced elsewhere, FalkorDB only verifies that at least one match exists." For node matches this is not an issue, but if we ever extend lease logic to traverse edges inside the same query, we must bind and reference the relationship alias or we will silently operate on one arbitrary edge rather than all of them.

### Lease renewal

```cypher
MATCH (t:Task {id: $task_id, claimed_by: $agent_id, status: 'IN_PROGRESS'})
SET t.lease_expiry = timestamp() + $lease_duration_ms
RETURN t.lease_expiry AS new_expiry
```

### Expired-lease reclaim

```cypher
MATCH (t:Task {status: 'IN_PROGRESS'})
WHERE t.lease_expiry < timestamp()
SET t.status = 'READY', t.claimed_by = null, t.lease_expiry = null
RETURN t.id AS recovered_task_id
```

**Caution on `timestamp()` units:** the docs list `timestamp()` as a scalar function but I did not fetch its unit (milliseconds vs nanoseconds). Determine it empirically before using `+ $lease_duration_ms` constants. An off-by-1000 here silently breaks every lease.

## 3. Speculative sandboxing — GRAPH.COPY

Fetched from https://docs.falkordb.com/commands/graph.copy.md:

- Usage `GRAPH.COPY <src> <dest>`.
- "The copy reflects a consistent snapshot of the source graph at the time the command begins. Modifications to the source graph during the copy will not affect the destination."
- "GRAPH.COPY creates a complete clone of the source graph including all nodes, relationships, properties, indexes, and constraints."
- "The source graph remains fully accessible for both reads and writes during the copy operation."
- Copy to an existing destination key returns an error; delete it first with `GRAPH.DELETE`.

```bash
GRAPH.COPY blackboard:workspace_01 sandbox:coder_01_42
```
```python
graph_z = graph_a.copy('sandbox:coder_01_42')
```

**Speculative execution workflow:**

1. Planner writes task and constraint nodes to `blackboard:{workspace}`.
2. Engine issues `GRAPH.COPY blackboard:{workspace} sandbox:{agent}_{task}`.
3. Executing agent works only inside the sandbox graph.
4. On success, the delta written in the sandbox is replayed to the blackboard as one atomic query (see the write ordering note below).
5. On failure, `GRAPH.DELETE sandbox:{agent}_{task}`; the blackboard is untouched.

**Two real limitations, both documented:**

- **The copy is a snapshot at copy time, not live.** Writes the blackboard receives during the sandbox run are not in the sandbox. On merge, those concurrent writes are not automatically reconciled. Our merge step must be written as a single query keyed on node identity, and a last-write-wins policy must be stated explicitly. This is a genuine design cost and should be disclosed honestly in the README rather than glossed.
- **Latency is not documented.** The docs give no figure. Round 1's "sub-second for typical agent memory graphs (< 100k nodes)" has no source. We must measure it on our own graph size and report the measurement with the dataset size stated.

**Merge ordering, from the concurrency page:** "Filters after a `WITH` boundary observe the state produced by any preceding write operation." So a merge query can `MERGE` a node and then `MATCH` against the just-written state inside the same query, and it is atomic as a whole. That is the correct way to build the sandbox-to-blackboard merge.

## 4. Graph-delta handoffs

Round 1's design stands: agents query the specific subgraph they need rather than receiving a prompt dump.

```cypher
// Downstream agent asks: what do I depend on?
MATCH (t:Task {id: $my_task_id})-[:REQUIRES]->(a:Artifact)
RETURN a.id, a.type, a.content, a.confidence, a.created_by
ORDER BY a.created_at DESC
```

**Doc-grounded advantage:** `GRAPH.RO_QUERY` (read-only query) "errors if the query attempts any write", which gives a cheap safety boundary for read-only agents. And because reads run in parallel and are snapshot-isolated, a downstream agent reading mid-handoff never sees partial state.

**Unverified:** round 1's "~96% token savings" figure is an estimate with no experimental backing. Round 1's own audit already flagged it. Do not quote the percentage in a submission. Quote the mechanism (targeted query vs full dump) and, if we want a number, measure it ourselves and publish the measurement.

## 5. Concurrency scaling posture (verified)

| Property | Documented behavior | Consequence for our build |
|---|---|---|
| Parallel reads | Many read queries run concurrently per graph, pool sized by `THREAD_COUNT` | Retrieval-heavy agent loops scale well |
| Serialized writes | One write at a time per graph, FIFO | Write throughput is bounded; batch multiple changes into one query |
| Write-heavy warning | "Write-heavy workloads are bottlenecked by write serialization" | Agent memory ingestion should be batched, not per-fact |
| Multi-query transactions | Not native; `MULTI`/`EXEC` blocks **all graphs** | Avoid `MULTI`/`EXEC` for coordination; use single queries |
| Cross-graph isolation | Named graphs, listed by `GRAPH.LIST` | Per-tenant and per-agent isolation is structural, not a WHERE clause |

**Documented consequence we should design around:** because `MULTI`/`EXEC` serializes across ALL graphs, using it for a transaction would freeze every tenant's graph for the duration. So coordination correctness must come from single-query atomicity, not from Redis transactions. This is a real constraint and worth stating in the blog post as a design decision with reasons.

## 6. Prior art on coordination patterns (carried from round 1, not re-verified)

- Blackboard architecture originates in Hearsay-II (Erman et al., 1980, Carnegie Mellon University).
- Classic components: blackboard (shared store), knowledge sources (specialist agents), control shell (scheduler).
- O(N^2) peer-to-peer message passing is the naive alternative; the blackboard replaces pairwise messaging with a single shared surface.
- Graph-delta handoff as a concept is our design, not a documented prior system.

These are reasonable historical claims but were not re-fetched this pass. If they appear in the blog post, re-fetch a source for Hearsay-II first.

## 7. What we build that is not already shipped

| Capability | Documented prior art | Our claim |
|---|---|---|
| Per-user graph isolation | mem0-falkordb plugin; Graphiti `graph_name` | **Already exists. Do not claim as novel.** |
| Temporal episode memory | Graphiti on FalkorDB | **Already exists. Do not claim as novel.** |
| Atomic task leasing in one Cypher query | Not found on any fetched page; follows from documented engine semantics | Ours, with the engine guarantee quoted as justification |
| Sandboxed speculative execution via GRAPH.COPY | GRAPH.COPY documented as a clone command; no fetched page describes agent sandboxing | Ours as an application of a documented primitive |
| Procedural memory as action DAGs | Not found | Ours |
| Graph-delta handoffs | Not found | Ours |

## Claims table

| ID | Claim | Source URL | Status | Notes |
|---|---|---|---|---|
| M6-01 | Per-graph reader-writer model: parallel reads, serialized FIFO writes | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M6-02 | Every write query is atomic, including schema changes | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M6-03 | Readers get snapshot isolation; never see partial writes | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M6-04 | No native multi-query transactions; MULTI/EXEC serializes across all graphs | docs.falkordb.com/design/concurrency.md | VERIFIED | Drives the single-query design rule |
| M6-05 | Write-heavy workloads are bottlenecked by write serialization | docs.falkordb.com/design/concurrency.md | VERIFIED | |
| M6-06 | GRAPH.COPY yields a consistent snapshot; source stays accessible; copies indexes and constraints | docs.falkordb.com/commands/graph.copy.md | VERIFIED | |
| M6-07 | GRAPH.COPY to an existing destination errors | docs.falkordb.com/commands/graph.copy.md | VERIFIED | |
| M6-08 | Filters after a WITH boundary observe preceding writes in the same query | docs.falkordb.com/design/concurrency.md | VERIFIED | Enables atomic merge |
| M6-09 | GRAPH.RO_QUERY errors on write attempts | docs.falkordb.com/cypher/cheat-sheet.md | VERIFIED | Read-only agent boundary |
| M6-10 | Task-lease query is race-free under concurrent agents | docs.falkordb.com/design/concurrency.md | VERIFIED (by composition of M6-01 + M6-02) | Mechanism is serialized writes, not a single-threaded event loop |
| M6-11 | Hearsay-II (Erman et al., 1980, CMU) introduced the blackboard | (not fetched this pass) | UNVERIFIED | Carried from round 1 |
| M6-12 | Graph-delta handoffs save ~96% tokens vs prompt dumps | (no source) | UNVERIFIED — DO NOT QUOTE | Round 1 estimate; measure ourselves |
| M6-13 | GRAPH.COPY latency is sub-second for < 100k-node graphs | (not in docs) | UNVERIFIED — DO NOT QUOTE | No figure exists in the docs |
| M6-14 | `timestamp()` returns milliseconds | (unit not captured) | UNVERIFIED | Must be determined empirically |
| M6-15 | No prior system ships atomic task leasing, procedure DAGs, or graph-delta handoffs on FalkorDB | (absence across pages fetched) | UNVERIFIED (negative) | Absence of evidence across the pages fetched, not a proof |

## Could not verify

- `timestamp()` unit.
- Any latency figure for GRAPH.COPY or any algorithm.
- Exact YIELD fields for every algorithm besides `algo.pageRank`.
- Whether any public project already implements Cypher task leasing on FalkorDB (searched docs only, not the wider ecosystem).
- Hearsay-II citation details.

## Coordination log

- 2026-10-15 main agent. Round-2 subagent assignments were interrupted.
- Round-1 file `research/04_AGENT_COORDINATION_AND_HANDOFFS.md` left unmodified; corrections recorded here:
  - "FalkorDB serializes commands through a single-threaded event loop" → corrected to "per-graph reader-writer model with a thread pool and a serialized FIFO write queue; reads are parallel, not single-threaded".
  - "Write queries: Serialized through the primary. Prevents race conditions without explicit locking" → the conclusion holds, but the mechanism is documented serialization plus atomic single queries, not Redis folklore.
  - The ~96% token-savings table and the sub-100ms latency claims are unverified estimates and should not be published as numbers.
- Highest-value next step for the team: build the task-lease query first and empirically test two concurrent claimers, because it is the cheapest demo of our core differentiator and the engine docs already justify it.
