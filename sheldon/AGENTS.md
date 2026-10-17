# sheldon package

Import across areas. Do not edit another area's module to make yours work. If you need a new status or edge name, it goes in `schema.py` and the PR says why.

| Module | Public function | Query file |
|---|---|---|
| `memory.ingest` | `record_event` | `queries/record_event.cypher` |
| `retrieval.read` | `retrieve`, `q_star` | `queries/q_star.cypher` |
| `answers.compose` | `compose` | none — it does not write Cypher |
| `coordination.board` | `claim_task`, `heartbeat`, `complete_task`, `handoff_task`, `resume` | matching file under `queries/` |
| `belief.refute` | `refute_hypothesis` | `queries/refute_hypothesis.cypher` |
| `eval.harness` | `reset_from_seed`, `count_repeated_failed_steps` | `queries/repeated_failed_steps.cypher` |

`db.py` and `cypher.py` are shared. `load_query` strips full-line `//` comments and rejects a second statement.

No Cypher string in this package. `tests/test_contracts.py` fails the build if one appears.

Stub flags: `CLAIM_IS_STUB` and `REFUTE_IS_STUB`. The race tests xfail while they are true. Set the flag false only in the same change that deletes the `NotImplementedError`.
