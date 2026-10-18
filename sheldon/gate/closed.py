"""Outage policy for commit, push, and done.

The default is to block. ``SHELDON_FAIL_OPEN=1`` keeps the previous warn.
"""

import os
from typing import NoReturn


class DatabaseBlocked(RuntimeError):
    """The graph is down, so this action must not proceed."""


def fail_open() -> bool:
    return os.environ.get("SHELDON_FAIL_OPEN") == "1"


def outage_decision(action: str, exc: BaseException) -> dict:
    """Return a preflight decision for a database error."""
    if fail_open():
        return {
            "decision": "warn",
            "reason": f"Database unavailable; {action} bypassed: {exc}",
            "evidence_ids": [],
            "claim_ids": [],
            "incident_ids": [],
        }
    return {
        "decision": "block",
        "reason": (
            f"Database unavailable; {action} blocked. "
            "Commit, push, and done do not proceed while the graph is down: "
            f"{exc}"
        ),
        "evidence_ids": [],
        "claim_ids": [],
        "incident_ids": [],
    }


def raise_if_closed(action: str, exc: BaseException) -> NoReturn:
    """Re-raise ``exc`` when the escape hatch is set. Otherwise block."""
    if fail_open():
        raise exc
    raise DatabaseBlocked(
        f"Database unavailable; {action} blocked. "
        "Commit, push, and done do not proceed while the graph is down: "
        f"{exc}"
    ) from exc
