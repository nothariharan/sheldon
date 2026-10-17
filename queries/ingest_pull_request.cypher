// pr-ingest. One statement. The PR's changed files for one head sha.
// A new push replaces the changed-file set: CHANGES edges to files the PR no
// longer touches are removed. File nodes are never deleted, and an existing
// File (from history ingest) is reused by path. Only the edge is derived data.
// Write paths elsewhere use CREATE for Claim. PR and File are keyed by
// number and path, so MERGE is the intended upsert here.

MERGE (pr:PR {number: $number})
SET pr.head_sha = $head_sha
WITH pr
OPTIONAL MATCH (pr)-[old:CHANGES]->(gone:File)
WHERE NOT gone.path IN $paths
DELETE old
WITH DISTINCT pr
UNWIND $paths AS path
MERGE (f:File {path: path})
MERGE (pr)-[c:CHANGES]->(f)
SET c.sha = $head_sha
RETURN count(c) AS changes
