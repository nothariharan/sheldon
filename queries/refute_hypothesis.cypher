// Lead (a) and (b). One atomic write. No second statement. No DELETE.
// Dedupe evidence ids in the client. If any cited id is missing, MATCH
// fails, the WHERE on size fails, and this returns 0 rows.
// A refute with no dependent tasks must still return h.id. The stale
// walk is OPTIONAL plus FOREACH so an empty task list is not a rejection.
// INVESTIGATES is unconfirmed. See TASK_TO_HYPOTHESIS in sheldon/schema.py.
// Depth is *1..3. Do not open it to an unbounded pattern.

MATCH (h:Hypothesis {id: $hypothesis_id})
UNWIND $evidence_ids AS evidence_id
MATCH (e:Event {id: evidence_id})
WITH h, collect(e) AS evidence
WHERE size(evidence) = size($evidence_ids)
SET h.status = $refuted,
    h.confidence = $confidence
WITH h, evidence
UNWIND evidence AS e
MERGE (h)-[rb:REFUTED_BY]->(e)
SET rb.agent = $agent_id,
    rb.at = $at_ms
WITH DISTINCT h
OPTIONAL MATCH (h)<-[:INVESTIGATES*1..3]-(t:Task {status: $open})
WITH h, collect(t) AS tasks
FOREACH (task IN tasks | SET task.stale = true)
RETURN h.id, size(tasks) AS stale_tasks
