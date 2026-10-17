// Record an action during evaluation runs.
// Sent via GRAPH.QUERY.

CREATE (act:Action {
  id: $id,
  cmd: $cmd,
  fingerprint: $fingerprint,
  session: $session
})
RETURN act.id AS action_id
