# queries

Every Cypher statement the app runs lives in this folder, one file, one statement. `sheldon.cypher.load_query` reads the file, drops full-line `//` comments, and refuses a semicolon.

Name the file after the operation (`refute_hypothesis.cypher`, `claim_task.cypher`). Pass values as parameters. Do not concatenate ids into the text.

## Gotchas

- A second logical write belongs in the same statement, or it is not atomic. No `MULTI`/`EXEC`.
- `refute_hypothesis.cypher` is the evidence gate. It must `MATCH` every cited id, return 0 rows when one is missing, mark open tasks stale at `*1..3`, and not `DELETE`.
- `claim_task.cypher` is the lease. The race test expects one winner out of many callers.
- `create_vector_index_event.cypher` is comments on purpose until `EMBEDDING_DIM` is set. `load_query` will reject it.
- Don't add `*0..`. `LIMIT` does not constrain eager work, and an unbounded walk is how a demo query gets killed by the 1000ms timeout.
- Edge names that appear as literals here must match `sheldon/schema.py`. The contract test checks `INVESTIGATES` until that constant changes.
