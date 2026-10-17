"""Git-history ingest.

Status: to build. This function is not a working feature.
"""

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
    """To build. Write one history record. Do not take a previous id from the caller."""
    del graph, event_id, event_type, text, agent_id, session_id, ts_ms, source
    if RECORD_EVENT_IS_STUB:
        raise NotImplementedError("P1: queries/record_event.cypher")
