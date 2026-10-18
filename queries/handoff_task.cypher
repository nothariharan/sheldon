// P4. Release the lease and keep the handoff on the task.
// One statement. Matches a claimed task this agent holds.

MATCH (t:Task {id: $task_id, owner: $agent_id, status: $claimed})
SET t.status = $open,
    t.owner = null,
    t.lease_expires = null,
    t.to_agent = $to_agent,
    t.note = $note
RETURN t.id
