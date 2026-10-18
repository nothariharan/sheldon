// Demo seed. One CREATE. Ids are seed data, not a result.
// docs/plan/deep.md section 3 and docs/plan/demo.md walk through these ids.
//
// Step 1 (retry block): C-5, the cache-TTL fix for INC-12, was refuted by E-41.
//   ACT-1 is that attempt. Preflight matches a new action against it.
// Step 2 (gate): E-52 is a test_run that never executed.
// Step 3 (cascade): E-60 is new failing CI evidence. W2 refutes C-7 with it,
//   which stales approval A-3 and task T-9.
// Step 5 (R1): PR 7 changes checkout/cache.py, which co-changes with
//   checkout/session.py, which INC-12 touched.
// Claim status is open | confirmed | refuted (deep.md section 5).
// $head is PR 7's head sha (default 'b2'). Seed at the real commit you record
// from, so a `sheldon run` there lands on the same sha the check reads.
// Step 2 (gate): C-11 is Agent B's done claim. W3 approves it only with a
// passing executed test_run on $head.

CREATE (repo:Repository {name: 'demo/checkout'}),
       (dev:Developer {name: 'dev-a'}),
       (cache:File {path: 'checkout/cache.py', extension: 'py', language: 'python'}),
       (session:File {path: 'checkout/session.py', extension: 'py', language: 'python'}),
       (api:File {path: 'checkout/api.py', extension: 'py', language: 'python'}),
       (readme:File {path: 'docs/readme.md', extension: 'md', language: 'markdown'}),
       (cache)-[:BELONGS_TO]->(repo), (session)-[:BELONGS_TO]->(repo),
       (api)-[:BELONGS_TO]->(repo), (readme)-[:BELONGS_TO]->(repo),
       (c1:Commit {hash: 'a1', message: 'Add session lock around checkout', timestamp: 1792000000000}),
       (c2:Commit {hash: 'a0', message: 'Cache cart totals', timestamp: 1791900000000}),
       (dev)-[:AUTHORED]->(c1), (dev)-[:AUTHORED]->(c2),
       (c1)-[:MODIFIED {additions: 40, deletions: 6}]->(cache),
       (c1)-[:MODIFIED {additions: 22, deletions: 3}]->(session),
       (c2)-[:MODIFIED {additions: 15, deletions: 1}]->(cache),
       (cache)-[:CO_CHANGED_WITH {frequency: 4}]->(session),

       (inc:Incident {id: 'INC-12', title: 'Checkout times out under load', severity: 'sev2',
                      at: 1792050000000}),
       (inc)-[:TOUCHED]->(session),

       (c5:Claim {id: 'C-5', kind: 'fix', status: 'refuted', confidence: 0.1,
                  text: 'Raising the cache TTL to 600s fixes the checkout timeout',
                  model: 'agent-model-a', session: 'S-1'}),
       (c7:Claim {id: 'C-7', kind: 'root_cause', status: 'open', confidence: 0.7,
                  text: 'Session lock contention under load causes the checkout timeout',
                  model: 'agent-model-a', session: 'S-1'}),
       (inc)-[:HAS_CAUSE]->(c5), (inc)-[:HAS_CAUSE]->(c7),
       (:Claim {id: 'C-11', kind: 'done', status: 'open',
                text: 'Done, all tests pass on PR 7', model: 'agent-model-b', session: 'S-3'}),

       (e41:Evidence {id: 'E-41', kind: 'ci_run', executed: true, sha: 'a1', exit_code: 1,
                      model: 'ci', session: 'CI-41'}),
       (e30:Evidence {id: 'E-30', kind: 'trace', executed: true, sha: 'a1', exit_code: 0,
                      model: 'ci', session: 'CI-30'}),
       (e31:Evidence {id: 'E-31', kind: 'test_run', executed: true, sha: $head, exit_code: 0,
                      model: 'sheldon-run', session: 'S-2'}),
       (:Evidence {id: 'E-52', kind: 'test_run', executed: false, sha: $head,
                   model: 'agent-model-b', session: 'S-3'}),
       (:Evidence {id: 'E-60', kind: 'ci_run', executed: true, sha: $head, exit_code: 1,
                   model: 'ci', session: 'CI-60'}),
       (c5)-[:REFUTED_BY {agent: 'ci', at: 1792060000000, model: 'ci', session: 'CI-41'}]->(e41),
       (c7)-[:SUPPORTED_BY]->(e30),

       (:Action {id: 'ACT-1', cmd: 'edit checkout/cache.py', files: ['checkout/cache.py'],
                 fingerprint: 'edit checkout/cache.py', model: 'agent-model-a', session: 'S-1'})
         -[:ATTEMPTED_FIX_FOR]->(c5),

       (pr:PR {number: 7, head_sha: $head, status: 'open'})-[:CHANGES {sha: $head}]->(cache),
       (a3:Approval {id: 'A-3', by: 'reviewer-agent', actor_kind: 'agent', sha: $head,
                     status: 'active', at: 1792070000000, model: 'agent-model-c', session: 'S-4'}),
       (a3)-[:FOR]->(pr), (a3)-[:CITES]->(e31), (a3)-[:RELIES_ON]->(c7),
       (:Task {id: 'T-9', status: 'open', title: 'Shard the session lock'})-[:DEPENDS_ON]->(c7)
