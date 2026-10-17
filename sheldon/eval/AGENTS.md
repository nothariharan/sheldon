# eval

Status: reset and repeated-step count built; paired runs to build. Report no number from it. Satyansh owns this folder.

Owns the repeated-failed-steps count and the frozen-seed reset.

## Contract

Write the definition of "repeated failed step" in `docs/` before `count_repeated_failed_steps` returns a real number. Then replace `queries/repeated_failed_steps.cypher`.

`reset_from_seed` is `GRAPH.COPY` from `schema.EVAL_SEED_GRAPH` onto a fresh destination. The command errors if the destination exists, so delete the run graph first. Every S0 run and every S3 run starts from that same frozen copy. At least 3 runs each. Report raw counts.

## Gotchas

- The copy is a methods line. It is not a sandbox and not a novelty claim.
- TIDE's published loop-ratio drop is from model scaling, not memory. Don't report it as our result.
- Don't quote a copy-time or a query-time number unless this harness measured it.
- Wiring `sameAction` is roadmap. Do not change the image pin. The pinned image stays `falkordb/falkordb:v4.22.1`. UDFs are read-only, so they don't belong in the refute write.
