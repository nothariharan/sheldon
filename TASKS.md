# Tasks

Claim a row by writing your name under Owner, then branch `area/short-name`. One owner per row. The stub you are replacing is named in the area `AGENTS.md`.

Scope is p0–p4 plus the eval. Do not add rows for playbooks, ablations, the MCP server, label vector filters, or a `GRAPH.COPY` sandbox.

## Order and deadlines

Times are IST.

- Amaan's memory rows go first; everyone else builds on them. p1 lands by tonight (Sat 17 Oct).
- Satyansh writes eval-def tonight, before any count is quoted. Define a repeated failed step MAST-style (step repetition, FM-1.3, arXiv 2503.13657): write the rule, hand-label a sample, then automate. Optional second number: TIDE's loop ratio (redundant loop actions / total actions, arXiv 2602.02196), used as a definition only, never as a memory result.
- Akshat runs the demo question against plain memory (S0) and shows it fails before building p2-qstar.
- p4-claim and p4-refute green by Sun 18 Oct morning; eval counts by Sun afternoon; Sun evening is the demo video and the clean public repo. Submission closes Sun 18 Oct 11:59 PM IST.

| ID | Area | Work | Done when | Owner |
|---|---|---|---|---|
| p0-spikes | spikes | Re-run `spikes/` against `falkordb/falkordb:v4.22.1` and paste the summary in the PR | Smoke is already green. Spike summary matches module `42201` | Amaan |
| p1-schema | memory | Apply indexes and the constraints in `sheldon/schema.py`. Confirm UNIQUE's exact-match index on this image | Constraints reject a hypothesis with no status | Amaan |
| p1-ingest | memory | `record_event` runs `queries/record_event.cypher`. Prev comes from the query | Two concurrent appends do not fork `NEXT` | Amaan |
| p1-seed | memory | One frozen incident graph, the eval seed | `GRAPH.COPY` of that graph is what eval resets from | Amaan |
| p1-s0 | retrieval | Vector + keyword baseline, no traversal | A number recorded for S0 on the dev questions | Akshat |
| p2-retrieve | retrieval | Intent, bounded traversal, evidence bundle | Dev questions return paths, not just text | Akshat |
| p2-qstar | retrieval | `queries/q_star.cypher` answers the demo question | S0 fails the same question live | Akshat |
| p3-compose | answers | Citations, abstention, path next to the answer | Unanswerable questions abstain. No invented ids | Satyansh |
| p4-claim | coord | `claim_task` runs `queries/claim_task.cypher`. Set `CLAIM_IS_STUB = False` | `test_parallel_claim_has_one_winner` passes with the xfail removed | Hariharan |
| p4-lease | coord | Heartbeat, complete, handoff. Each stays one statement | A non-owner cannot extend or complete | Hariharan |
| p4-resume | coord | `resume` returns tried / failed / believed / next, with ids | Refuted hypotheses are still in the result | Satyansh |
| p4-refute | belief | `refute_hypothesis` runs `queries/refute_hypothesis.cypher`. Set `REFUTE_IS_STUB = False` | Missing evidence is rejected. Dependent open tasks go stale. The hypothesis remains | Hariharan |
| eval-def | eval | Write the definition of "repeated failed step" | The definition is in `docs/` before any count is quoted | Satyansh |
| eval-count | eval | S0 vs S3, at least 3 runs, each reset from one frozen copy | Raw counts in the PR. No unmeasured speed number | Satyansh |
