# sheldon package

Import across areas. Do not edit another area's module to make yours work. If you need a new status or edge name, it goes in `schema.py` and the PR says why.

Product scope is [`docs/plan/README.md`](../docs/plan/README.md). Every function below is to build unless the row says the query ran. None of them is a working feature.

| Module | Public function | Status | Owner |
|---|---|---|---|
| `memory.ingest` | `record_event` | to build | Amaan |
| `pr.ingest` | `ingest_pull_request` | wired and tested | Amaan |
| `seed.snapshot` | `load_seed`, `copy_graph` | wired and tested | Amaan |
| `retrieval.s0` | `s0` | keyword half wired on a fixture; vector half waits on `EMBEDDING_DIM` | Akshat |
| `retrieval.recall` | `recall` | wired on a fixture; waits on pr-ingest and the seed for real data | Akshat |
| `retrieval.read` | `retrieve`, `q_star` | to build | Akshat |
| `check.app`, `check.webhook` | `decide_check`, `check_run_payload`, `handle_event`, `make_app` | wired; not yet run against GitHub | Akshat |
| `gate.approve` | `approve` | built. test_approve.py | Hariharan |
| `gate.done` | `claim_done` | to build | Hariharan |
| `belief.refute` | `refute_hypothesis` | W2 query ran; function to build | Hariharan |
| `evidence.run` | `record_run` | built. test_run.py writes executed Evidence | Hariharan |
| `provenance` | `writes_with_provenance` | to build | Hariharan |
| `coordination.board` | `claim_task`, `heartbeat`, `complete_task`, `handoff_task` | built. test_claim.py and the claim race | Hariharan |
| `coordination.resume` | `resume` | to build | Satyansh |
| `preflight` | `preflight` | to build | Satyansh |
| `capsule` | `capsule` | to build | Satyansh |
| `mcp.server` | `call_tool` | to build | Satyansh |
| `answers.compose` | `compose` | to build | Satyansh |
| `eval.harness` | `reset_from_seed`, `count_repeated_failed_steps` | to build | Satyansh |

`db.py` and `cypher.py` are shared. `load_query` strips full-line `//` comments and rejects a second statement.

No Cypher string in this package. `tests/test_contracts.py` fails the build if one appears.

Stub flags: `CLAIM_IS_STUB` and `REFUTE_IS_STUB`. The race tests xfail while they are true. Set the flag false only in the same change that deletes the `NotImplementedError`.
