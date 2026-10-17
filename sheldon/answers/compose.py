"""PR comment from traversal rows.

Status: built. Generates PR review comment citing bundle evidence or abstains.
Does not decide gate or mutate graph beliefs.
"""

from typing import Any

COMPOSE_IS_STUB = False


def compose(graph: str, question: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """Return answer, citations, path, and abstained.

    Citations come strictly from ``evidence``. No ID or path is invented.
    An empty or insufficient bundle abstains.
    This function does not decide whether a refute lands.
    """
    del graph, question

    if not evidence:
        return {
            "answer": "Abstained: no incident or traversal evidence in the provided bundle.",
            "citations": [],
            "path": [],
            "abstained": True,
        }

    # Extract all valid, non-null IDs and paths present in the bundle
    citations_ordered: list[str] = []
    seen_citations = set()
    paths_ordered: list[str] = []
    seen_paths = set()

    incidents: dict[str, dict[str, Any]] = {}

    for row in evidence:
        f = row.get("file")
        v = row.get("via")
        for p in (f, v):
            if p and p not in seen_paths:
                seen_paths.add(p)
                paths_ordered.append(p)

        inc_id = row.get("incident")
        claim_id = row.get("claim")
        ev_id = row.get("evidence")

        for item_id in (inc_id, claim_id, ev_id):
            if item_id and item_id not in seen_citations:
                seen_citations.add(item_id)
                citations_ordered.append(item_id)

        if inc_id:
            if inc_id not in incidents:
                incidents[inc_id] = {
                    "title": row.get("title") or inc_id,
                    "refuted": [],
                    "supported": [],
                    "files": set(),
                }
            if f:
                incidents[inc_id]["files"].add(f)
            if v:
                incidents[inc_id]["files"].add(v)

            status = (row.get("status") or "").lower()
            rel = (row.get("relation") or "").upper()
            if status == "refuted" or rel == "REFUTED_BY":
                incidents[inc_id]["refuted"].append((claim_id, ev_id))
            elif rel == "SUPPORTED_BY" or status in ("supported", "open"):
                incidents[inc_id]["supported"].append((claim_id, ev_id))

    if not incidents and not citations_ordered:
        return {
            "answer": "Abstained: bundle contains no incident or claim findings.",
            "citations": [],
            "path": paths_ordered,
            "abstained": True,
        }

    # Build the grounded PR review comment
    paragraphs = []
    for inc_id, inc_info in incidents.items():
        title = inc_info["title"]
        file_summary = (
            ", ".join(sorted(inc_info["files"])) if inc_info["files"] else "changed files"
        )
        intro = f"In incident {inc_id} ({title!r}), touching {file_summary}:"
        details = []

        for cid, eid in inc_info["refuted"]:
            if cid and eid:
                details.append(f"fix {cid} was refuted by evidence {eid}")
            elif cid:
                details.append(f"fix {cid} was refuted")

        for cid, eid in inc_info["supported"]:
            if cid and eid:
                details.append(f"claim {cid} is supported by evidence {eid}")
            elif cid:
                details.append(f"claim {cid} remains supported")

        if details:
            body = "; ".join(details) + "."
            warning = (
                " Verify that changes in this PR do not repeat any refuted fix."
                if inc_info["refuted"]
                else ""
            )
            paragraphs.append(f"{intro} {body}{warning}")
        else:
            paragraphs.append(f"{intro} historical incident touched these paths.")

    answer = "\n\n".join(paragraphs)

    return {
        "answer": answer,
        "citations": citations_ordered,
        "path": paths_ordered,
        "abstained": False,
    }
