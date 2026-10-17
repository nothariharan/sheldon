"""R1, recall at PR time.

Status: wired. ``recall`` runs ``queries/recall_pr.cypher`` through
``GRAPH.RO_QUERY``. It needs pr-ingest and the seed to have written the graph.
"""

from sheldon.db import read

RECALL_ROW_LIMIT = 50


def recall(graph: str, pr_number: int) -> list[dict]:
    """Return file, via, incident, title, claim, kind, status, relation, and evidence rows.

    ``via`` is the file the incident touched: the changed file itself, or a
    file that co-changed with it. ``relation`` is ``SUPPORTED_BY``,
    ``REFUTED_BY``, or ``None`` when the claim cites no evidence yet.
    An empty list means no incident touches the PR's files.
    """
    return read(graph, "recall_pr", {"pr": pr_number, "limit": RECALL_ROW_LIMIT})
