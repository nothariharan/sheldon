// P4. Extend the lease only when this agent still holds the task.

MATCH (t:Task {id: $task_id, owner: $agent_id, status: $claimed})
SET t.lease_expires = $now + $ttl
RETURN t.id
