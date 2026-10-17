// P4 stub. Releases the lease. The decision event belongs in this same
// statement once its shape is settled. Do not split the write.

MATCH (t:Task {id: $task_id, owner: $agent_id, status: $claimed})
SET t.status = $open,
    t.owner = null,
    t.lease_expires = null
RETURN t.id
