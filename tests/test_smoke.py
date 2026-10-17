"""The engine is up, and it is the image we pinned."""

from sheldon.db import assert_pinned_engine, connect


def test_module_version_matches_the_pin() -> None:
    db = connect()
    assert assert_pinned_engine(db) > 0


def test_graph_copy_round_trip() -> None:
    db = connect()
    src_name = "sheldon_smoke_src"
    dst_name = "sheldon_smoke_dst"
    src = db.select_graph(src_name)
    dst = db.select_graph(dst_name)
    for graph in (dst, src):
        try:
            graph.delete()
        except Exception:  # noqa: BLE001 - missing graph
            pass

    src = db.select_graph(src_name)
    src.query("CREATE (:Smoke {id: 'ok'})")
    db.execute_command("GRAPH.COPY", src_name, dst_name)
    copied = db.select_graph(dst_name).query("MATCH (n:Smoke) RETURN n.id").result_set
    assert copied[0][0] == "ok"

    db.select_graph(src_name).delete()
    db.select_graph(dst_name).delete()
