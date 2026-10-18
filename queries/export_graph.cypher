// One read of every node and each outgoing edge. No writes.
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN labels(n) AS start_labels,
       properties(n) AS start_props,
       type(r) AS rel,
       properties(r) AS rel_props,
       labels(m) AS end_labels,
       properties(m) AS end_props
