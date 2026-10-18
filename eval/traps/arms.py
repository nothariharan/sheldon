"""Arms for the trap suite.

Each arm is one class with ``name`` and ``blocks(graph, scenario) -> bool``.
True means the arm refuses the proposed action. ``graph`` is a fresh
``GRAPH.COPY`` of the frozen seed. The runner times ``blocks`` only.

To add an arm, implement that pair and append an instance in ``runner.ARMS``.
"""

from pathlib import Path
from typing import Any, Protocol

from sheldon.db import read
from sheldon.gate.approve import approve
from sheldon.gate.done import claim_done
from sheldon.preflight import preflight
from sheldon.retrieval.s0 import s0

REPO_ROOT = Path(__file__).resolve().parents[2]
REFUTED = "refuted"


class Arm(Protocol):
    """Check interface. One class, two attributes, same scenarios for every arm."""

    name: str

    def blocks(self, graph: str, scenario: dict[str, Any]) -> bool:
        """Return True when this arm refuses ``scenario`` on ``graph``."""


class NoMemory:
    """Always allow. This arm keeps no memory of the graph."""

    name = "no-memory"

    def blocks(self, graph: str, scenario: dict[str, Any]) -> bool:
        del graph, scenario
        return False


class SearchOnlyBaseline:
    """Keyword recall stand-in. Not a named product.

    Search ``scenario['text']`` with the S0 keyword path. Block when any hit
    is a claim whose status is refuted, or an incident whose ``HAS_CAUSE``
    claim is refuted. An open claim does not block. The command and the paths
    are not part of the query.
    """

    name = "search-only baseline"

    def blocks(self, graph: str, scenario: dict[str, Any]) -> bool:
        hits = s0(graph, scenario["text"])
        if not hits:
            return False
        rows = read(graph, "trap_hit_status", {"ids": [hit["id"] for hit in hits]})
        for row in rows:
            if row.get("claim_status") == REFUTED:
                return True
            if row.get("incident_cause_status") == REFUTED:
                return True
        return False


class SheldonArm:
    """Gates as they exist on main.

    A preflight action blocks only when ``preflight`` returns decision
    ``block``. ``warn`` and ``ok`` are allows. A done action blocks when
    ``claim_done`` returns None. An approval blocks when ``approve`` returns
    None. ``approve`` checks cited evidence. It does not walk ``RELIES_ON``
    or ``DEPENDS_ON``.
    """

    name = "sheldon"

    def blocks(self, graph: str, scenario: dict[str, Any]) -> bool:
        action = scenario["action"]
        kind = action["type"]
        if kind == "preflight":
            decision = preflight(
                graph,
                command=action["command"],
                paths=list(action["paths"]),
                repo_root=REPO_ROOT,
            )
            return decision["decision"] == "block"
        if kind == "done":
            approval_id = claim_done(
                graph,
                claim_id=action["claim_id"],
                head_sha=action["sha"],
                evidence_ids=list(action["evidence_ids"]),
                model="trap",
                session="trap",
            )
            return approval_id is None
        if kind == "approve":
            approval_id = approve(
                graph,
                pr_number=int(action["pr"]),
                head_sha=action["sha"],
                approval_id=f"A-trap-{scenario['id']}",
                evidence_ids=list(action["evidence_ids"]),
                by="trap",
                actor_kind="agent",
                model="trap",
                session="trap",
            )
            return approval_id is None
        raise ValueError(f"unknown action type {kind!r} on {scenario['id']}")
