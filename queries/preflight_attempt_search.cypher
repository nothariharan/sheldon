// Fallback when the exact fingerprint misses.
// Full-text over claim text, then keep a hit only when the graph says it is
// a failed attempt on one of $paths, or it is the refuted claim $claim.
// $claim may be ''. $terms is a RediSearch OR query. Zero hits return no rows.

CALL db.idx.fulltext.queryNodes('Claim', $terms) YIELD node, score
WHERE node.status = $refuted
OPTIONAL MATCH (act:Action)-[:ATTEMPTED_FIX_FOR]->(node)
OPTIONAL MATCH (node)-[:REFUTED_BY]->(e:Evidence {executed: true})
WHERE (e.exit_code IS NOT NULL AND e.exit_code <> 0) OR e.kind = 'ci_run'
OPTIONAL MATCH (inc:Incident)-[:HAS_CAUSE]->(node)
WITH node, act, e, inc, [f IN coalesce(act.files, []) WHERE f IN $paths] AS shared
WHERE e IS NOT NULL AND (size(shared) > 0 OR ($claim <> '' AND node.id = $claim))
RETURN DISTINCT node.id AS claim,
       e.id AS evidence,
       act.id AS action,
       inc.id AS incident,
       coalesce(node.text, 'Refuted fix') AS reason
