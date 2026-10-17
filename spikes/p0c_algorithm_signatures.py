"""
P0 follow-up C: the docs and the running engine DISAGREE about the algorithm
list. The engine is the truth. This dumps the real signatures and re-tests
every algorithm with the engine's actual names and argument shapes.
"""

from __future__ import annotations

import os

from falkordb import FalkorDB

HOST = os.environ.get("FALKORDB_HOST", "localhost")
PORT = int(os.environ.get("FALKORDB_PORT", "6379"))
GRAPH = "spike_p0c"
db = FalkorDB(host=HOST, port=PORT)
g = db.select_graph(GRAPH)


def try_q(cypher: str, params: dict | None = None):
    try:
        res = g.query(cypher, params or {})
        return True, res.result_set, res.header
    except Exception as exc:  # noqa: BLE001
        return False, str(exc), None


def reset() -> None:
    try:
        g.delete()
    except Exception:  # noqa: BLE001
        pass


print("\n" + "=" * 70)
print("P0C: real algorithm signatures + exact YIELD columns")
print("=" * 70)

# ---- 1. full procedure metadata, including yield columns -------------------
print("\n--- 1. full metadata for every algo.* procedure ---\n")
ok, rows, header = try_q("CALL dbms.procedures()")
print(f"    header: {header}")
if ok:
    for row in rows:
        text = " | ".join(str(c) for c in row)
        if "algo." in text:
            print(f"    {text}")

# ---- 2. labelPropagation, betweenness, harmonic with real signatures -------
print("\n--- 2. algorithms with the engine's real names ---\n")
reset()
g.query(
    """
    CREATE (a:S {n:'a'})-[:L]->(b:S {n:'b'}),
           (b)-[:L]->(c:S {n:'c'}),
           (a)-[:L]->(c),
           (a)-[:L]->(d:S {n:'d'})
    """
)
cases = [
    ("labelPropagation(S,L)",
     "CALL algo.labelPropagation('S','L') YIELD node, communityId RETURN node.n, communityId"),
    ("labelPropagation via node",
     "CALL algo.labelPropagation('S','L') YIELD node RETURN node.n"),
    ("betweenness(S,L)",
     "CALL algo.betweenness('S','L') YIELD node, score RETURN node.n, score"),
    ("betweenness(L)",
     "CALL algo.betweenness('L') YIELD node, score RETURN node.n, score"),
    ("HarmonicCentrality(S,L) [capital H]",
     "CALL algo.HarmonicCentrality('S','L') YIELD node, score RETURN node.n, score"),
    ("HarmonicCentrality(L) [capital H]",
     "CALL algo.HarmonicCentrality('L') YIELD node, score RETURN node.n, score"),
    ("WCC(NULL,NULL)",
     "CALL algo.WCC(NULL, NULL) YIELD node, componentId RETURN node.n, componentId"),
    ("WCC no args",
     "CALL algo.WCC() YIELD node, componentId RETURN node.n, componentId"),
    ("maxFlow(S,L)",
     "CALL algo.maxFlow('S','L') YIELD node RETURN node.n"),
]
for label, cy in cases:
    ok, out, hdr = try_q(cy)
    if ok:
        print(f"  [PASS] {label}\n         yield={hdr}\n         {repr(out)[:140]}")
    else:
        print(f"  [FAIL] {label}\n         {str(out)[:140]}")

# ---- 3. path algorithms need Node arguments, not strings -------------------
print("\n--- 3. path algorithms with node references ---\n")
resolve = (
    "MATCH (a:S {n:'a'}), (d:S {n:'d'}) "
)
for label, tail in [
    ("SPpaths",
     "CALL algo.SPpaths({sourceNode:a, targetNode:d, relTypes:['L'], maxLen:3}) "
     "YIELD path RETURN [n IN nodes(path) | n.n]"),
    ("SSpaths",
     "CALL algo.SSpaths({sourceNode:a, relTypes:['L'], maxLen:2}) "
     "YIELD path RETURN [n IN nodes(path) | n.n]"),
    ("AStar",
     "CALL algo.AStar({sourceNode:a, targetNode:d, relTypes:['L']}) "
     "YIELD path RETURN [n IN nodes(path) | n.n]"),
]:
    ok, out, hdr = try_q(resolve + tail)
    if ok:
        print(f"  [PASS] {label}\n         yield={hdr}\n         {repr(out)[:140]}")
    else:
        print(f"  [FAIL] {label}\n         {str(out)[:140]}")

# ---- 4. BFS with a node reference ------------------------------------------
print("\n--- 4. BFS with node reference ---\n")
ok, out, hdr = try_q(
    "MATCH (a:S {n:'a'}) CALL algo.BFS(a, 3, 'L') YIELD nodes, edges "
    "RETURN [n IN nodes | n.n], edges"
)
print(f"  [{'PASS' if ok else 'FAIL'}] BFS(node, depth, rel)\n         {repr(out)[:160] if ok else str(out)[:140]}")

# ---- 5. does the vector-index property-filter interaction hold with a range?
print("\n--- 5. vector query shapes ---\n")
reset()
try_q("CREATE VECTOR INDEX FOR (n:D) ON (n.emb) OPTIONS {dimension:4, similarityFunction:'cosine'}")
try_q(
    "CREATE (:D {id:'x', team:'red',  emb:vecf32([1.0,0.0,0.0,0.0])}),"
    " (:D {id:'y', team:'blue', emb:vecf32([0.9,0.1,0.0,0.0])}),"
    " (:D {id:'z', team:'blue', emb:vecf32([0.0,1.0,0.0,0.0])})"
)
for label, cy in [
    ("plain top-k",
     "CALL db.idx.vector.queryNodes('D','emb',3,vecf32([1.0,0.0,0.0,0.0])) YIELD node,score RETURN node.id,score"),
    ("+ WHERE equality",
     "CALL db.idx.vector.queryNodes('D','emb',3,vecf32([1.0,0.0,0.0,0.0])) YIELD node,score WHERE node.team='blue' RETURN node.id,score"),
    ("+ MATCH-join filter",
     "CALL db.idx.vector.queryNodes('D','emb',3,vecf32([1.0,0.0,0.0,0.0])) YIELD node,score MATCH (node) WHERE node.team='blue' RETURN node.id,score"),
]:
    ok, out, hdr = try_q(cy)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}\n         {repr(out)[:150] if ok else str(out)[:150]}")

print()
