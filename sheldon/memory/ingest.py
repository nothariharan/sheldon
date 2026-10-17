"""P1. Append-only event chain. Prev is derived inside the query."""

# Flip to False in the PR that runs queries/record_event.cypher.
RECORD_EVENT_IS_STUB = True


def record_event(
    graph: str,
    event_id: str,
    event_type: str,
    text: str,
    agent_id: str,
    session_id: str,
    ts_ms: int,
    source: str = "agent",
) -> str:
    """Write one event and its NEXT link. Return the event id.

    Do not accept a client-computed previous id. The query derives it.
    Embedding stays off until EMBEDDING_DIM is set in schema.py.
    """
    del graph, event_id, event_type, text, agent_id, session_id, ts_ms, source
    if RECORD_EVENT_IS_STUB:
        raise NotImplementedError("P1: queries/record_event.cypher")
