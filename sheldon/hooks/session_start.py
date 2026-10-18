"""Session-start hook. Prints the capsule for the current task."""

import os
import sys

from sheldon.capsule import capsule


def session_start(graph: str, task_id: str, db=None) -> str:
    """Return the same text ``capsule`` returns for this task."""
    return capsule(graph, task_id, db=db)


def main(argv: list[str] | None = None, stdout=None) -> int:
    """Print the capsule. Claude Code SessionStart reads stdout."""
    import argparse

    parser = argparse.ArgumentParser(prog="python -m sheldon.hooks.session_start")
    parser.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon"))
    parser.add_argument("--task", default=os.environ.get("SHELDON_TASK", ""))
    args = parser.parse_args(argv)
    if not args.task:
        sys.stderr.write("sheldon: set --task or SHELDON_TASK\n")
        return 1
    try:
        text = session_start(args.graph, args.task)
    except KeyError as exc:
        sys.stderr.write(f"sheldon: {exc}\n")
        return 1
    stream = stdout if stdout is not None else sys.stdout
    stream.write(text if text.endswith("\n") else text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
