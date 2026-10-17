// Check run. Read-only. Look up each evidence id an agent cited on the PR.
// A missing id still returns a row, with found = false.

UNWIND $ids AS evidence_id
OPTIONAL MATCH (e:Evidence {id: evidence_id})
RETURN evidence_id AS evidence, e IS NOT NULL AS found, e.executed AS executed,
       e.sha AS sha, e.exit_code AS exit_code
