// P4. One conditional write. N concurrent callers, exactly one winner.
// Alias the dependency relationship. An unaliased pattern under-counts.
// d.status <> $done is not index-backed. Fine at demo scale.
// $now comes from the service clock, not from the agent.

MATCH (t:Task {id: $task_id})
WHERE (t.status = $open OR (t.status = $claimed AND t.lease_expires < $now))
OPTIONAL MATCH (t)-[dep:DEPENDS_ON]->(d:Task)
WHERE d.status <> $done AND ID(dep) >= 0
WITH t, count(d) AS blockers
WHERE blockers = 0
SET t.status = $claimed,
    t.owner = $agent_id,
    t.lease_expires = $now + $ttl,
    t.version = coalesce(t.version, 0) + 1
RETURN t.id, t.version
