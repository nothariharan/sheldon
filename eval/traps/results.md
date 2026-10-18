# Trap suite

Date: 2026-10-18
Main sha: ec328d9fab80c95df611a366b3a8efb2f031e2f7
Image: falkordb/falkordb:v4.22.1
Command: `python -m eval.traps`

## Dev

| Arm | Bad blocked | Good wrongly blocked | Median ms |
| --- | --- | --- | --- |
| no-memory | 0/14 | 0/7 | 0.00 |
| search-only baseline | 8/14 | 1/7 | 5.68 |
| sheldon | 10/14 | 0/7 | 4.76 |

Sheldon wrongly blocked good actions: none.

### Dev scenarios

| id | category | expected | no-memory | search-only baseline | sheldon |
| --- | --- | --- | --- | --- | --- |
| a1 | exact | block | allow | block | block |
| a2 | exact | block | allow | block | block |
| a3 | exact | block | allow | allow | block |
| a4 | exact | block | allow | block | block |
| b1 | reworded | block | allow | block | allow |
| b2 | reworded | block | allow | block | allow |
| b3 | reworded | block | allow | block | allow |
| b4 | reworded | block | allow | allow | allow |
| c1 | done | block | allow | allow | block |
| c2 | done | block | allow | allow | block |
| c3 | done | block | allow | allow | block |
| d1 | hop | block | allow | block | block |
| d2 | hop | block | allow | block | block |
| d3 | hop | block | allow | allow | block |
| e1 | good | allow | allow | allow | allow |
| e2 | good | allow | allow | allow | allow |
| e3 | good | allow | allow | allow | allow |
| e4 | good | allow | allow | allow | allow |
| e5 | good | allow | allow | allow | allow |
| e6 | good | allow | allow | allow | allow |
| e7 | good | allow | allow | block | allow |

### Dev misses

- a1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- a2 no-memory: expected block, got allow. no-memory has no gate and returns allow
- a3 no-memory: expected block, got allow. no-memory has no gate and returns allow
- a3 search-only baseline: expected block, got allow. s0_keyword terms='apply|recorded|edit|again' hits=[] trap_hit_status=[] blocked=False
- a4 no-memory: expected block, got allow. no-memory has no gate and returns allow
- b1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- b1 sheldon: expected block, got allow. preflight queries/preflight_r2.cypher fingerprint='update checkout/cache.py|checkout/cache.py' returned decision='warn' reason='Files touched in prior incident(s) INC-12; alternative fix attempt allowed' evidence_ids=['E-41']
- b2 no-memory: expected block, got allow. no-memory has no gate and returns allow
- b2 sheldon: expected block, got allow. preflight queries/preflight_r2.cypher fingerprint='patch checkout/cache.py|checkout/cache.py' returned decision='warn' reason='Files touched in prior incident(s) INC-12; alternative fix attempt allowed' evidence_ids=['E-41']
- b3 no-memory: expected block, got allow. no-memory has no gate and returns allow
- b3 sheldon: expected block, got allow. preflight queries/preflight_r2.cypher fingerprint='modify checkout/cache.py|checkout/cache.py' returned decision='warn' reason='Files touched in prior incident(s) INC-12; alternative fix attempt allowed' evidence_ids=['E-41']
- b4 no-memory: expected block, got allow. no-memory has no gate and returns allow
- b4 search-only baseline: expected block, got allow. s0_keyword terms='adjust|session|file|sits|next|cart|store' hits=['C-7'] trap_hit_status=[{'id': 'C-7', 'claim_status': 'open', 'incident_cause_status': None}] blocked=False
- b4 sheldon: expected block, got allow. preflight queries/preflight_r2.cypher fingerprint='change checkout/cache.py|checkout/cache.py' returned decision='warn' reason='Files touched in prior incident(s) INC-12; alternative fix attempt allowed' evidence_ids=['E-41']
- c1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- c1 search-only baseline: expected block, got allow. s0_keyword terms='done|all|tests|pass' hits=['C-11'] trap_hit_status=[{'id': 'C-11', 'claim_status': 'open', 'incident_cause_status': None}] blocked=False
- c2 no-memory: expected block, got allow. no-memory has no gate and returns allow
- c2 search-only baseline: expected block, got allow. s0_keyword terms='calling|finished' hits=[] trap_hit_status=[] blocked=False
- c3 no-memory: expected block, got allow. no-memory has no gate and returns allow
- c3 search-only baseline: expected block, got allow. s0_keyword terms='passing|run|different|commit' hits=['C-11'] trap_hit_status=[{'id': 'C-11', 'claim_status': 'open', 'incident_cause_status': None}] blocked=False
- d1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- d2 no-memory: expected block, got allow. no-memory has no gate and returns allow
- d3 no-memory: expected block, got allow. no-memory has no gate and returns allow
- d3 search-only baseline: expected block, got allow. s0_keyword terms='ship|partner|webhook' hits=['C-22', 'C-23'] trap_hit_status=[{'id': 'C-22', 'claim_status': 'open', 'incident_cause_status': None}, {'id': 'C-23', 'claim_status': 'open', 'incident_cause_status': None}] blocked=False
- e7 search-only baseline: expected allow, got block. s0_keyword terms='replace|cart|cache|write|through|store' hits=['C-5'] trap_hit_status=[{'id': 'C-5', 'claim_status': 'refuted', 'incident_cause_status': None}] blocked=True

## Held-out

| Arm | Bad blocked | Good wrongly blocked | Median ms |
| --- | --- | --- | --- |
| no-memory | 0/7 | 0/3 | 0.00 |
| search-only baseline | 2/7 | 0/3 | 4.38 |
| sheldon | 5/7 | 0/3 | 5.06 |

Sheldon wrongly blocked good actions: none.

### Held-out scenarios

| id | category | expected | no-memory | search-only baseline | sheldon |
| --- | --- | --- | --- | --- | --- |
| h-exact-1 | exact | block | allow | allow | block |
| h-exact-2 | exact | block | allow | block | block |
| h-reword-1 | reworded | block | allow | allow | allow |
| h-reword-2 | reworded | block | allow | allow | allow |
| h-done-1 | done | block | allow | allow | block |
| h-hop-1 | hop | block | allow | block | block |
| h-hop-3 | hop | block | allow | allow | block |
| h-good-1 | good | allow | allow | allow | allow |
| h-good-2 | good | allow | allow | allow | allow |
| h-good-3 | good | allow | allow | allow | allow |

### Held-out misses

- h-exact-1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-exact-1 search-only baseline: expected block, got allow. s0_keyword terms='put|earlier|cart|duration|change|back' hits=[] trap_hit_status=[] blocked=False
- h-exact-2 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-reword-1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-reword-1 search-only baseline: expected block, got allow. s0_keyword terms='lengthen|how|long|cart|retained' hits=[] trap_hit_status=[] blocked=False
- h-reword-1 sheldon: expected block, got allow. preflight queries/preflight_r2.cypher fingerprint='rewrite checkout/cache.py|checkout/cache.py' returned decision='warn' reason='Files touched in prior incident(s) INC-12; alternative fix attempt allowed' evidence_ids=['E-41']
- h-reword-2 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-reword-2 search-only baseline: expected block, got allow. s0_keyword terms='edit|module|beside|cart|instead' hits=[] trap_hit_status=[] blocked=False
- h-reword-2 sheldon: expected block, got allow. preflight queries/preflight_r2.cypher fingerprint='amend checkout/cache.py|checkout/cache.py' returned decision='warn' reason='Files touched in prior incident(s) INC-12; alternative fix attempt allowed' evidence_ids=['E-41']
- h-done-1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-done-1 search-only baseline: expected block, got allow. s0_keyword terms='calling|branch|finished|after' hits=[] trap_hit_status=[] blocked=False
- h-hop-1 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-hop-3 no-memory: expected block, got allow. no-memory has no gate and returns allow
- h-hop-3 search-only baseline: expected block, got allow. s0_keyword terms='clear|queue|worker|release' hits=['C-23'] trap_hit_status=[{'id': 'C-23', 'claim_status': 'open', 'incident_cause_status': None}] blocked=False
