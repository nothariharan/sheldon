"""Outage policy for commit, push, and done.

The default is to block. ``SHELDON_FAIL_OPEN=1`` keeps the previous warn.
"""

import os
from typing import NoReturn


class DatabaseBlocked(RuntimeError):
    """The graph is down, so this action must not proceed."""


def fail_open() -> bool:
    return os.environ.get("SHELDON_FAIL_OPEN") == "1"


_CLOSED = {"commit", "push", "done"}


def is_closed_action(command: str) -> bool:
    """True for commit, push, and done. Reads and other commands stay open."""
    words = command.strip().lower().split()
    if not words:
        return False
    verb = words[1] if words[0] == "git" and len(words) > 1 else words[0]
    return verb in _CLOSED


def outage_decision(action: str, exc: BaseException, *, closed: bool = True) -> dict:
    """Return a preflight decision for a database error.

    Commit, push, and done block. Every other action warns.
    ``SHELDON_FAIL_OPEN=1`` warns even for those three.
    """
    if fail_open() or not closed:
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


def read_warning(exc: BaseException) -> str:
    """Warning text for a read that continues while the graph is down."""
    return f"Database unavailable; read bypassed: {exc}"


def raise_if_closed(action: str, exc: BaseException) -> NoReturn:
    """Re-raise ``exc`` when the escape hatch is set. Otherwise block."""
    if fail_open():
        raise exc
    raise DatabaseBlocked(
        f"Database unavailable; {action} blocked. "
        "Commit, push, and done do not proceed while the graph is down: "
        f"{exc}"
    ) from exc
