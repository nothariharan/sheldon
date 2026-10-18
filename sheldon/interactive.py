"""`sheldon` with no args on a terminal: a prompt (docs/plan/cli-spec.md).

Each line is a command and its arguments, run the same way as from the shell.
`quit`, `exit`, or end of input leaves with exit 0. Not a TTY: the CLI keeps its
usage error and never reaches this module.
"""

import shlex
from collections.abc import Callable
from typing import TextIO

from sheldon.output import BANNER


def _preflight(argv: list[str]) -> int:
    from sheldon.preflight import main

    return main(argv)


def _run(argv: list[str]) -> int:
    from sheldon.cli import main

    return main(["run", "--", *argv])


def _check(argv: list[str]) -> int:
    from sheldon.check.__main__ import main

    return main(argv)


COMMANDS: dict[str, Callable[[list[str]], int]] = {
    "preflight": _preflight,
    "run": _run,
    "check": _check,
}

MENU = """\
  preflight   check a command before it runs
  run         run a command and record the exit
  check       print the PR check
  help
"""


def prompt(stdin: TextIO, stdout: TextIO, stderr: TextIO) -> int:
    """Read commands until `quit` or end of input. Return 0."""
    from sheldon.cli import build_parser

    stdout.write(BANNER + "\n" + MENU + "\n")
    while True:
        stdout.write("> ")
        stdout.flush()
        line = stdin.readline()
        if not line:
            stdout.write("\n")
            return 0
        try:
            words = shlex.split(line)
        except ValueError as exc:
            stderr.write(f"{exc}\n")
            continue
        if not words:
            continue
        name, args = words[0], words[1:]
        if name in ("quit", "exit"):
            return 0
        if name == "help":
            stdout.write(build_parser().format_help())
            continue
        command = COMMANDS.get(name)
        if command is None:
            stderr.write(f"unknown command: {name}\n")
            continue
        try:
            command(args)
        except SystemExit:
            # argparse already printed the usage line. Stay in the prompt.
            pass
