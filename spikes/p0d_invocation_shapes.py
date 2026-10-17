"""P0 follow-up D: exact invocation for the algorithms whose argument shape is
still ambiguous. Answers only - no new questions."""

from __future__ import annotations

import os

from falkordb import FalkorDB

db = FalkorDB(host=os.environ.get("FALKORDB_HOST", "localhost"), port=int(os.environ.get("FALKORDB_PORT", "6379")))
g = db.select_graph("spike_p0d")


def try_q(cypher: str):
    try:
        res = g.query(cypher)
        return True, res.result_set
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


try:
    g.delete()
except Exception:  # noqa: BLE001
    pass

g.query(
    """
    CREATE (a:S {n:'a'})-[:L]->(b:S {n:'b'}),
           (b)-[:L]->(c:S {n:'c'}),
           (a)-[:L]->(c),
           (a)-[:L]->(d:S {n:'d'}),
           (e:S {n:'e'})
    """
)

print("\n" + "=" * 70)
print("P0D: exact invocation shapes")
print("=" * 70 + "\n")

cases = [
    ("labelPropagation() no-arg",
     "CALL algo.labelPropagation() YIELD node, communityId RETURN node.n, communityId"),
    ("labelPropagation() full",
     "CALL algo.labelPropagation() YIELD node, communityId RETURN node.n, communityId ORDER BY node.n"),
    ("betweenness() no-arg",
     "CALL algo.betweenness() YIELD node, score RETURN node.n, score ORDER BY node.n"),
    ("HarmonicCentrality(map)",
     "CALL algo.HarmonicCentrality({relTypes:['L']}) YIELD node, score RETURN node.n, score"),
    ("HarmonicCentrality(node-ref)",
     "MATCH (a:S {n:'a'}) CALL algo.HarmonicCentrality(a) YIELD node, score RETURN node.n, score"),
    ("WCC() full",
     "CALL algo.WCC() YIELD node, componentId RETURN node.n, componentId ORDER BY node.n"),
    ("pageRank() no-arg",
     "CALL algo.pageRank() YIELD node, score RETURN node.n, score ORDER BY node.n"),
]
for label, cy in cases:
    ok, out = try_q(cy)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}\n         {repr(out)[:150] if ok else str(out)[:150]}")

print()
