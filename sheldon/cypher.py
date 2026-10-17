"""Load Cypher from queries/. Application code does not embed statements."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "queries"

# Files with a single statement the app can send.
RUNNABLE: tuple[str, ...] = (
    "record_event",
    "record_run",
    "claim_task",
    "heartbeat",
    "complete_task",
    "handoff_task",
    "resume_state",
    "refute_hypothesis",
    "q_star",
    "audit_refuted_without_evidence",
    "repeated_failed_steps",
    "create_index_event_id",
    "create_index_event_ts",
    "create_index_task_id",
    "create_index_hypothesis_id",
    "create_fulltext_event_text",
    "recall_pr",
    "s0_keyword",
    "create_fulltext_incident_title",
    "create_fulltext_claim_text",
    "ingest_pull_request",
    "check_approvals",
    "check_cited_evidence",
    "seed_demo",
    "count_nodes",
)

# Present so the decision is visible, not yet a statement we should run.
SKETCH_ONLY: tuple[str, ...] = ("create_vector_index_event",)


def query_path(name: str) -> Path:
    if name not in RUNNABLE and name not in SKETCH_ONLY:
        known = ", ".join(RUNNABLE + SKETCH_ONLY)
        raise KeyError(f"unknown query {name!r}. known: {known}")
    return QUERIES / f"{name}.cypher"


def load_query(name: str) -> str:
    """Return one Cypher statement.

    Full-line ``//`` comments are for the person editing the file. They are
    not sent to FalkorDB. A sketch that is only comments raises.
    """
    raw = query_path(name).read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if not line.lstrip().startswith("//")]
    text = "\n".join(lines).strip()
    if not text:
        raise ValueError(f"{name} is comments only and is not runnable yet")
    if ";" in text:
        raise ValueError(f"{name} must be one statement with no semicolon")
    return text
