# CLI experience

Owners: Akshat and Satyansh. Row: `cli-ux`. The interaction to aim at is a Claude Code style terminal: a banner when a person is watching, a status line you can scan, and plain text when a pipe or another program is the reader.

## Who builds what

Akshat: the banner, the interactive mode, help, and the non-TTY / `NO_COLOR` fallback. He still records the demo and submits the form by 11:00 PM IST.

Satyansh: spinners, the colored status lines, and the per-command output for preflight, `sheldon run`, check, and the MCP server. Those four call one shared module, `sheldon/output.py`, so color, spinners, and the plain-text switch live in one place. Akshat's banner, help, and fallback call that same module.

Satyansh's order: the compose fix comes before this CLI work. On the seed, E-30 supported C-7 and E-60 is the refuting run. The session-start hook is built (`python -m sheldon.hooks.session_start`). If time runs short, fail-closed is the cut. This CLI work stays.

This file does not add a dependency. The implementation pull request pins `rich` in `requirements.txt` and `requirements-dev.txt`. `textual` is a later choice for a full-screen app, not part of the 9 PM cut. Do not add either library in the docs pull request.

## Output interface

`sheldon/output.py` is the one writer. Command code returns a `CommandResult` and does not print. Akshat and Satyansh add a banner, a spinner, or color by wrapping `emit`, not by editing preflight, run, check, resume, or recall.

`CommandResult` fields:

- `command`: `preflight`, `run`, `check`, `resume`, or `recall`
- `exit_code`: the process exit code
- `data`: the structured payload
- `text`: the plain-text line
- `stream`: `stdout` or `stderr`. Preflight block and warn use `stderr`
- `json_style`: `envelope` or `payload`

`emit(result, as_json=False)` writes `text` to `stream`. That is the default. `emit(result, as_json=True)` writes JSON to stdout and nothing to stderr.

The envelope is `command`, `exit_code`, `text`, and `data`. Preflight, `sheldon run`, resume, and recall use it. Check uses `json_style="payload"`: `--json` still prints the check-run payload, because that document is what a program already parses. The `CommandResult` for check still carries that payload in `data`.

Flags, all before any `--` separator:

- `python -m sheldon.preflight --json`
- `sheldon run --json -- <cmd>`
- `python -m sheldon.check --json`
- `python -m sheldon.coordination.resume --json`
- `python -m sheldon.retrieval.recall --json`

Plain text when `--json` is absent:

- preflight: the reason on stderr, exit 2 on block, exit 0 on warn or ok
- `sheldon run`: `recorded evidence <id> exit <code>`, then the child exit code
- check: the title line and the summary, unchanged
- resume: `tried`, `failed`, `believed`, and `next` counts
- recall: one line of incident, claim, relation, and evidence per row

Today `sheldon` is `sheldon.cli:console_main` and requires a subcommand. `python -m sheldon.preflight`, `python -m sheldon.check`, and `python -m sheldon.mcp.server` are separate entry points. The frames below are the target look. Where today's process prints less, the frame says so.

## Rules for every command

- A TTY and `NO_COLOR` unset: banner, color, and (if the nice-to-have lands) a spinner.
- Not a TTY, or `NO_COLOR` set to anything other than empty: plain text. No banner, no spinner, no ANSI color. Exit codes stay the same.
- Status words and colors: `blocked` red, `passed` or `clear` green, `stale` amber. A warn from preflight is amber and is not the same word as `stale`.
- Color is decoration. The status word is still in the text, so a log without color still reads.
- MCP stdout is the protocol. No banner, no spinner, no status paint, even on a TTY. Diagnostics go to stderr as plain text.

## Banner

On a TTY, human commands print a short banner before the status. Original mark, not taken from another product:

```text
 sheldon
 one graph per repo
```

`sheldon --help` includes the banner on a TTY and omits it when stdout is not a TTY.

## Help

Must ship. `sheldon --help` lists `run` and points at the module commands that are not subcommands yet:

```text
usage: sheldon run -- <cmd>

  run     run a command and record one executed Evidence node

Also:
  python -m sheldon.preflight    block a repeated refuted edit (exit 2)
  python -m sheldon.check        print the PR check
  python -m sheldon.mcp.server   MCP on stdin/stdout
```

`sheldon` with no args today exits with an argparse error, because the subparser is required. That stays acceptable for the 9 PM cut. The friendly prompt is nice to have.

## Preflight

`python -m sheldon.preflight --command "edit checkout/cache.py" --paths checkout/cache.py`

Today the block path writes the reason to stderr and returns 2. The reason starts `blocked: refuted by E-41` and names INC-12. A warn writes the reason and returns 0. An ok returns 0 and prints nothing. A database error is a warn and exit 0 (fail open), until that behavior changes.

Target frame on a TTY, block:

```text
 sheldon
 one graph per repo

 blocked  INC-12
 blocked: refuted by E-41; this edit repeats the fix tried for INC-12; E-41 refuted it: <seed reason>
```

The last clause is the reason on the seed, not a rewritten sentence. Exit code stays 2.

Target frame, not a TTY: the reason line, no banner, no color, exit 2.

## sheldon run

`sheldon run -- pytest`

Today the process captures the child stdout and stderr, records one Evidence node (`executed: true`, the child exit code, the sha, the output digest), and returns the child exit code. It prints no status line.

Target frame on a TTY, child exit 0:

```text
 sheldon
 one graph per repo

 running  pytest
 passed   evidence E-<digest prefix>  exit 0
```

Target frame, child exit non-zero. The node is still recorded. The line is not `passed`:

```text
 recorded evidence E-<digest prefix>  exit 3
```

Not a TTY: one plain line, `recorded evidence E-<id> exit <code>`, then the child exit code. Do not dump the captured child output a second time unless `--verbose` is added later.

A spinner while the child runs is nice to have. It stops before the status line. It does not run when stdout is not a TTY or `NO_COLOR` is set.

## Check

`python -m sheldon.check --repo demo/checkout 7 <head-sha>`

Today this prints the title, the conclusion, and the summary. Exit 1 on failure, else 0. `--json` prints the payload and must stay free of color and banner, because a program will parse it.

Target frame for the evidence gate (seed path, citing E-52):

```text
 sheldon: blocked (failure) PR 7 at <sha>
 blocked: E-52 not executed
 refuted: C-5 by E-41 (INC-12, via checkout/session.py)
```

Target frame after the refute of C-7 by E-60:

```text
 sheldon: blocked (failure) PR 7 at <sha>
 stale: A-3 marked stale
 refuted: C-5 by E-41 (INC-12, via checkout/session.py)
 refuted: C-7 by E-60 (INC-12, via checkout/session.py)
```

Color the words `blocked` and `stale`. A success title is `sheldon: clear (success)` in green. `--json` is unchanged.

## MCP server

`python -m sheldon.mcp.server`

Stdout is MCP JSON-RPC, one message at a time, as it is today. Tools include `preflight`, `sheldon_run`, and `claim_done`. The server does not print the banner. A spinner would break the client. Stderr may say the server is up, as plain text, with no color when stderr is not a TTY.

## Interactive mode

Nice to have. `sheldon` with no args, on a TTY, opens a prompt instead of an error:

```text
 sheldon
 one graph per repo

  preflight   check a command before it runs
  run         run a command and record the exit
  check       print the PR check
  help

>
```

Not a TTY: keep today's usage error and exit non-zero. Do not wait for input. A `textual` full-screen app is out of the 9 PM cut.

## Must ship by 9 PM IST

- Banner on a TTY for `sheldon run`, preflight, and check (Akshat). Omitted when not a TTY, when `NO_COLOR` is set, and always on MCP stdout.
- The non-TTY / `NO_COLOR` fallback (Akshat).
- `sheldon --help` as above (Akshat).
- Colored `blocked`, `passed` / `clear`, and `stale` lines, with the word still in the text (Satyansh, via `sheldon/output.py`).
- `sheldon run` prints the evidence id and the child exit code (Satyansh).
- `--json` on check stays machine-readable (Satyansh).

## Nice to have

- `sheldon` with no args opens the prompt (Akshat).
- Spinners, via `rich`, while a command or a graph read is in flight (Satyansh).
- A `textual` full-screen app.
