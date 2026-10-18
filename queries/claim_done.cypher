// W3. Same shape as W1, on a done claim.
// The cited run must be an executed test_run that exited 0 on this sha.
// Zero rows means refused. The client de-duplicates ids before this statement.
// MERGE on the approval id, so a second call does not write a second node.
// The write is also refused when this claim is refuted, or reaches a refuted
// claim in 1..3 RELIES_ON or DEPENDS_ON hops. That is the W2 hop window.

MATCH (c:Claim {id: $cid, kind: $done_kind})
MATCH (e:Evidence)
WHERE e.id IN $ids
  AND e.executed = true
  AND e.sha = $sha
  AND e.kind = $test_run
  AND e.exit_code = 0
WITH c, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
OPTIONAL MATCH (c)-[:RELIES_ON|DEPENDS_ON*1..3]->(ancestor:Claim {status: $refuted})
WITH c, ev, [a IN collect(DISTINCT ancestor) WHERE a IS NOT NULL] AS ancestors
WHERE c.status <> $refuted AND size(ancestors) = 0
MERGE (a:Approval {id: $aid})
ON CREATE SET
  a.sha = $sha,
  a.status = $status,
  a.at = timestamp(),
  a.model = $model,
  a.session = $session
MERGE (a)-[:FOR]->(c)
FOREACH (x IN ev | MERGE (a)-[:CITES]->(x))
RETURN a.id AS id
