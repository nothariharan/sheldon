// Capsule read: return task details and touching refuted attempts with evidence ids.
// Refuted claims and evidence are never deleted.
// Do not write from this file.

MATCH (t:Task {id: $task_id})
OPTIONAL MATCH (t)-[:DEPENDS_ON*1..2]->(c_direct:Claim {status: $refuted})
OPTIONAL MATCH (c_direct)-[:REFUTED_BY]->(e_dir:Evidence)
OPTIONAL MATCH (act_dir:Action)-[:ATTEMPTED_FIX_FOR]->(c_direct)

WITH t,
     collect(DISTINCT {
       action_id: act_dir.id,
       cmd: act_dir.cmd,
       fingerprint: act_dir.fingerprint,
       claim_id: c_direct.id,
       claim_text: coalesce(c_direct.text, c_direct.statement, ''),
       evidence_id: e_dir.id
     }) AS direct_attempts

OPTIONAL MATCH (t)-[:DEPENDS_ON*1..2]->(c:Claim)<-[:HAS_CAUSE]-(inc:Incident)-[:HAS_CAUSE]->(c_ref:Claim {status: $refuted})
OPTIONAL MATCH (c_ref)-[:REFUTED_BY]->(e_ref:Evidence)
OPTIONAL MATCH (act:Action)-[:ATTEMPTED_FIX_FOR]->(c_ref)
WITH t, direct_attempts,
     collect(DISTINCT {
       action_id: act.id,
       cmd: act.cmd,
       fingerprint: act.fingerprint,
       claim_id: c_ref.id,
       claim_text: coalesce(c_ref.text, c_ref.statement, ''),
       evidence_id: e_ref.id
     }) AS inc_attempts

WITH t, [d IN direct_attempts WHERE d.claim_id IS NOT NULL] + [i IN inc_attempts WHERE i.claim_id IS NOT NULL] AS all_attempts
RETURN t.id AS task_id,
       t.title AS title,
       t.proving_command AS proving_cmd,
       coalesce(t.stale, false) AS stale,
       t.stale_because AS stale_because,
       all_attempts AS refuted_attempts
