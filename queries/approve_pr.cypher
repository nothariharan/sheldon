// W1. One atomic write. Zero rows means refused.
// Duplicate ids fail because collect keeps one node and size($ids) does not.
// executed and sha are matched here. Python does not filter the ids.
// $cited is optional (''). When set, the approval RELIES_ON that claim, and
// the write is refused if the claim is missing, refuted, or reaches a
// refuted claim in 1..3 RELIES_ON or DEPENDS_ON hops. That is the same
// hop window W2 uses when it stales dependents.

MATCH (pr:PR {number: $pr, head_sha: $sha})
MATCH (e:Evidence) WHERE e.id IN $ids AND e.executed = true AND e.sha = $sha
WITH pr, collect(e) AS ev
WHERE size($ids) > 0 AND size(ev) = size($ids)
OPTIONAL MATCH (cited:Claim {id: $cited})
OPTIONAL MATCH (cited)-[:RELIES_ON|DEPENDS_ON*1..3]->(ancestor:Claim {status: $refuted})
WITH pr, ev, cited, [a IN collect(DISTINCT ancestor) WHERE a IS NOT NULL] AS ancestors
WHERE $cited = '' OR (cited IS NOT NULL AND cited.status <> $refuted AND size(ancestors) = 0)
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
FOREACH (c IN CASE WHEN $cited = '' THEN [] ELSE [cited] END | CREATE (a)-[:RELIES_ON]->(c))
RETURN a.id AS id
