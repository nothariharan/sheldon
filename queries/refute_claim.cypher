// W2. The statement that ran, one write. The older sketch stays in
// refute_hypothesis.cypher because the contract test locks that file.
// A claim is refuted, never marked stale. Dependents at up to 3 hops:
// an approval's status becomes stale; a task keeps its status and gets
// the boolean stale. schema.py owns that boolean.
// Zero rows means the evidence did not all match. Nothing is deleted.

MATCH (c:Claim {id: $cid})
MATCH (e:Evidence) WHERE e.id IN $ids AND e.executed = true
WITH c, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
SET c.status = $refuted,
    c.confidence = c.confidence - $alpha,
    c.refuted_at = timestamp()
FOREACH (x IN ev |
  CREATE (c)-[:REFUTED_BY {agent: $agent, model: $model, session: $session, at: timestamp()}]->(x)
)
WITH c
OPTIONAL MATCH (c)<-[:RELIES_ON|DEPENDS_ON*1..3]-(d)
WHERE d IS NOT NULL AND NOT d:Claim AND d.status IN $live
WITH c, collect(DISTINCT d) AS deps
FOREACH (x IN deps |
  SET x.stale_because = c.id,
      x.status = CASE WHEN x:Task THEN x.status ELSE $stale END,
      x.stale = CASE WHEN x:Task THEN true ELSE x.stale END
)
RETURN c.id AS id, size(deps) AS staled
