// Trap-suite overlay. Run after queries/seed_demo.cypher so the S0
// full-text indexes already exist and these claims are indexed.
// C-20 is refuted by E-20. C-21, C-22, and C-23 sit 1, 2, and 3
// RELIES_ON hops away from that refuted claim. E-99 is an executed
// passing test_run on a sha that is not PR 7's head.

CREATE
  (c20:Claim {id: 'C-20', kind: 'fix', status: 'refuted', confidence: 0.1,
              text: 'Retrying the invoice post fixes the duplicate charge',
              model: 'trap', session: 'trap'}),
  (e20:Evidence {id: 'E-20', kind: 'ci_run', executed: true, sha: 'a1', exit_code: 1,
                 model: 'ci', session: 'trap'}),
  (c20)-[:REFUTED_BY {agent: 'ci', at: 1792080000000, model: 'ci', session: 'trap'}]->(e20),
  (c21:Claim {id: 'C-21', kind: 'fix', status: 'open', confidence: 0.4,
              text: 'Split the invoice post into two steps',
              model: 'trap', session: 'trap'}),
  (c21)-[:RELIES_ON]->(c20),
  (c22:Claim {id: 'C-22', kind: 'fix', status: 'open', confidence: 0.4,
              text: 'The partner webhook can wait',
              model: 'trap', session: 'trap'}),
  (c22)-[:RELIES_ON]->(c21),
  (c23:Claim {id: 'C-23', kind: 'fix', status: 'open', confidence: 0.4,
              text: 'Ship the partner webhook when the queue drains',
              model: 'trap', session: 'trap'}),
  (c23)-[:RELIES_ON]->(c22),
  (:Evidence {id: 'E-99', kind: 'test_run', executed: true, sha: 'other', exit_code: 0,
              model: 'trap', session: 'trap'})
