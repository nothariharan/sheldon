"""Session capsule.

Status: built. Generates task capsule with proving command and do-not directives
from touching refuted attempts, constrained to a token/character budget.
"""

from typing import Any

from sheldon.db import read
from sheldon.schema import HypothesisStatus

DEFAULT_PROVING_COMMAND = "sheldon run -- pytest"
DEFAULT_MAX_CHARS = 1200


def capsule(
    graph: str,
    task_id: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    db: Any = None,
) -> str:
    """Return task context with proving command and do-not directives from refuted attempts.

    Refuted attempts and evidence ids are never truncated mid-string. If an entry does not fit
    within max_chars, it is omitted.
    """
    params = {
        "task_id": task_id,
        "refuted": HypothesisStatus.REFUTED.value,
    }

    rows = read(graph, "capsule_task", params, db=db)
    if not rows:
        raise KeyError(f"task {task_id!r} not found in {graph}")

    row = rows[0]
    title = row.get("title") or task_id
    proving_cmd = row.get("proving_cmd") or DEFAULT_PROVING_COMMAND
    stale = bool(row.get("stale", False))
    stale_because = row.get("stale_because")

    # Priority 1: Reserved task header and proving command
    header_parts = [
        f"# Sheldon Task Context: {task_id} ({title})",
    ]
    if stale:
        reason = f" (claim {stale_because})" if stale_because else ""
        header_parts.append(
            f"> WARNING: Task is marked stale because dependent fix was refuted{reason}."
        )

    header_parts.extend([
        "",
        "## Proving Command",
        "Run before merge:",
        "```bash",
        proving_cmd,
        "```",
    ])

    base_text = "\n".join(header_parts)
    if len(base_text) >= max_chars:
        return base_text[:max_chars]

    # Priority 2: Refuted do-not directives
    raw_attempts = row.get("refuted_attempts") or []
    seen = set()
    unique_attempts = []
    for a in raw_attempts:
        att = dict(a) if isinstance(a, dict) else a
        key = (att.get("claim_id"), att.get("action_id"), att.get("evidence_id"))
        if key not in seen:
            seen.add(key)
            unique_attempts.append(att)

    if not unique_attempts:
        return base_text

    bullets = []
    for att in unique_attempts:
        cmd = att.get("cmd") or att.get("fingerprint")
        claim_id = att.get("claim_id")
        claim_text = att.get("claim_text") or "Refuted approach"
        evidence_id = att.get("evidence_id")

        ev_cite = f" Refuted by {evidence_id}." if evidence_id else ""
        if cmd:
            line = f"- DO NOT run `{cmd}`: {claim_text}.{ev_cite}"
        else:
            line = f"- DO NOT repeat {claim_id}: {claim_text}.{ev_cite}"
        bullets.append(line)

    section_header = "\n\n## Do-Not Directives (Refuted Attempts)\n"
    current_text = base_text + section_header

    # Pack bullets without exceeding max_chars and without cutting evidence IDs mid-string
    packed_bullets = []
    for bullet in bullets:
        candidate = current_text + "\n".join(packed_bullets + [bullet]) + "\n"
        if len(candidate) <= max_chars:
            packed_bullets.append(bullet)
        else:
            # Bullet does not fit within budget; omit to preserve whole-item integrity
            break

    if packed_bullets:
        return current_text + "\n".join(packed_bullets) + "\n"
    return base_text
