// Read the confidence refute_hypothesis must write back. The locked
// sketch sets h.confidence = $confidence, so a null parameter wipes it.

MATCH (h:Hypothesis {id: $hypothesis_id})
RETURN h.confidence AS confidence
