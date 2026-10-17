// R2 preflight query. Sent via GRAPH.RO_QUERY.
// Reads exact action blocks and file incident warnings.
// Zero matching actions or files returns empty collections, not 0 rows.

OPTIONAL MATCH (act:Action {fingerprint: $fingerprint})-[:ATTEMPTED_FIX_FOR]->(c_block:Claim {status: 'refuted'})-[:REFUTED_BY]->(e_block:Evidence {executed: true})
WHERE (e_block.exit_code IS NOT NULL AND e_block.exit_code <> 0) OR e_block.kind = 'ci_run'
OPTIONAL MATCH (inc_block:Incident)-[:HAS_CAUSE]->(c_block)

WITH collect(DISTINCT {
       action: act.id,
       claim: c_block.id,
       evidence: e_block.id,
       incident: inc_block.id,
       reason: coalesce(c_block.text, c_block.statement, 'Refuted fix')
     }) AS raw_blocks

UNWIND (CASE WHEN size($paths) = 0 THEN [null] ELSE $paths END) AS p
OPTIONAL MATCH (f:File {path: p})
OPTIONAL MATCH (f)-[:CO_CHANGED_WITH]-(n:File)
WITH raw_blocks, p, f, collect(DISTINCT n) AS neighbours
WITH raw_blocks, p, (CASE WHEN f IS NULL THEN [] ELSE [f] + neighbours END) AS near
UNWIND (CASE WHEN size(near) = 0 THEN [null] ELSE near END) AS g
OPTIONAL MATCH (g)<-[:TOUCHED]-(i:Incident)
OPTIONAL MATCH (i)-[:HAS_CAUSE]->(c_warn:Claim)
OPTIONAL MATCH (c_warn)-[:REFUTED_BY]->(e_warn:Evidence {executed: true})
WHERE (e_warn.exit_code IS NOT NULL AND e_warn.exit_code <> 0) OR e_warn.kind = 'ci_run'

WITH raw_blocks,
     collect(DISTINCT {
       file: p,
       incident: i.id,
       title: i.title,
       claim: c_warn.id,
       evidence: e_warn.id
     }) AS raw_warnings

RETURN [b IN raw_blocks WHERE b.claim IS NOT NULL] AS blocks,
       [w IN raw_warnings WHERE w.incident IS NOT NULL] AS warnings
