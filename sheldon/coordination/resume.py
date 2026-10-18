"""Resume read.

Status: built. Queries tried, failed, believed, and next tasks citing ids.
Refuted claims and hypotheses are preserved and never deleted.
"""

import os
import time
from typing import Any

from sheldon.db import read
from sheldon.gate.closed import read_warning
from sheldon.output import CommandResult, emit
from sheldon.schema import EventType, HypothesisStatus, TaskStatus


def resume(graph: str, agent_id: str, now_ms: int | None = None) -> dict[str, Any]:
    """Return tried, failed, believed, and next, with ids.

    Refuted claims and hypotheses are preserved and never deleted.
    """
    if now_ms is None:
        now_ms = int(time.time() * 1000)

    params = {
        "refuted": HypothesisStatus.REFUTED.value,
        "believed_statuses": [
            HypothesisStatus.SUPPORTED.value,
            HypothesisStatus.OPEN.value,
        ],
        "tried_event_types": [
            EventType.ACTION.value,
            EventType.DECISION.value,
        ],
        "done": TaskStatus.DONE.value,
    }

    rows = read(graph, "resume_state", params)
    if not rows:
        return {
            "tried": [],
            "failed": [],
            "believed": [],
            "next": [],
        }

    row = rows[0]
    tried = [dict(t) if isinstance(t, dict) else t for t in (row.get("tried") or [])]
    failed = [dict(f) if isinstance(f, dict) else f for f in (row.get("failed") or [])]
    believed = [dict(b) if isinstance(b, dict) else b for b in (row.get("believed") or [])]
    raw_tasks = row.get("next_tasks") or []

    next_tasks = []
    for t in raw_tasks:
        task = dict(t) if isinstance(t, dict) else t
        status = task.get("status")
        # Completed tasks are not eligible next work
        if status == TaskStatus.DONE.value:
            continue

        owner = task.get("owner")
        lease_expires = task.get("lease_expires")
        blockers = task.get("blockers", 0)
        stale = bool(task.get("stale", False))

        is_active = (
            owner == agent_id
            and status == TaskStatus.CLAIMED.value
            and (lease_expires is None or lease_expires >= now_ms)
        )
        is_expired = (
            status == TaskStatus.CLAIMED.value
            and lease_expires is not None
            and lease_expires < now_ms
        )
        is_open = status == TaskStatus.OPEN.value or is_expired
        claimable = is_open and blockers == 0 and not stale

        task_info = {
            "id": task["id"],
            "title": task.get("title", task["id"]),
            "status": status,
            "owner": owner,
            "stale": stale,
            "stale_because": task.get("stale_because"),
            "blockers": blockers,
            "claimable": claimable,
            "active": is_active,
        }
        next_tasks.append(task_info)

    # Order: active task held by this agent first, then claimable (unblocked, not stale),
    # then other open/claimed tasks
    next_tasks.sort(key=lambda x: (not x["active"], not x["claimable"], x["stale"], x["id"]))

    return {
        "tried": tried,
        "failed": failed,
        "believed": believed,
        "next": next_tasks,
    }


def resume_result(graph: str, agent_id: str, now_ms: int | None = None) -> CommandResult:
    """Return the resume dict as a ``CommandResult``."""
    try:
        data = resume(graph, agent_id, now_ms=now_ms)
    except (ConnectionError, OSError) as exc:
        reason = read_warning(exc)
        return CommandResult(
            command="resume",
            exit_code=0,
            data={
                "tried": [],
                "failed": [],
                "believed": [],
                "next": [],
                "decision": "warn",
                "reason": reason,
            },
            text=reason,
            stream="stderr",
        )
    text = "\n".join(
        f"{key} {len(data[key])}" for key in ("tried", "failed", "believed", "next")
    )
    return CommandResult(command="resume", exit_code=0, data=data, text=text)


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    """Print a resume read. ``--json`` prints the result object."""
    import argparse

    parser = argparse.ArgumentParser(prog="python -m sheldon.coordination.resume")
    parser.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon"))
    parser.add_argument("--agent", default=os.environ.get("SHELDON_AGENT", "agent"))
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    result = resume_result(args.graph, args.agent)
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    import sys

    sys.exit(main())
