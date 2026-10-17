// P1. Derive prev inside the query. Do not pass it in from the client.
// Embedding is omitted until EMBEDDING_DIM is locked in sheldon/schema.py.
// One statement. Spike the empty OPTIONAL MATCH on the pinned image before trusting it.

MATCH (inv:Investigation {id: $inv})
OPTIONAL MATCH (inv)<-[:IN_INVESTIGATION]-(p:Event)
WITH inv, p
ORDER BY p.ingest_seq DESC
LIMIT 1
CREATE (e:Event {
  id: $id,
  type: $type,
  text: $text,
  ts: $ts,
  agent_id: $agent_id,
  session_id: $session_id,
  source: $source,
  ingest_seq: $seq
})
CREATE (e)-[:IN_INVESTIGATION]->(inv)
FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END |
  CREATE (p)-[:NEXT {gap_ms: $gap_ms}]->(e)
)
RETURN e.id
