"""R1, recall at PR time.

Status: wired. ``recall`` runs ``queries/recall_pr.cypher`` through
``GRAPH.RO_QUERY``. It needs pr-ingest and the seed to have written the graph.
"""

from sheldon.db import read
from sheldon.output import CommandResult, emit

RECALL_ROW_LIMIT = 50


def recall(graph: str, pr_number: int) -> list[dict]:
    """Return file, via, incident, title, claim, kind, status, relation, and evidence rows.

    ``via`` is the file the incident touched: the changed file itself, or a
    file that co-changed with it. ``relation`` is ``SUPPORTED_BY``,
    ``REFUTED_BY``, or ``None`` when the claim cites no evidence yet.
    An empty list means no incident touches the PR's files.
    """
    return read(graph, "recall_pr", {"pr": pr_number, "limit": RECALL_ROW_LIMIT})


def recall_result(graph: str, pr_number: int) -> CommandResult:
    """Return the recall rows as a ``CommandResult``."""
    rows = recall(graph, pr_number)
    lines = [
        " ".join(
            str(row.get(key) or "")
            for key in ("incident", "claim", "relation", "evidence")
        ).strip()
        for row in rows
    ]
    return CommandResult(
        command="recall",
        exit_code=0,
        data={"pr": pr_number, "rows": rows},
        text="\n".join(line for line in lines if line),
    )


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    """Print a recall read. ``--json`` prints the result object."""
    import argparse
    import os

    parser = argparse.ArgumentParser(prog="python -m sheldon.retrieval.recall")
    parser.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon"))
    parser.add_argument("pr", type=int, help="pull request number")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    result = recall_result(args.graph, args.pr)
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    import sys

    sys.exit(main())
