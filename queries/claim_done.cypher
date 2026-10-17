// W3. Same shape as W1, on a done claim.
// The cited run must be an executed test_run that exited 0 on this sha.
// Zero rows means refused. The client de-duplicates ids before this statement.
// MERGE on the approval id, so a second call does not write a second node.

MATCH (c:Claim {id: $cid, kind: $done_kind})
MATCH (e:Evidence)
WHERE e.id IN $ids
  AND e.executed = true
  AND e.sha = $sha
  AND e.kind = $test_run
  AND e.exit_code = 0
WITH c, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
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
