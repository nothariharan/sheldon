// Check run. Read-only. Every approval FOR this PR, with the ids of cited
// evidence that is not an executed run on the head sha being checked.
// No rows means the PR is not in the graph yet. A PR with no approval
// returns one row whose approval is null.

MATCH (pr:PR {number: $pr})
OPTIONAL MATCH (a:Approval)-[:FOR]->(pr)
OPTIONAL MATCH (a)-[:CITES]->(e:Evidence)
WITH pr, a, collect(e) AS cited
RETURN pr.number AS pr, a.id AS approval, a.status AS status, a.sha AS sha,
       [x IN cited WHERE NOT (x.executed = true AND x.sha = $sha) | x.id] AS bad_evidence
ORDER BY approval
