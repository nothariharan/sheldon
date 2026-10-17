// Demo audit. A healthy graph returns 0 rows.
// Refuted hypotheses with no REFUTED_BY edge to an Event.

MATCH (h:Hypothesis {status: $refuted})
WHERE NOT (h)-[:REFUTED_BY]->(:Event)
RETURN h.id
