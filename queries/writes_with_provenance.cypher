// Provenance read. One GRAPH.RO_QUERY.
// Claim, Evidence, Approval, and Action. Tasks are not in this read.

MATCH (n)
WHERE n:Claim OR n:Evidence OR n:Approval OR n:Action
RETURN n.id AS id, head(labels(n)) AS label, n.model AS model, n.session AS session
ORDER BY id
