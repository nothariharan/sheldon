"""Resume read.

Status: built. Queries tried, failed, believed, and next tasks citing ids.
Refuted claims and hypotheses are preserved and never deleted.
"""

import time
from typing import Any

from sheldon.db import read
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
            "agent_id": agent_id,
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
        "agent_id": agent_id,
        "tried": tried,
        "failed": failed,
        "believed": believed,
        "next": next_tasks,
    }
