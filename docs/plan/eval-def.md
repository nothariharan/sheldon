# Evaluation Definition: Repeated Failed Steps & Evaluation Protocol

This document defines the operational criteria for what constitutes a **repeated failed step**, specifies the benchmark taxonomy and hand-labelled sample cases, outlines what is automated, and formalizes the paired task evaluation protocol.

In accordance with [`TASKS.md`](../../TASKS.md), this document establishes definitions and rules only; **no empirical counts or measurement numbers are recorded in this file.**

---

## 1. Repeated Failed Step Definition

### 1.1 MAST-Style Step Repetition
Following the Multi-Agent System Failure Taxonomy (MAST; FM-1.3, step repetition failure mode, arXiv:2503.13657), an action attempt is defined as a **repeated failed step** when:

> An agent initiates an action (tool execution, shell command, or file edit) whose canonical normalized target and intent match a historical action previously attempted for a claim, where that previous attempt was refuted by an executed run (`executed = true`, non-zero exit code or failing CI/test outcome).

Formally, an attempted action $A_{new} = (cmd, paths)$ for investigation or task $T$ is classified as a repeated failed step if and only if:
1. Syntactic fingerprint $\text{fp}(A_{new}) = \text{fp}(A_{prior})$, where $A_{prior}$ is an action recorded in the knowledge graph.
2. $A_{prior} \xrightarrow{\text{ATTEMPTED\_FIX\_FOR}} C$, where $C$ is a `Claim` with property `status = 'refuted'`.
3. $C \xrightarrow{\text{REFUTED\_BY}} E$, where $E$ is an `Evidence` node with `executed = true` and `exit_code != 0` (or `kind = 'ci_run'` with failing status).

### 1.2 External Reference: TIDE Loop Ratio
TIDE (Trajectory-based Diagnostic Evaluation, arXiv:2602.02196) is an evaluation framework, not a benchmark. Its loop ratio is Eq. 4:
$$LR = \frac{\sum (j - i)}{\text{total actions}}$$
The sum is over loop segments. It counts redundant actions inside loops, not cycles.

*Boundary Notice:* TIDE reports that loop ratio drops when scaling up within one model family (Qwen3-4B to Qwen3-30B-A3B). In Sheldon, TIDE's loop ratio is referenced solely as an external definition, never as a Sheldon memory result or empirical finding.

---

## 2. Seven-Case Operational Taxonomy & Hand-Labelled Sample

To avoid ambiguity between a refuted fix, an unexecuted run, and a legitimate alternative edit to the same file, every candidate action is classified under one of seven distinct cases:

| Case | Scenario Description | Knowledge Graph State | Expected Classification | Enforcement Decision |
|---|---|---|---|---|
| **Case 1** | Exact repeat of a refuted fix | $A_{prior}$ exists on refuted $C_5$, backed by failing $E_{41}$ (`executed = true`, `exit_code = 1`) | **Repeated Failed Step** | `block` (Exit code 2) |
| **Case 2** | Syntactically equivalent fix (whitespace / relative path variation) | Normalized fingerprint matches $A_{prior}$ on refuted $C_5$ | **Repeated Failed Step** | `block` (Exit code 2) |
| **Case 3** | Different fix touching the same file | Same file path, but command / intent differs from $A_{prior}$ | **Context Overlap / Legitimate Alternative** | `warn` (Exit code 0, allowed) |
| **Case 4** | Refuted fix attempted after underlying condition changed | Action matches $A_{prior}$, but graph claim updated or override provided | **Re-evaluated / Overridden Attempt** | `warn` (Exit code 0). The override is a flag on the check. The reason names the refuting evidence. It is not written to the graph. |
| **Case 5** | Unexecuted command or missing test run | Cited evidence has `executed = false` or exit code missing | **Unverified Evidence** | Rejected by Gate (Cannot support or refute) |
| **Case 6** | Genuinely new action with clean history | No matching action fingerprint; no touched file overlap | **Clean Action** | `ok` (Exit code 0, allowed) |
| **Case 7** | Database outage | FalkorDB is unreachable or times out | **Fail closed for commit, push, and done. Fail open for reads.** | Commit, push, and done: `block` (exit 2). Reads (recall, resume, and the check summary): `warn` (exit 0). `SHELDON_FAIL_OPEN=1` makes commit, push, and done warn and exit 0. |

---

## 3. Hand-Labelled Sample Reference

The following concrete examples illustrate the 7 cases mapped to the demo seed graph:

### Sample 1: Exact Refuted Fix (Case 1)
* **Candidate Input:** `command = "edit checkout/cache.py"`, `paths = ["checkout/cache.py"]`.
* **Historical Context:** `INC-12` touched `checkout/session.py` (which co-changes with `checkout/cache.py`). Claim `C-5` ("Raising the cache TTL to 600s fixes the checkout timeout") is marked `status: 'refuted'`. Evidence `E-41` is an executed CI run (`exit_code: 1`). Action `ACT-1` has `fingerprint: "edit checkout/cache.py"`.
* **Classification:** **Repeated Failed Step (`block`)**.
* **Reason to emit (preflight is to build):** `"blocked: refuted by E-41; this edit repeats the cache-TTL fix tried for INC-12; E-41 (CI run) refuted it"`.

### Sample 2: Syntactic Variant of Refuted Fix (Case 2)
* **Candidate Input:** `command = "edit   ./checkout/cache.py"`, `paths = ["./checkout/cache.py"]`.
* **Normalization:** Canonical relative path becomes `"checkout/cache.py"`; normalized command becomes `"edit checkout/cache.py"`.
* **Classification:** **Repeated Failed Step (`block`)**.
* **Reason to emit (preflight is to build):** Matched to `ACT-1` and `C-5`, citing `E-41`.

### Sample 3: Legitimate Alternative on Same File (Case 3)
* **Candidate Input:** `command = "refactor checkout/cache.py"`, `paths = ["checkout/cache.py"]`.
* **Historical Context:** Touched file `checkout/cache.py` is associated with `INC-12`, but the command does not match `ACT-1`'s TTL modification.
* **Classification:** **Legitimate Alternative (`warn`)**. A different action after a refusal is allowed.
* **Reason to emit (preflight is to build):** Permitted with informational advisory: `"checkout/cache.py was touched in INC-12; verified alternative attempt"`.

### Sample 4: Changed Conditions / Manual Override (Case 4)
* **Candidate Input:** `command = "edit checkout/cache.py"`, `paths = ["checkout/cache.py"]`, with flag `--override` or environment variable `SHELDON_PREFLIGHT_OVERRIDE=1`.
* **Policy:** When external conditions change (e.g. cache service upgraded), Sheldon does not speculate; execution proceeds only via graph status re-opening or explicit manual override flag.
* **Classification:** **Overridden Step (`warn`)**.

### Sample 5: Unexecuted Test Run (Case 5)
* **Candidate Input:** Agent cites evidence `E-52` in PR body to claim completion.
* **Historical Context:** `E-52` exists in the graph with `executed: false`.
* **Classification:** **Unverified Evidence**.
* **Reason Emitted:** Gate W1 / W3 rejects completion claim because unexecuted runs provide zero validity proof.

### Sample 6: Clean Action (Case 6)
* **Candidate Input:** `command = "edit checkout/api.py"`, `paths = ["checkout/api.py"]`.
* **Historical Context:** `checkout/api.py` has no connection to refuted claims or open incidents.
* **Classification:** **Clean Action (`ok`)**.

### Sample 7: Database Outage (Case 7)
* **Candidate Input:** FalkorDB times out or is unreachable.
* **Classification:** **Fail closed for commit, push, and done. Fail open for reads.**
* **Decision:** Commit, push, and done return `block` and exit 2. Reads (recall, resume, and the check summary) return `warn` and exit 0. `SHELDON_FAIL_OPEN=1` makes commit, push, and done warn and exit 0.

---

## 4. What to automate (to build)

Automation will be split across the query, decision, and hook layers:

1. **Fingerprint Normalization (`sheldon/preflight.py`):**
   - to build: `sheldon/preflight.py` will canonicalize file paths relative to the repository root via `canonicalize_paths(paths, repo_root)` and reject traversal outside the repository root.
   - to build: `normalize_command(command)` will normalize whitespace in commands.
   - to build: `compute_action_fingerprint(command, paths, repo_root)` will compute a deterministic syntactic action fingerprint.
2. **Query Layer (`queries/preflight_r2.cypher`):**
   - to build: `queries/preflight_r2.cypher` will evaluate whether an action fingerprint matches an action linked to a refuted claim backed by executed non-zero evidence (`executed = true AND exit_code != 0`).
   - to build: the query will identify whether touched file paths intersect past incidents.
   - to build: the query will enforce `timeout_ms = 1000` via `GRAPH.RO_QUERY`.
3. **Decision Layer (`sheldon.preflight.decide_preflight`):**
   - to build: `decide_preflight` will map query results into `ok`, `warn`, or `block` with cited evidence IDs and incident IDs.
4. **Hook Integration Layer (`sheldon/preflight.py` CLI):**
   - to build: the CLI hook will read Claude Code `PreToolUse` JSON payloads from stdin.
   - to build: the hook will exit code `2` on `block` with explanatory text on stderr, and exit code `0` on `ok` and `warn`.

---

## 5. Paired Evaluation Methodology

When the empirical evaluation is executed (Sunday afternoon), runs will adhere to the following protocol:

### 5.1 Experimental Arms
* **S0 (Baseline Memory):** Standard coding agent with keyword/vector memory, without graph traversal, evidence gates, or preflight retry hooks.
* **S3 (Sheldon Full System):** Identical coding agent equipped with Sheldon's PreToolUse retry block, evidence gate (W1/W3), and session capsule.
* **S1 (Ablation Arm - Optional):** Baseline agent with PreToolUse retry block only, isolating the specific contribution of retry prevention.

### 5.2 Paired Task Matrix
Every task $T_i$ ($i \in \{1 \dots N\}$) is evaluated under both S0 and S3 on identical starting repositories. Individual task outcomes are recorded as pairs $(S0_i, S3_i)$:
* **Improved:** $S0_i = 0$ (failed), $S3_i = 1$ (passed).
* **Regressed:** $S0_i = 1$ (passed), $S3_i = 0$ (failed).
* **Preserved Pass:** $S0_i = 1$ (passed), $S3_i = 1$ (passed).
* **Preserved Fail:** $S0_i = 0$ (failed), $S3_i = 0$ (failed).

### 5.3 Metric Formulas & Definitions
* **Task Pass Rate:**
  $$\text{Pass Rate} = \frac{\sum_{i=1}^N \mathbb{I}(\text{Task } i \text{ passes hidden test suite})}{N}$$
* **Invalid Completion Attempts:** Count of submitted "done" claims lacking verified, executed passing test evidence on the head SHA.
* **Invalid Completions Prevented:** Count of invalid completion attempts rejected by the evidence gate.
* **Refuted-Fix Retries:** Count of attempted actions matching historically refuted claims.
* **Retry Blocks:** Count of refuted-fix retries intercepted and prevented by the PreToolUse hook.
* **Regression Count:** Number of previously passing repository tests that fail after agent modification.
* **False-Block Rate:**
  $$\text{False-Block Rate} = \frac{\text{Legitimate non-refuted actions blocked}}{\text{Total legitimate actions evaluated}}$$

### 5.4 Execution & Isolation Protocol
* Each run resets from one frozen `GRAPH.COPY` snapshot (`sheldon:seed:demo`).
* Working directory cleanups (`git clean -fdx`) run strictly in a dedicated disposable evaluation directory, preserving the integrity of the primary clone.
* Raw counts, per-run results, and min–max spread are recorded across at least 3 runs per arm.
* Quality framing standard: "safer at the same quality" by default; "smarter" only if the pass-rate margin clears a 1-task gap across all evaluated runs.
