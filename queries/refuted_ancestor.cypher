// Shortest path from $id to a refuted claim, including the claim itself.
// claim_ids, edge_types, and the REFUTED_BY evidence id explain a refusal.
// This read does not write. Zero rows means the claim is missing.
// *1..3 is the same hop window W2 uses. A refuted start is the 0-hop case.

MATCH (start:Claim {id: $id})
OPTIONAL MATCH p = (start)-[:RELIES_ON|DEPENDS_ON*1..3]->(hit:Claim {status: $refuted})
WITH start, p, hit
ORDER BY CASE WHEN p IS NULL THEN 99 ELSE length(p) END
LIMIT 1
WITH CASE WHEN start.status = $refuted THEN start ELSE hit END AS target,
     CASE
       WHEN start.status = $refuted THEN [start.id]
       WHEN p IS NULL THEN []
       ELSE [n IN nodes(p) | n.id]
     END AS claim_ids,
     CASE
       WHEN start.status = $refuted OR p IS NULL THEN []
       ELSE [r IN relationships(p) | type(r)]
     END AS edge_types
OPTIONAL MATCH (target)-[:REFUTED_BY]->(e:Evidence)
WITH claim_ids, edge_types, head(collect(DISTINCT e.id)) AS evidence
RETURN claim_ids, edge_types, evidence
