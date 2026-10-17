# tests

`pytest` is the suite CI runs, with FalkorDB from `docker-compose.yml` or the Actions service container.

| File | Needs the engine | What it locks |
|---|---|---|
| `test_smoke.py` | yes | Module `42201`, and `GRAPH.COPY` round trip |
| `test_races.py` | yes, once the stub flags flip | 20 claimers, one winner. 20 bad refutes, all rejected |
| `test_contracts.py` | no | One statement per query, no inline Cypher, shared image pin, no forbidden claims, no rival-team names |

## Gotchas

- Do not delete the xfail by skipping the race. Flip `CLAIM_IS_STUB` or `REFUTE_IS_STUB` to `False` and remove the `NotImplementedError`. `test_stub_flags_match_the_function_body` fails if the flag and the body disagree.
- Smoke uses graph keys `sheldon_smoke_src` and `sheldon_smoke_dst` and deletes them. Race tests use `race_claim` and `race_refute`.
- A contract test scans the tree for other teams' names. Don't weaken that list to get a PR green.
