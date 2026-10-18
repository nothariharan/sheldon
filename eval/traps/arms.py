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
from sheldon.preflight import compute_action_fingerprint, preflight
from sheldon.retrieval.s0 import keyword_terms, s0

REPO_ROOT = Path(__file__).resolve().parents[2]
REFUTED = "refuted"


def _compact_status(rows: list[dict]) -> list[dict]:
    compact = []
    for row in rows:
        compact.append(
            {
                "id": row.get("id"),
                "claim_status": row.get("claim_status"),
                "incident_cause_status": row.get("incident_cause_status"),
            }
        )
    return compact


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
        self.trace = "no-memory has no gate and returns allow"
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
        terms = keyword_terms(scenario["text"])
        hits = s0(graph, scenario["text"])
        ids = [hit["id"] for hit in hits]
        rows = read(graph, "trap_hit_status", {"ids": ids}) if ids else []
        blocked = any(
            row.get("claim_status") == REFUTED or row.get("incident_cause_status") == REFUTED
            for row in rows
        )
        self.trace = (
            f"s0_keyword terms={terms!r} hits={ids} "
            f"trap_hit_status={_compact_status(rows)} blocked={blocked}"
        )
        return blocked


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
            fingerprint = compute_action_fingerprint(
                action["command"], list(action["paths"]), REPO_ROOT
            )
            decision = preflight(
                graph,
                command=action["command"],
                paths=list(action["paths"]),
                repo_root=REPO_ROOT,
            )
            blocked = decision["decision"] == "block"
            self.trace = (
                "preflight queries/preflight_r2.cypher "
                f"fingerprint={fingerprint!r} returned decision={decision['decision']!r} "
                f"reason={decision['reason']!r} evidence_ids={decision['evidence_ids']}"
            )
            return blocked
        if kind == "done":
            approval_id = claim_done(
                graph,
                claim_id=action["claim_id"],
                head_sha=action["sha"],
                evidence_ids=list(action["evidence_ids"]),
                model="trap",
                session="trap",
            )
            self.trace = f"claim_done queries/claim_done.cypher returned {approval_id!r}"
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
            self.trace = f"approve queries/approve_pr.cypher returned {approval_id!r}"
            return approval_id is None
        raise ValueError(f"unknown action type {kind!r} on {scenario['id']}")
