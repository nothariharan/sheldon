"""
P0 follow-up: enumerate what the engine ACTUALLY registers, and re-test the
four failures from p0_engine_semantics.py in isolation.

The first spike showed algo.CDLP and algo.betweennessCentrality "not
registered" even though docs.falkordb.com lists them. The docs may describe a
different build than 4.2.201. This script asks the engine directly.
"""

from __future__ import annotations

import os

from falkordb import FalkorDB

HOST = os.environ.get("FALKORDB_HOST", "localhost")
PORT = int(os.environ.get("FALKORDB_PORT", "6379"))
GRAPH = "spike_p0b"

db = FalkorDB(host=HOST, port=PORT)
g = db.select_graph(GRAPH)


def try_q(cypher: str, params: dict | None = None) -> tuple[bool, object]:
    try:
        res = g.query(cypher, params or {})
        return True, res.result_set
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def reset() -> None:
    try:
        g.delete()
    except Exception:  # noqa: BLE001
        pass


print("\n" + "=" * 70)
print("P0 FOLLOW-UP: procedure inventory + failure re-test")
print("=" * 70 + "\n")

# ---- 1. list every registered procedure -----------------------------------
print("--- 1. registered procedures ---")
for listing in (
    "CALL dbms.procedures()",
    "CALL db.procedures()",
    "CALL dbms.procedures() YIELD name RETURN name",
):
    ok, out = try_q(listing)
    if ok:
        names = []
        for row in out:  # type: ignore[union-attr]
            names.extend(str(c) for c in row)
        algo = sorted({n for n in names if n.lower().startswith("algo.")})
        print(f"  [PASS] {listing}  -> {len(names)} rows, {len(algo)} algo.*")
        for n in algo:
            print(f"         {n}")
        break
    print(f"  [FAIL] {listing}  {str(out)[:100]}")

# ---- 2. WCC and the centralities in isolation ------------------------------
print("\n--- 2. graph algorithms, isolated ---")
reset()
g.query(
    """
    CREATE (a:S {n:'a'})-[:L]->(b:S {n:'b'}),
           (b)-[:L]->(c:S {n:'c'}),
           (a)-[:L]->(c),
           (d:S {n:'d'})
    """
)
cases = [
    ("pageRank", "CALL algo.pageRank('S','L') YIELD node, score RETURN node.n, score"),
    ("WCC", "CALL algo.WCC('S','L') YIELD node, componentId RETURN node.n, componentId"),
    ("CDLP", "CALL algo.CDLP('S','L') YIELD node, communityId RETURN node.n, communityId"),
    ("betweennessCentrality(single-arg)",
     "CALL algo.betweennessCentrality('L') YIELD node, score RETURN node.n, score"),
    ("betweennessCentrality(two-arg)",
     "CALL algo.betweennessCentrality('S','L') YIELD node, score RETURN node.n, score"),
    ("harmonicCentrality(single-arg)",
     "CALL algo.harmonicCentrality('L') YIELD node, score RETURN node.n, score"),
    ("harmonicCentrality(two-arg)",
     "CALL algo.harmonicCentrality('S','L') YIELD node, score RETURN node.n, score"),
    ("MSF", "CALL algo.MSF('S','L') YIELD node RETURN node.n"),
    ("MaxFlow", "CALL algo.MaxFlow('s','t','S','L') YIELD flow RETURN flow"),
    ("SPpaths", "CALL algo.SPpaths({sourceNode:'a', targetNode:'c', relTypes:['L']}) YIELD path RETURN path"),
    ("SSpaths", "CALL algo.SSpaths({sourceNode:'a', relTypes:['L']}) YIELD path RETURN path"),
    ("AStar", "CALL algo.AStar({sourceNode:'a', targetNode:'c', relTypes:['L']}) YIELD path RETURN path"),
    ("BFS", "CALL algo.BFS('a', 3, 'L') YIELD nodes, edges RETURN nodes, edges"),
]
for label, cy in cases:
    ok, out = try_q(cy)
    verdict = "PASS" if ok else "FAIL"
    note = repr(out)[:110] if ok else str(out)[:110]
    print(f"  [{verdict}] {label}\n         {note}")

# ---- 3. does a vector index actually work on this build? -------------------
print("\n--- 3. vector index end-to-end ---")
reset()
ok, out = try_q(
    "CREATE VECTOR INDEX FOR (n:Doc) ON (n.emb) OPTIONS {dimension:4, similarityFunction:'cosine'}"
)
print(f"  [{'PASS' if ok else 'FAIL'}] create vector index\n         {repr(out)[:110] if ok else str(out)[:110]}")

ok, out = try_q(
    "CREATE (:Doc {id:'d1', emb:vecf32([1.0,0.0,0.0,0.0])}),"
    " (:Doc {id:'d2', emb:vecf32([0.0,1.0,0.0,0.0])})"
)
print(f"  [{'PASS' if ok else 'FAIL'}] insert vecf32 nodes\n         {repr(out)[:110] if ok else str(out)[:110]}")

ok, out = try_q(
    "CALL db.idx.vector.queryNodes('Doc','emb',2,vecf32([1.0,0.0,0.0,0.0])) "
    "YIELD node, score RETURN node.id, score"
)
print(f"  [{'PASS' if ok else 'FAIL'}] queryNodes YIELD node, score\n         {repr(out)[:130] if ok else str(out)[:130]}")

# ---- 4. does a vector query combine with a property filter? ----------------
ok, out = try_q(
    "CALL db.idx.vector.queryNodes('Doc','emb',2,vecf32([1.0,0.0,0.0,0.0])) "
    "YIELD node, score WHERE node.id = 'd1' RETURN node.id, score"
)
print(f"  [{'PASS' if ok else 'FAIL'}] vector query + WHERE property filter (docs say unsupported)\n         {repr(out)[:130] if ok else str(out)[:130]}")

print()
