# web

The landing page and the read-only seed view (`website` and `web-ui` in [`TASKS.md`](../TASKS.md); spec in [`docs/plan/ui-spec.md`](../docs/plan/ui-spec.md)). Static files, no build step, no server, no public database.

- `index.html`, `styles.css`, `app.js`: the page.
- `fixtures/`: everything the page shows. Each terminal replays one recorded `{argv, exit_code, stdout, stderr}` from here. The page never types a line that is not in a fixture.

## Preview

```bash
python -m http.server 8765 -d web
```

Open `http://127.0.0.1:8765/`. Opening `index.html` from disk does not work, because the page fetches `fixtures/`.

## Deploy

Vercel: import the repo, set Root Directory to `web`, Framework Preset to Other, and leave the build command empty. GitHub Pages: publish the `web` folder. The page uses relative paths, so it works from a subpath.

## Fixtures

| File | Written by | What the page shows |
|---|---|---|
| `graph.json` and the three `.txt` / `.json` moment files | `python -m sheldon.export --seed --graph sheldon_export_seed --out web/fixtures` | The retry block (moment 1), the seed graph (before), and the check after the refute |
| `evidence-gate-run.json` | `python web/record_frames.py` | Moment 2: the check citing E-52, `sheldon run -- python -m pytest tests/test_output.py -q`, and the check citing the evidence id that run stored, all on a seed whose PR 7 head is `git rev-parse HEAD` |
| `refute.json` | `python web/record_frames.py` | Moment 3: the `refute_claim(C-7, [E-60])` call, its return value, and the check after it |
| `graph-after.json` | `python web/record_frames.py` | The graph after that refute: C-7 refuted, A-3 stale, T-9 `stale: true` |

Both commands need FalkorDB up (`./scripts/setup.sh`) and run inside the venv. `--seed` deletes the graph key it is given. `record_frames.py` uses its own scratch keys (`sheldon_site_*`) and deletes them after. Run the export first, then `record_frames.py`, so the before and after snapshots come from the same seed.

`evidence-gate-run.json` records the sha of the commit you run it from, so re-run it after the seed changes.

## Rules the page follows

The theme follows the OS until someone uses the toggle, which is then saved in this browser. Wording matches the README. No speed number, no cost number, no eval number, no quotes, no other team's name. `prefers-reduced-motion: reduce` shows every transcript in full, without typing. There is no autoplay video.
