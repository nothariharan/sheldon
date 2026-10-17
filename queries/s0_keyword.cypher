// S0. Plain-memory baseline: keyword hits over stored text, no traversal.
// Read-only. $terms is a RediSearch OR query built by sheldon.retrieval.s0.
// A label with no full-text index returns no rows instead of an error, so
// create_fulltext_incident_title and create_fulltext_claim_text run first.
// The vector half waits on EMBEDDING_DIM in sheldon/schema.py.

CALL db.idx.fulltext.queryNodes('Incident', $terms) YIELD node, score
RETURN labels(node)[0] AS label, node.id AS id, node.title AS text, score
UNION ALL
CALL db.idx.fulltext.queryNodes('Claim', $terms) YIELD node, score
RETURN labels(node)[0] AS label, node.id AS id, node.text AS text, score
