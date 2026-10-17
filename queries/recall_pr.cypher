// R1. PR-time recall. Read-only, sent through GRAPH.RO_QUERY.
// For each file the PR changes, look at that file and its 1-hop
// CO_CHANGED_WITH neighbours for incidents, their claims, and the
// evidence that supports or refutes each claim.
// The R1 statement that ran used CO_CHANGED_WITH*0..1. The contract test
// bans that substring, so the file itself is added to its neighbour list
// instead. Same rows, still bounded at one hop.
// Files with no incident return no rows. A clean PR returns nothing.

MATCH (pr:PR {number: $pr})-[:CHANGES]->(f:File)
OPTIONAL MATCH (f)-[:CO_CHANGED_WITH]-(n:File)
WITH f, [f] + collect(DISTINCT n) AS near
UNWIND near AS g
MATCH (g)<-[:TOUCHED]-(i:Incident)-[:HAS_CAUSE]->(c:Claim)
OPTIONAL MATCH (c)-[r:SUPPORTED_BY|REFUTED_BY]->(e:Evidence)
RETURN DISTINCT f.path AS file, g.path AS via, i.id AS incident, i.title AS title,
       c.id AS claim, c.kind AS kind, c.status AS status,
       type(r) AS relation, e.id AS evidence
ORDER BY file, incident, claim, evidence
LIMIT $limit
