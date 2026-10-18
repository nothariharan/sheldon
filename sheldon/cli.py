"""Command line. `sheldon run -- <cmd>` records one executed Evidence node."""

import argparse
import hashlib
import os
import shlex
import subprocess
import sys

from sheldon.evidence.run import record_run


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


def main(argv: list[str] | None = None) -> int:
    """Run `sheldon run` and return the child process exit code."""
    parser = argparse.ArgumentParser(prog="sheldon")
    sub = parser.add_subparsers(dest="name", required=True)
    run = sub.add_parser("run", help="run a command and record the exit")
    run.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon"))
    run.add_argument("--id", default="")
    run.add_argument("--model", default=os.environ.get("SHELDON_MODEL", ""))
    run.add_argument("--session", default=os.environ.get("SHELDON_SESSION", ""))
    run.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if args.name != "run" or not cmd:
        parser.error("usage: sheldon run -- <cmd>")

    completed = subprocess.run(cmd, capture_output=True)
    digest = digest_output(completed.stdout, completed.stderr)
    evidence_id = args.id or f"E-{digest[:12]}"
    record_run(
        args.graph,
        evidence_id=evidence_id,
        command=shlex.join(cmd),
        head_sha=head_sha(),
        exit_code=completed.returncode,
        model=args.model,
        session=args.session,
        output_digest=digest,
    )
    return completed.returncode


def console_main() -> None:
    """Setuptools entry point. The package name stays `sheldon`."""
    sys.exit(main())
