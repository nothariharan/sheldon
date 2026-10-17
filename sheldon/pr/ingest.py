"""Webhook and diff ingest for one pull request.

Status: to build. It is not a working feature.
"""


def ingest_pull_request(
    graph: str,
    number: int,
    head_sha: str,
    changed_paths: list[str],
) -> int:
    """To build. Return how many CHANGES edges were written."""
    del graph, number, head_sha, changed_paths
    raise NotImplementedError("to build: pr-ingest")
