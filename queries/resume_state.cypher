// Resume read: return tried, failed, believed, and next tasks, each citing ids.
// Refuted claims and hypotheses are never deleted.
// Do not write from this file.

OPTIONAL MATCH (act:Action)
OPTIONAL MATCH (act)-[:ATTEMPTED_FIX_FOR]->(act_c:Claim)
WITH collect(DISTINCT {
       id: act.id,
       cmd: act.cmd,
       fingerprint: act.fingerprint,
       claim_id: act_c.id
     }) AS raw_actions

OPTIONAL MATCH (ev:Event)
WHERE ev.type IN ['action', 'attempt', 'decision']
WITH raw_actions,
     collect(DISTINCT {
       id: ev.id,
       type: ev.type,
       text: ev.text
     }) AS raw_events

OPTIONAL MATCH (c_fail)
WHERE (c_fail:Claim OR c_fail:Hypothesis) AND c_fail.status = $refuted
OPTIONAL MATCH (c_fail)-[:REFUTED_BY]->(e_fail:Evidence)
WITH raw_actions, raw_events,
     c_fail, collect(DISTINCT e_fail.id) AS fail_ev_ids
WITH raw_actions, raw_events,
     collect(DISTINCT {
       id: c_fail.id,
       status: c_fail.status,
       text: coalesce(c_fail.text, c_fail.statement, ''),
       evidence_ids: [x IN fail_ev_ids WHERE x IS NOT NULL]
     }) AS raw_failed

OPTIONAL MATCH (c_bel)
WHERE (c_bel:Claim OR c_bel:Hypothesis) AND c_bel.status IN $believed_statuses
OPTIONAL MATCH (c_bel)-[:SUPPORTED_BY]->(e_bel:Evidence)
WITH raw_actions, raw_events, raw_failed,
     c_bel, collect(DISTINCT e_bel.id) AS bel_ev_ids
WITH raw_actions, raw_events, raw_failed,
     collect(DISTINCT {
       id: c_bel.id,
       status: c_bel.status,
       text: coalesce(c_bel.text, c_bel.statement, ''),
       confidence: c_bel.confidence,
       evidence_ids: [x IN bel_ev_ids WHERE x IS NOT NULL]
     }) AS raw_believed

OPTIONAL MATCH (t:Task)
OPTIONAL MATCH (t)-[dep:DEPENDS_ON]->(d:Task)
WHERE d.status <> $done AND ID(dep) >= 0
WITH raw_actions, raw_events, raw_failed, raw_believed,
     t, count(d) AS blockers
WITH raw_actions, raw_events, raw_failed, raw_believed,
     collect(DISTINCT {
       id: t.id,
       title: coalesce(t.title, t.id),
       status: t.status,
       owner: t.owner,
       lease_expires: t.lease_expires,
       stale: coalesce(t.stale, false),
       stale_because: t.stale_because,
       blockers: blockers
     }) AS raw_tasks

RETURN [a IN raw_actions WHERE a.id IS NOT NULL] + [e IN raw_events WHERE e.id IS NOT NULL] AS tried,
       [f IN raw_failed WHERE f.id IS NOT NULL] AS failed,
       [b IN raw_believed WHERE b.id IS NOT NULL] AS believed,
       [t IN raw_tasks WHERE t.id IS NOT NULL] AS next_tasks
