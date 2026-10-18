// Text the mem0 trap arm stores. Read-only.
// The same stored text S0 searches: incident titles and claim text.

MATCH (n)
WHERE n:Incident OR n:Claim
RETURN n.id AS id, coalesce(n.text, n.title) AS text
ORDER BY id
