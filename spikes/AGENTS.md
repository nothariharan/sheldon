# spikes

P0 scripts from 15 Oct 2026. They answered engine questions by running them. They are not pytest tests, and CI does not run them.

```bash
FALKORDB_HOST=localhost FALKORDB_PORT=6379 .venv/bin/python spikes/p0_engine_semantics.py
```

Host and port come from the environment. Default is the compose port.

## Gotchas

- The original run used the `latest` tag and the engine reported module `42201` (4.22.1). The repo is now pinned to `falkordb/falkordb:v4.22.1`. Re-run on that tag before treating a spike line as current. `p0-spikes` in `TASKS.md` is that job.
- They delete their own graphs (`spike_p0`, `spike_p0b`, …). Don't point them at an investigation graph.
- Useful results, already baked into the rules: multi-type `*1..3` works; the in-query prev link does not fork at 8 writers; a single conditional claim has one winner at 12 writers; vector filters apply after the top-k cut; `algo.WCC()` with args returns `[]` and does not error; `algo.AStar` is geographic.
- `p0e_vector_filter_semantics.py` is the post-cut demonstration. Don't "fix" the empty blue result. That empty result is the finding.
