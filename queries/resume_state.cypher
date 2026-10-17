// P4 stub read. Replace with tried / failed / believed / next, each citing ids.
// Refuted hypotheses stay in the result. They are never deleted.
// Do not write from this file.

MATCH (h:Hypothesis)
WHERE h.status = $open OR h.status = $supported OR h.status = $refuted
RETURN h.id, h.status, h.confidence, h.statement
