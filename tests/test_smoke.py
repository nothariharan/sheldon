"""The engine is up, and it is the image we pinned."""

from sheldon.belief.refute import refute_claim
from sheldon.db import assert_pinned_engine, connect
from sheldon.gate.approve import approve
from sheldon.retrieval.recall import recall
from sheldon.schema import ApprovalStatus
from sheldon.seed.snapshot import load_seed


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


def test_w1_w2_and_r1_on_the_seed() -> None:
    db = connect()
    name = "sheldon_smoke_seed"
    try:
        db.select_graph(name).delete()
    except Exception:  # noqa: BLE001 - missing graph
        pass
    load_seed(name)
    try:
        rows = recall(name, 7)
        assert any(
            row.get("incident") == "INC-12" and row.get("evidence") == "E-41" for row in rows
        )
        assert (
            approve(name, 7, "b2", "A-smoke-missing", ["E-missing"], "ci", "ci", "ci", "s")
            is None
        )
        assert refute_claim(name, "C-7", ["E-60"], "ci", "ci", "s") is True
        status = db.select_graph(name).query(
            "MATCH (a:Approval {id: 'A-3'}) RETURN a.status"
        ).result_set[0][0]
        assert status == ApprovalStatus.STALE.value
    finally:
        db.select_graph(name).delete()
