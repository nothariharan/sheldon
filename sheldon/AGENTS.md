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
| `gate.done` | `claim_done` | built. test_done.py | Hariharan |
| `belief.refute` | `refute_claim`, `refute_hypothesis` | `refute_claim` is built (test_refute.py). `refute_hypothesis` is a sketch: it matches `:Event` and does not check `executed` | Hariharan |
| `evidence.run` | `record_run` | built. test_run.py writes executed Evidence | Hariharan |
| `provenance` | `writes_with_provenance` | built. test_provenance.py | Hariharan |
| `coordination.board` | `claim_task`, `heartbeat`, `complete_task`, `handoff_task` | claim, heartbeat, and complete are built (test_claim.py and the claim race). `handoff_task` is partly built: it releases a claimed lease and drops `to_agent` and `note` | Hariharan |
| `coordination.resume` | `resume` | to build | Satyansh |
| `preflight` | `preflight` | built. test_preflight.py | Satyansh |
| `capsule` | `capsule` | to build | Satyansh |
| `mcp.server` | `call_tool` | built. tests/mcp/test_server.py; resume returns a placeholder | Satyansh |
| `answers.compose` | `compose` | to build | Satyansh |
| `eval.harness` | `reset_from_seed`, `count_repeated_failed_steps` | to build | Satyansh |

`db.py` and `cypher.py` are shared. `load_query` strips full-line `//` comments and rejects a second statement.

No Cypher string in this package. `tests/test_contracts.py` fails the build if one appears.

Stub flags: `CLAIM_IS_STUB` and `REFUTE_IS_STUB`. The race tests xfail while they are true. Set the flag false only in the same change that deletes the `NotImplementedError`.
