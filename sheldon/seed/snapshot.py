"""Seed incidents, including one refuted fix, and the frozen copy.

Status: wired and tested. ``load_seed`` writes ``queries/seed_demo.cypher``
into an empty graph. ``copy_graph`` is the ``GRAPH.COPY`` reset the demo and
the eval start from.
"""

from sheldon.cypher import load_query
from sheldon.db import connect, read


def load_seed(graph: str) -> str:
    """Write the demo seed into ``graph`` and return the key. The graph must be empty.

    Freeze it once with ``copy_graph(graph, frozen_key)``. Every demo take and
    eval run then copies from that frozen key, never from a graph that ran.
    """
    rows = read(graph, "count_nodes")
    if rows and rows[0]["nodes"]:
        raise ValueError(f"{graph} is not empty. Seed a fresh key or copy_graph the frozen one")
    connect().select_graph(graph).query(load_query("seed_demo"))
    return graph


def copy_graph(source: str, dest: str) -> None:
    """Replace ``dest`` with a copy of ``source``. ``GRAPH.COPY`` errors if dest exists."""
    db = connect()
    try:
        db.select_graph(dest).delete()
    except Exception:  # noqa: BLE001 - dest may not exist yet
        pass
    db.execute_command("GRAPH.COPY", source, dest)
