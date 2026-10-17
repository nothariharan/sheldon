import os

from falkordb import FalkorDB

db = FalkorDB(
    host=os.environ.get("FALKORDB_HOST", "localhost"),
    port=int(os.environ.get("FALKORDB_PORT", "6379")),
)
g = db.select_graph("spike_p0e")
try:
    g.delete()
except Exception:
    pass

# 4 reds VERY close to the query vector, 1 blue further away.
g.query(
    "CREATE VECTOR INDEX FOR (n:D) ON (n.emb) "
    "OPTIONS {dimension:4, similarityFunction:'cosine'}"
)
g.query(
    """
CREATE (:D {id:'r1',team:'red', emb:vecf32([1.0,0.00,0,0])}),
       (:D {id:'r2',team:'red', emb:vecf32([1.0,0.01,0,0])}),
       (:D {id:'r3',team:'red', emb:vecf32([1.0,0.02,0,0])}),
       (:D {id:'r4',team:'red', emb:vecf32([1.0,0.03,0,0])}),
       (:D {id:'b1',team:'blue',emb:vecf32([0.0,1.00,0,0])})
"""
)


def q(cy):
    try:
        return repr(g.query(cy).result_set)
    except Exception as e:
        return f"ERR {e}"


print(
    "all 5, k=5      :",
    q(
        "CALL db.idx.vector.queryNodes('D','emb',5,vecf32([1,0,0,0])) "
        "YIELD node,score RETURN node.id,score"
    ),
)
print(
    "k=2 NO filter   :",
    q(
        "CALL db.idx.vector.queryNodes('D','emb',2,vecf32([1,0,0,0])) "
        "YIELD node,score RETURN node.id,score"
    ),
)
print(
    "k=2 WHERE blue  :",
    q(
        "CALL db.idx.vector.queryNodes('D','emb',2,vecf32([1,0,0,0])) "
        "YIELD node,score WHERE node.team='blue' RETURN node.id,score"
    ),
)
print(
    "k=2 MATCH blue  :",
    q(
        "CALL db.idx.vector.queryNodes('D','emb',2,vecf32([1,0,0,0])) "
        "YIELD node,score MATCH (node) WHERE node.team='blue' RETURN node.id,score"
    ),
)
