// Demo read. S0 (vector + keyword) cannot answer this.
// Which open tasks are still blocked by, or justified by, a hypothesis
// whose supporting evidence traces back to an action that was later
// refuted, and what's the chain?
// INVESTIGATES is unconfirmed (an earlier sketch said JUSTIFIED_BY).
// Every var-length pattern has an upper bound.

MATCH p = (t:Task {status: $open})-[:DEPENDS_ON*1..3]->(:Task)-[:INVESTIGATES]->(h:Hypothesis)-[:SUPPORTED_BY]->(:Event)<-[:RESULTED_IN|CAUSED_BY*1..3]-(a:Event {type: $action})
WHERE (h)-[:REFUTED_BY]->(:Event)
RETURN t.id, h.id, a.id, length(p)
