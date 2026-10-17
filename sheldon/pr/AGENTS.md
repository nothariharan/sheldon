# pr

Amaan. Status: `ingest_pull_request` is wired and tested in `tests/pr/test_ingest.py`. The check-run webhook calls it on every `pull_request` event.

## Contract

`ingest_pull_request(graph, number, head_sha, changed_paths)` runs `queries/ingest_pull_request.cypher` as one statement. It writes `(:PR {number, head_sha})-[:CHANGES {sha}]->(:File {path})` and returns how many `CHANGES` edges it wrote.

- A new push replaces the PR's changed-file set. `CHANGES` edges to files the PR no longer touches are removed. That edge is derived from the diff. It is the only thing this folder deletes.
- `File` nodes are reused by `path`, so history ingest's `File` (with `language`, `extension`) is the same node. They are never deleted.
- Duplicate paths are dropped before the call.

## Gotchas

- Git history ingest stays in `sheldon/memory/`. Do not add it here.
- `PR` and `File` use `MERGE` because they are keyed by number and path. Claims and approvals use `CREATE`. Do not copy this pattern there.
