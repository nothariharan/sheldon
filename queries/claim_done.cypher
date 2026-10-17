// W3. Same shape as W1, on a done claim.
// The cited run must be an executed test_run that exited 0 on this sha.
// Zero rows means refused. Python does not filter the ids.

MATCH (c:Claim {id: $cid, kind: $done_kind})
MATCH (e:Evidence)
WHERE e.id IN $ids
  AND e.executed = true
  AND e.sha = $sha
  AND e.kind = $test_run
  AND e.exit_code = 0
WITH c, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
CREATE (a:Approval {
  id: $aid,
  sha: $sha,
  status: $status,
  at: timestamp(),
  model: $model,
  session: $session
})-[:FOR]->(c)
FOREACH (x IN ev | CREATE (a)-[:CITES]->(x))
RETURN a.id AS id
