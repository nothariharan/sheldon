// W1. One atomic write. Zero rows means refused.
// Duplicate ids fail because collect keeps one node and size($ids) does not.
// executed and sha are matched here. Python does not filter the ids.

MATCH (pr:PR {number: $pr, head_sha: $sha})
MATCH (e:Evidence) WHERE e.id IN $ids AND e.executed = true AND e.sha = $sha
WITH pr, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
CREATE (a:Approval {
  id: $aid,
  by: $by,
  actor_kind: $kind,
  sha: $sha,
  status: $status,
  at: timestamp(),
  model: $model,
  session: $session
})-[:FOR]->(pr)
FOREACH (x IN ev | CREATE (a)-[:CITES]->(x))
RETURN a.id AS id
