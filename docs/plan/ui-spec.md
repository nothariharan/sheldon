# Website and web interface

Owner: Amaan. Rows: `website`, `web-ui`. Patterns: [ui-reference.md](ui-reference.md). Wording matches the README. No hype, no speed or cost number, no eval number, no other team's name. Cost stays "to measure".

Stack for the page that must ship: static files on Vercel (or GitHub Pages if Vercel is not ready). Next.js is allowed for the read-only interface later. The 9 PM page does not need a server and does not need a public FalkorDB.

The landing page does not invent output. Each terminal replay is a recording of a real command against the seed. If a live line differs from a sketch in this file, the recording wins.

## Landing page

Order:

1. Nav. Product name, a link to this spec or the repo README, the install command, and the public repo. No compare link.
2. Hero. The README lock sentence, in one block. Under it, the install command (`./scripts/setup.sh`) and the repo link. No second slogan.
3. Three demo moments, each a framed terminal that types a recorded transcript. See below.
4. A static graph of the seed. Nodes and edges from the seed, drawn or listed: INC-12, C-5, C-7, E-41, E-30, E-60, A-3, T-9, and the edges the seed actually writes (`REFUTED_BY`, `SUPPORTED_BY`, `RELIES_ON`, `DEPENDS_ON`). Not a live database.
5. How it works. Three short steps: preflight blocks a repeated refuted edit, a done claim needs a passing executed test run, a refute stales the approvals and tasks that relied on the claim. One atomic write. Nothing deletes a node.
6. Install and repo again. `./scripts/setup.sh` on Linux, `powershell -File scripts/setup.ps1` on Windows. The image pin stays `falkordb/falkordb:v4.22.1`.

`prefers-reduced-motion: reduce` shows the full transcript at once. Do not autoplay a video with sound.

### Moment 1: retry block

Command shape: `python -m sheldon.preflight` on `edit checkout/cache.py` and path `checkout/cache.py`, graph loaded from the seed. The process writes the reason to stderr and exits 2. The locked prefix is `blocked: refuted by E-41`, and the line names INC-12. Color that status blocked. Do not typeset a prettier reason than the recording.

### Moment 2: evidence gate

Two recorded frames.

A PR check that cites evidence which is not an executed run on the head prints a failure. On the seed path the summary lines are:

```text
sheldon: blocked (failure) PR 7 at <sha>
blocked: E-52 not executed
refuted: C-5 by E-41 (INC-12, via checkout/session.py)
```

A check that cites a real executed run on the head sha prints `sheldon: clear (success)`. The refuted-claim line can still be present. It informs. It does not by itself fail the check.

`sheldon run -- <cmd>` is the writer that records the executed run. Show a recorded run: the child exit code and the evidence id the command stored.

### Moment 3: refute plus stale cascade

Record `refute_claim` of C-7 citing E-60, then the check on the seed path. The summary lines the test on main expects are:

```text
stale: A-3 marked stale
refuted: C-5 by E-41 (INC-12, via checkout/session.py)
refuted: C-7 by E-60 (INC-12, via checkout/session.py)
```

Color `stale` differently from `blocked` and from a passing line. T-9 is the task the same write marks stale. Say that in the caption if the check summary does not print the task id.

## Read-only web interface

Row `web-ui`. A page over a frozen snapshot of the seed, checked into the site. It lists claims, evidence, and approvals, and it shows the stale cascade after the recorded refute (C-7 refuted by E-60, A-3 stale, T-9 stale). No write button, no login, no public database. If this needs a framework, Next.js on Vercel reading that snapshot is enough.

The snapshot and the transcripts are already in `web/fixtures/`. Regenerate them with:

```bash
python -m sheldon.export --seed --graph sheldon_export_seed --out web/fixtures
```

`--seed` deletes that graph key and loads the demo seed. Do not point it at a graph you need to keep.

`python -m sheldon.export --graph <key> --serve 8765` serves the same document on `http://127.0.0.1:8765/export.json`. GET is the method. There is no write route.

### Export schema `sheldon.export.v1`

`web/fixtures/graph.json`:

- `schema`: `sheldon.export.v1`
- `graph`: the key that was exported
- `nodes`: `{key, labels, properties}`. `key` is `id`, else `path`, else `PR-<number>`, else `name`
- `edges`: `{type, from, to, properties}` using those keys
- `moments.retry_block`, `moments.evidence_gate`, `moments.stale_cascade`: each is `{argv, exit_code, stdout, stderr}` from a real CLI run

Plain transcripts next to the JSON:

- `retry-block.txt` is preflight stderr for `edit checkout/cache.py`. Exit 2. It cites E-41 and INC-12.
- `evidence-gate.txt` is `python -m sheldon.check` citing E-52. It contains `blocked: E-52 not executed`.
- `stale-cascade.txt` is the check after C-7 is refuted by E-60. It contains `stale: A-3 marked stale` and `refuted: C-7 by E-60`.

The `.json` file beside each transcript is that moment's `{argv, exit_code, stdout, stderr}`.

## Must ship by 9 PM IST

- Hero, the three recorded terminal replays, the static seed graph, how it works, install, and the repo link.
- The page is on Vercel or GitHub Pages, and the link is ready for the form.
- Reduced-motion shows the transcripts without typing.

## Nice to have

- The read-only web interface (`web-ui`).
- An interactive graph (pan, select a node, read its properties) on the same snapshot.
- The demo video embedded, once the recording exists. No eval table on the page.
