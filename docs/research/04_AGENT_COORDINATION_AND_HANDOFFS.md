> **Precedence:** [`facts.md`](../facts.md), [`REPORT.md`](../decisions/REPORT.md), and [`papers.md`](../engine/papers.md) override this file.

# Multi-Agent Coordination & State Sharing: Research & Design
**Track 02 — Agent Memory and Coordination**  
**Status:** Research Complete (verified via web search + academic papers, Oct 15 2026)  
**Last Updated By:** Main agent

---

## 1. The Coordination Problem: Why Naive Approaches Fail

### 1.1 The O(N²) Peer-to-Peer Message Passing Problem
In naive multi-agent LLM systems, agents communicate directly with each other. Each agent sends its full state to every agent it collaborates with:
- **N = 5 agents:** 20 directed message channels
- **N = 10 agents:** 90 directed message channels
- **Coordination overhead:** O(N²)

**Concrete failure modes:**
1. **Context Explosion:** Each agent receives messages from 4-9 peers. If each peer message is ~5,000 tokens, the agent's context is instantly dominated by coordination overhead rather than task content.
2. **Message Storms:** Agents broadcasting state updates simultaneously can overwhelm LLM inference queues.
3. **Conflicting Facts:** Without a single source of truth, Agent A and Agent B may operate on different beliefs about the same task status.
4. **No Auditability:** A 20k-token dump of peer agent outputs is not auditable or traceable.

### 1.2 The Blackboard Architecture: Origin & Modernization
**Origin:** The **Hearsay-II** speech understanding system (Erman et al., 1980, Carnegie Mellon University). First formal use of a "blackboard" as a shared workspace for multiple knowledge sources.

**Classic Blackboard Components:**
1. **Blackboard:** Centralized, globally-readable/writable shared data store. All agent hypotheses, partial results, and task status posted here.
2. **Knowledge Sources (KS):** Autonomous specialist agents. Each monitors the blackboard for opportunities to apply its expertise.
3. **Control Shell:** Scheduler that selects which knowledge source to activate next based on blackboard state.

**Modern LLM-Era Translation to FalkorDB:**
| Classic Component | SynapseOS Implementation |
|---|---|
| Blackboard | `blackboard:{workspace_id}` named graph in FalkorDB |
| Hypotheses / Partial Results | `:Artifact` nodes with typed content and confidence scores |
| Task Queue | `:Task` nodes with `status`, `priority`, `lease_expiry` properties |
| Constraints | `:Constraint` nodes linked to `:Task` and `:Artifact` via `:DEPENDS_ON`, `:BLOCKS` edges |
| Knowledge Sources | Specialized LLM agents (Planner, Coder, Reviewer, Researcher) |
| Control Shell | Cypher-based atomic task leasing (see Section 3) |

---

## 2. Shared State Architecture

### 2.1 Graph Schema for the Blackboard

```cypher
// Task nodes
(:Task {
    id: string,
    spec: string,            // Natural language task description
    status: 'READY' | 'IN_PROGRESS' | 'DONE' | 'FAILED' | 'BLOCKED',
    priority: float,         // 0.0 (low) to 1.0 (critical)
    claimed_by: string,      // agent_id, null if unclaimed
    lease_expiry: int,       // timestamp() + lease_duration_ms
    created_at: int,
    completed_at: int
})

// Artifact nodes — outputs agents produce
(:Artifact {
    id: string,
    type: 'CODE' | 'ANALYSIS' | 'PLAN' | 'DATA' | 'DECISION',
    content: string,
    embedding: vecf32[1536], // semantic vector for similarity retrieval
    created_by: string,      // agent_id
    created_at: int,
    confidence: float
})

// Relationships
(:Task)-[:PRODUCES]->(:Artifact)
(:Task)-[:DEPENDS_ON]->(:Task)      // dependency ordering
(:Task)-[:REQUIRES]->(:Artifact)    // prerequisite artifacts
(:Artifact)-[:BLOCKS]->(:Task)      // artifact is needed before task can proceed
(:Agent)-[:CLAIMED]->(:Task)        // lease tracking
```

### 2.2 Agent Nodes for Coordination Awareness

```cypher
(:Agent {
    id: string,           // e.g., "agent:planner:instance_01"
    type: string,         // 'planner' | 'coder' | 'reviewer' | 'researcher'
    status: string,       // 'idle' | 'busy' | 'offline'
    last_heartbeat: int,  // timestamp of last heartbeat update
    capabilities: [string] // list of task types this agent can handle
})
```

---

## 3. Atomic Task Leasing (VERIFIED PATTERN)

The core coordination primitive: **one agent claims one task atomically, preventing duplicate work.**

```cypher
// Atomic task acquisition — run by each agent when idle
MATCH (t:Task {status: 'READY'})
WHERE t.lease_expiry < timestamp() OR t.lease_expiry IS NULL
WITH t ORDER BY t.priority DESC LIMIT 1
SET t.status = 'IN_PROGRESS', 
    t.claimed_by = $agent_id, 
    t.lease_expiry = timestamp() + $lease_duration_ms
RETURN t.id AS task_id, t.spec AS spec
```

**Why this is atomic:** FalkorDB (via Redis) serializes commands through a single-threaded event loop. A `GRAPH.QUERY` is processed as an atomic unit. Two agents simultaneously executing this query will not both claim the same task — one will see `LIMIT 1` return the task and claim it; the other will see no unclaimed tasks (or claim a different one).

### 3.1 Lease Renewal (Heartbeat)
Running agents renew their lease every N seconds to signal liveness:

```cypher
// Agent heartbeat — extend lease if still working
MATCH (t:Task {id: $task_id, claimed_by: $agent_id, status: 'IN_PROGRESS'})
SET t.lease_expiry = timestamp() + $lease_duration_ms
RETURN t.lease_expiry AS new_expiry
```

### 3.2 Crash Recovery — Expired Lease Reclaim
Background supervisor or any idle agent can reclaim expired leases:

```cypher
// Find and reset orphaned tasks (agent crashed without completing)
MATCH (t:Task {status: 'IN_PROGRESS'})
WHERE t.lease_expiry < timestamp()
SET t.status = 'READY',
    t.claimed_by = null,
    t.lease_expiry = null
RETURN t.id AS recovered_task_id
```

### 3.3 Task Completion
```cypher
// Mark task done and register output artifact
MATCH (t:Task {id: $task_id, claimed_by: $agent_id})
SET t.status = 'DONE', t.completed_at = timestamp()
CREATE (a:Artifact {
    id: $artifact_id,
    type: $artifact_type,
    content: $content,
    created_by: $agent_id,
    created_at: timestamp(),
    confidence: $confidence
})
CREATE (t)-[:PRODUCES]->(a)
RETURN a.id AS artifact_id
```

---

## 4. Speculative Sandboxing via GRAPH.COPY

**Problem:** A planner agent wants to simulate a risky plan before committing it to the shared blackboard. If the plan fails, the blackboard state must remain clean.

**Solution:** `GRAPH.COPY` creates an isolated branch for experimentation.

```
GRAPH.COPY blackboard:workspace_01 sandbox:coder_01_{task_id}
```

**Workflow:**
1. **Planner** designs a plan on `blackboard:workspace_01` as `:Task` and `:Constraint` nodes.
2. **Engine** calls `GRAPH.COPY blackboard:workspace_01 sandbox:coder_01_{task_id}` to create an isolated sandbox.
3. **Coder Agent** executes its changes against `sandbox:coder_01_{task_id}` only.
4. **On Success:** Coder queries the delta (newly created/modified nodes) and writes them to the master blackboard:
   ```cypher
   // On sandbox: collect new artifacts
   MATCH (a:Artifact) WHERE a.created_at > $copy_timestamp RETURN a
   // Then write each artifact to master blackboard graph
   ```
5. **On Failure:** `GRAPH.DELETE sandbox:coder_01_{task_id}` — no contamination of master state.

> **⚠️ CORRECTION from Original Blueprint:** `GRAPH.COPY` does not provide native "zero-copy" semantics in the traditional OS sense (like Copy-on-Write). It creates an actual full copy of the graph data. For large graphs this takes non-trivial time. For hackathon-scale agent memory graphs (< 10k nodes), this is fast and practical.

---

## 5. Graph-Delta Handoffs vs. Prompt Dumps

### 5.1 The Problem with Prompt Dumps
Traditional agent handoff: Agent A finishes work → dumps its entire context + work history as a 15,000–25,000 token prompt → sends to Agent B.

**Problems:**
- Token cost: 25k tokens × $0.003/1k = $0.075 per handoff
- Lost-in-the-middle: Agent B fails to extract the specific 500 tokens it actually needs
- No traceability: The dump is a blob — no graph of dependencies, decisions, or provenance

### 5.2 Graph-Delta Handoffs
Agent B queries only the specific graph delta it needs:

```cypher
// Agent B queries: "What artifacts does my upstream task depend on?"
MATCH (t:Task {id: $my_task_id})-[:REQUIRES]->(a:Artifact)
RETURN a.id, a.type, a.content, a.confidence, a.created_by
ORDER BY a.created_at DESC
```

```cypher
// Agent B queries: "What decisions were made that affect my context?"
MATCH (t:Task {id: $upstream_task_id})-[:PRODUCES]->(a:Artifact {type: 'DECISION'})
RETURN a.content, a.created_by, a.created_at
```

**Benefits (VERIFIED reasoning):**
- **Token efficiency:** A targeted graph query returns 200–500 tokens of precise context vs. 20,000 token dump.
- **Auditability:** Every decision and artifact is a graph node with `created_by`, `created_at`, and `confidence` properties — fully traceable.
- **Dependency clarity:** `DEPENDS_ON` and `REQUIRES` edges make task dependencies explicit and queryable.

### 5.3 Quantified Token Savings (Estimated)
| Approach | Tokens per Handoff | Cost (at $0.003/1k) | Traceability |
|---|---|---|---|
| Full prompt dump | ~20,000 | ~$0.06 | ❌ None |
| Graph-delta query | ~300–800 | ~$0.001–0.002 | ✅ Full |
| **Savings** | **~96%** | **~97%** | ✅ |

---

## 6. High-Concurrency Read/Write Considerations

### 6.1 FalkorDB Concurrency Model
FalkorDB processes graph queries through Redis's single-threaded event loop:
- **Read queries:** Can run concurrently on read replicas.
- **Write queries:** Serialized through the primary. Prevents race conditions without explicit locking.
- **Atomic `MATCH...SET` patterns:** The task leasing query (Section 3) is inherently atomic within a single `GRAPH.QUERY` call.

### 6.2 Scaling Patterns
| Pattern | Mechanism |
|---|---|
| **Read scaling** | Redis read replicas for agent memory retrieval queries |
| **Write throughput** | Pipeline batching with `GRAPH.QUERY` — multiple writes in a single network round trip |
| **Per-tenant isolation** | Separate named graphs per user/workspace — distribute across Redis Cluster shards |
| **Async ingestion** | Background worker queue for episodic memory ingestion (prevents blocking agent loop) |

---

## 7. Coordination Summary: What We Build That Doesn't Exist

| Feature | Description | Existing Alternative |
|---|---|---|
| **FalkorDB Blackboard** | Named graph as shared workspace for N agents | LangGraph Store (flat KV only) |
| **Cypher Atomic Task Leasing** | Single Cypher `MATCH...SET` atomically claims tasks | External Redis SETNX (no graph) |
| **`GRAPH.COPY` Sandboxing** | Branch-and-merge speculative execution | Not available in any competing DB |
| **Graph-Delta Handoffs** | Targeted Cypher queries replace prompt dumps | Raw prompt copy-paste |
| **Blackboard + Memory in One DB** | Episodic/Semantic/Procedural AND coordination in same FalkorDB instance | Always two separate systems |
