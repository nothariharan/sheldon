"""FalkorDB connection. One place so host and port are not hardcoded again."""

import os

from falkordb import FalkorDB

from sheldon.cypher import load_query
from sheldon.schema import FALKORDB_MODULE_VERSION

# The image's default. A read the server kills raises. It is not an empty answer.
READ_TIMEOUT_MS = 1000


def connect() -> FalkorDB:
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", "6379"))
    return FalkorDB(host=host, port=port)


def graph_module_version(db: FalkorDB | None = None) -> int:
    client = db or connect()
    modules = client.connection.module_list()
    for module in modules:
        if module.get("name") == "graph":
            return int(module["ver"])
    raise RuntimeError(f"graph module not loaded: {modules!r}")


def assert_pinned_engine(db: FalkorDB | None = None) -> int:
    version = graph_module_version(db)
    if version != FALKORDB_MODULE_VERSION:
        raise RuntimeError(
            f"FalkorDB module is {version}, pinned constant is {FALKORDB_MODULE_VERSION}. "
            "Update sheldon/schema.py, docker-compose.yml, and CI together."
        )
    return version


def read(
    graph: str,
    query_name: str,
    params: dict | None = None,
    timeout_ms: int = READ_TIMEOUT_MS,
    db: FalkorDB | None = None,
) -> list[dict]:
    """Run one file from queries/ through GRAPH.RO_QUERY. Rows come back keyed by column.

    The server refuses a write sent this way, so a read helper cannot mutate the graph.
    """
    client = db or connect()
    result = client.select_graph(graph).ro_query(
        load_query(query_name), params or {}, timeout=timeout_ms
    )
    columns = [name for _, name in result.header]
    return [dict(zip(columns, row)) for row in result.result_set]
