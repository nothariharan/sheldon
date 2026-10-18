// Status of S0 hits for the trap suite. Read-only.
// A claim hit returns claim_status. An incident hit returns the status
// of each HAS_CAUSE claim, one row per cause. An unknown id returns nulls.

UNWIND $ids AS id
OPTIONAL MATCH (c:Claim {id: id})
OPTIONAL MATCH (i:Incident {id: id})-[:HAS_CAUSE]->(cause:Claim)
RETURN id AS id, c.status AS claim_status, cause.status AS incident_cause_status
