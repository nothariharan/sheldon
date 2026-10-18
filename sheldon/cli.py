"""Command line. `sheldon run -- <cmd>` records one executed Evidence node."""

import argparse
import hashlib
import os
import shlex
import subprocess
import sys

from sheldon.evidence.run import record_run
from sheldon.output import BANNER, CommandResult, emit, plain

HELP = """\
  run     run a command and record one executed Evidence node

Also:
  python -m sheldon.preflight    block a repeated refuted edit (exit 2)
  python -m sheldon.check        print the PR check
  python -m sheldon.mcp.server   MCP on stdin/stdout"""


class _Parser(argparse.ArgumentParser):
    """Prints the banner above help on a terminal, never in a pipe."""

    def print_help(self, file=None) -> None:
        file = file if file is not None else sys.stdout
        if not plain(file):
            file.write(BANNER + "\n")
        super().print_help(file)


def head_sha() -> str:
    """Return the git HEAD this process is running in, or an empty string."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def digest_output(stdout: bytes, stderr: bytes) -> str:
    """sha256 of the process stdout followed by its stderr."""
    return hashlib.sha256(stdout + stderr).hexdigest()


def run_result(
    graph: str,
    cmd: list[str],
    *,
    evidence_id: str = "",
    model: str = "",
    session: str = "",
) -> CommandResult:
    """Run ``cmd``, record one executed Evidence node, and return the result."""
    completed = subprocess.run(cmd, capture_output=True)
    digest = digest_output(completed.stdout, completed.stderr)
    evidence_id = evidence_id or f"E-{digest[:12]}"
    record_run(
        graph,
        evidence_id=evidence_id,
        command=shlex.join(cmd),
        head_sha=head_sha(),
        exit_code=completed.returncode,
        model=model,
        session=session,
        output_digest=digest,
    )
    return CommandResult(
        command="run",
        exit_code=completed.returncode,
        data={
            "id": evidence_id,
            "executed": True,
            "exit_code": completed.returncode,
            "command": shlex.join(cmd),
            "output_digest": digest,
        },
        text=f"recorded evidence {evidence_id} exit {completed.returncode}",
    )


def build_parser() -> argparse.ArgumentParser:
    """The `sheldon` parser. `--help` prints the banner on a terminal."""
    parser = _Parser(
        prog="sheldon",
        usage="sheldon run -- <cmd>",
        description=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="name", metavar="run", required=True, help=argparse.SUPPRESS)
    run = sub.add_parser("run", help="run a command and record the exit")
    run.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon"))
    run.add_argument("--id", default="")
    run.add_argument("--model", default=os.environ.get("SHELDON_MODEL", ""))
    run.add_argument("--session", default=os.environ.get("SHELDON_SESSION", ""))
    run.add_argument("--json", action="store_true", help="print the result as JSON")
    run.add_argument("cmd", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    """Run `sheldon run` and return the child process exit code."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv and not plain(sys.stdin) and not plain(sys.stdout):
        from sheldon.interactive import prompt

        return prompt(sys.stdin, sys.stdout, sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if args.name != "run" or not cmd:
        parser.error("usage: sheldon run -- <cmd>")

    result = run_result(
        args.graph,
        cmd,
        evidence_id=args.id,
        model=args.model,
        session=args.session,
    )
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


def console_main() -> None:
    """Setuptools entry point. The package name stays `sheldon`."""
    sys.exit(main())
