// Count repeated failed steps: actions matching a prior attempt on a refuted claim
// backed by executed non-zero evidence (MAST-style FM-1.3, arXiv:2503.13657).

MATCH (act:Action),
      (prior:Action)-[:ATTEMPTED_FIX_FOR]->(c)-[:REFUTED_BY]->(e:Evidence {executed: true})
WHERE act <> prior
  AND (c:Claim OR c:Hypothesis)
  AND c.status = $refuted
  AND (
    (act.fingerprint IS NOT NULL AND prior.fingerprint IS NOT NULL AND act.fingerprint = prior.fingerprint)
    OR (act.fingerprint IS NOT NULL AND act.fingerprint = prior.cmd)
    OR (prior.fingerprint IS NOT NULL AND act.cmd = prior.fingerprint)
    OR (act.cmd IS NOT NULL AND prior.cmd IS NOT NULL AND act.cmd = prior.cmd)
  )
  AND ((e.exit_code IS NOT NULL AND e.exit_code <> 0) OR e.kind = 'ci_run')
RETURN count(DISTINCT act) AS repeated_failed_steps
