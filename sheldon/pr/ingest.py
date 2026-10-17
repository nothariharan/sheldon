"""Webhook and diff ingest for one pull request.

Status: wired and tested. ``ingest_pull_request`` runs
``queries/ingest_pull_request.cypher``. The check-run webhook calls it.
"""

from sheldon.cypher import load_query
from sheldon.db import connect


def ingest_pull_request(
    graph: str,
    number: int,
    head_sha: str,
    changed_paths: list[str],
) -> int:
    """Write ``PR -[:CHANGES]-> File`` for ``head_sha``. Return how many CHANGES edges were written.

    One statement. A new push replaces the PR's changed-file set. File nodes
    are reused by path and never deleted.
    """
    paths = list(dict.fromkeys(changed_paths))
    result = connect().select_graph(graph).query(
        load_query("ingest_pull_request"),
        {"number": number, "head_sha": head_sha, "paths": paths},
    )
    return result.result_set[0][0]
