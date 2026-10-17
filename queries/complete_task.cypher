// P4 stub. Status flip only. When you add PRODUCED events, keep them in
// this same statement. Do not add a second query and do not use MULTI/EXEC.

MATCH (t:Task {id: $task_id, owner: $agent_id, status: $claimed})
SET t.status = $done
RETURN t.id
