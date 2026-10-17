"""Names the rest of the code must share. Do not invent a second copy.

Hypothesis status is a team decision. It is recorded here so parallel
branches do not each pick a vocabulary. Confirm it before the demo.
"""

from enum import StrEnum

# Spikes ran against an image that reported module 42201 (4.22.1).
# 4.x tags start with v. 6.x tags do not. Never latest or edge.
# Switch to falkordb/falkordb:6.0.2 only if a JS UDF is adopted, then set
# FALKORDB_MODULE_VERSION from MODULE LIST on that image.
FALKORDB_IMAGE = "falkordb/falkordb:v4.22.1"
FALKORDB_MODULE_VERSION = 42201

# Locked. The refute write walks dependent tasks at this depth.
STALE_MIN_HOPS = 1
STALE_MAX_HOPS = 3

# Conditional, default off. Turn on only after the evidence-id gate is green.
PATH_CHECK_MAX_HOPS: int | None = None

# Lock this before creating a vector index. None means "not chosen".
EMBEDDING_DIM: int | None = None

# Example in the papers, not a decision. None means "not chosen".
CONFIDENCE_ON_REFUTE: float | None = None

EVAL_SEED_GRAPH = "inv_seed"


class HypothesisStatus(StrEnum):
    """Working set. Confirm with the team.

    The docs used three vocabularies:

    - ``open`` / ``supported`` / ``refuted`` on the Hypothesis node (stuff.md). Chosen.
    - ``proposed`` / ``confirmed`` / ``rejected`` for causal edges. P5 is cut.
      Do not put these on a Hypothesis.
    - ``active`` / ``stale`` / ``unresolved``, the STALE paper's read-time markers.
      Not our schema. Task staleness is a boolean property, not a status.

    A refute sets ``refuted`` and ``confidence``. The node is never deleted.
    """

    OPEN = "open"
    SUPPORTED = "supported"
    REFUTED = "refuted"


class TaskStatus(StrEnum):
    """From stuff.md. Older notes used READY / IN_PROGRESS / DONE.

    ``stale`` is a boolean on the task, so an open task can be stale.
    """

    OPEN = "open"
    CLAIMED = "claimed"
    DONE = "done"
    BLOCKED = "blocked"


class ApprovalStatus(StrEnum):
    """From docs/plan/deep.md section 5. W2 sets ``stale``. Nothing deletes an approval."""

    ACTIVE = "active"
    STALE = "stale"


class EventType(StrEnum):
    OBSERVATION = "observation"
    ACTION = "action"
    RESULT = "result"
    DECISION = "decision"
    NOTE = "note"


INVESTIGATION = "Investigation"
SESSION = "Session"
AGENT = "Agent"
EVENT = "Event"
ENTITY = "Entity"
HYPOTHESIS = "Hypothesis"
TASK = "Task"

NEXT = "NEXT"
IN_INVESTIGATION = "IN_INVESTIGATION"
IN_SESSION = "IN_SESSION"
INVOLVES = "INVOLVES"
RELATED_TO = "RELATED_TO"
CAUSED_BY = "CAUSED_BY"
RESULTED_IN = "RESULTED_IN"
SUPPORTED_BY = "SUPPORTED_BY"
REFUTED_BY = "REFUTED_BY"
DEPENDS_ON = "DEPENDS_ON"
PRODUCED = "PRODUCED"

# stuff.md says INVESTIGATES. An earlier Q* sketch said JUSTIFIED_BY.
# Confirm before the demo. Queries should use this constant's value.
TASK_TO_HYPOTHESIS = "INVESTIGATES"


def investigation_graph(investigation_id: str) -> str:
    """One FalkorDB key per investigation. The id is the tenant unit."""
    if not investigation_id or not investigation_id.replace("_", "").isalnum():
        raise ValueError("investigation id must be letters, digits, and underscores")
    return f"inv_{investigation_id}"


# Constraints are a backstop. They can make a property required or unique.
# They cannot require an edge, and they cannot check that a cited id exists.
# The evidence gate lives in queries/refute_hypothesis.cypher.
# UNIQUE needs an exact-match index first. Confirm that command on v4.22.1
# before applying these. The range indexes in queries/ may not be enough.
CONSTRAINTS: tuple[tuple[str, str, str, str], ...] = (
    ("MANDATORY", "NODE", HYPOTHESIS, "status"),
    ("MANDATORY", "NODE", EVENT, "id"),
    ("UNIQUE", "NODE", EVENT, "id"),
    ("UNIQUE", "NODE", HYPOTHESIS, "id"),
    ("UNIQUE", "NODE", TASK, "id"),
    ("MANDATORY", "RELATIONSHIP", REFUTED_BY, "agent"),
    ("MANDATORY", "RELATIONSHIP", REFUTED_BY, "at"),
)
