# memory (p1)

Status: to build. Not a working feature. Product scope is [`docs/plan/README.md`](../../docs/plan/README.md). Amaan owns this folder.

Owns the append-only event chain and the schema apply.

## Contract

`record_event` writes one `Event`, links `IN_INVESTIGATION`, and links `NEXT` from the previous event. The previous event is chosen inside `queries/record_event.cypher` (`ORDER BY ingest_seq DESC LIMIT 1`). Do not take a previous id from the caller. Two concurrent appends must not fork the chain.

One FalkorDB key per investigation: `investigation_graph` in `schema.py`.

## Gotchas

- Do not add the embedding property until `EMBEDDING_DIM` is set. Re-embedding means a new index.
- `UNIQUE` needs an exact-match index first. The range indexes in `queries/create_index_*.cypher` may not satisfy it. Check on v4.22.1 before applying `schema.CONSTRAINTS`.
- Constraints cannot check that an evidence id exists. Don't try to express the refute gate here.
- `$now` and sequence numbers come from the service, not from an agent.
