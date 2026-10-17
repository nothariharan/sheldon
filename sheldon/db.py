"""FalkorDB connection. One place so host and port are not hardcoded again."""

import os

from falkordb import FalkorDB

from sheldon.schema import FALKORDB_MODULE_VERSION


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
