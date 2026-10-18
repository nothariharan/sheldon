"""R2 retry block.

Status: built.
Preflight checks proposed actions against the shared FalkorDB graph before tool execution.
Blocks exact retries of refuted fixes and emits warnings on touched incident files.
"""

import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sheldon.db import read
from sheldon.gate.closed import outage_decision
from sheldon.output import CommandResult, emit


def normalize_command(command: str) -> str:
    """Canonicalize command string syntactically by collapsing whitespace."""
    return " ".join(command.strip().split())


def canonicalize_paths(
    paths: Sequence[str],
    repo_root: str | Path | None = None,
) -> list[str]:
    """Resolve and normalize paths relative to repo_root.

    Invariants:
    - Resolves both relative and absolute paths to repo-relative POSIX format.
    - Rejects paths that escape the repository root via '..' or symlinks.
    - Deduplicates, sorts alphabetically, and is strictly idempotent.
    """
    root = Path(repo_root or Path.cwd()).resolve()
    canonical = set()

    for p in paths:
        s = p.strip()
        if not s:
            continue
        raw_path = Path(s)
        resolved = (raw_path if raw_path.is_absolute() else (root / raw_path)).resolve()

        try:
            rel = resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Security error: path escapes repository root: {s}") from exc

        posix_rel = rel.as_posix()
        if posix_rel != ".":
            canonical.add(posix_rel)

    return sorted(canonical)


def compute_action_fingerprint(
    command: str,
    paths: Sequence[str],
    repo_root: str | Path | None = None,
) -> str:
    """Generate deterministic syntactic action fingerprint."""
    norm_cmd = normalize_command(command)
    try:
        c_paths = canonicalize_paths(paths, repo_root)
    except ValueError:
        c_paths = [normalize_command(p) for p in paths if p.strip()]

    # Canonicalize embedded path in editor commands (e.g. 'edit ./checkout/cache.py')
    for prefix in ("edit ", "write "):
        if norm_cmd.startswith(prefix):
            raw_arg = norm_cmd[len(prefix) :].strip()
            try:
                norm_arg = canonicalize_paths([raw_arg], repo_root)
                if norm_arg:
                    norm_cmd = f"{prefix}{norm_arg[0]}"
            except ValueError:
                pass

    # Seed backward-compatibility rule for ACT-1 ('edit checkout/cache.py')
    if norm_cmd.startswith("edit ") and len(c_paths) == 1 and norm_cmd == f"edit {c_paths[0]}":
        return norm_cmd

    return f"{norm_cmd}|{','.join(c_paths)}"


def query_r2(
    graph: str,
    fingerprint: str,
    paths: Sequence[str],
    db: Any = None,
) -> dict[str, list[dict]]:
    """Query preflight_r2 through GRAPH.RO_QUERY."""
    rows = read(
        graph,
        "preflight_r2",
        {"fingerprint": fingerprint, "paths": list(paths)},
        db=db,
    )
    if not rows:
        return {"blocks": [], "warnings": []}

    row = rows[0]
    blocks = row.get("blocks") or []
    warnings = row.get("warnings") or []
    return {"blocks": list(blocks), "warnings": list(warnings)}


def decide_preflight(
    blocks: list[dict],
    warnings: list[dict],
    override: bool = False,
) -> dict[str, Any]:
    """Convert R2 query blocks and warnings into an ok / warn / block decision."""
    evidence_ids = sorted(
        {str(b["evidence"]) for b in blocks if isinstance(b, dict) and b.get("evidence")}
    )
    claim_ids = sorted(
        {str(b["claim"]) for b in blocks if isinstance(b, dict) and b.get("claim")}
    )
    incident_ids = sorted(
        {str(b["incident"]) for b in blocks if isinstance(b, dict) and b.get("incident")}
    )

    if override and blocks:
        return {
            "decision": "warn",
            "reason": (
                "Manual override provided; safety block bypassed with audit trail: "
                f"refuted by {', '.join(evidence_ids)}"
            ),
            "evidence_ids": evidence_ids,
            "claim_ids": claim_ids,
            "incident_ids": incident_ids,
        }

    if blocks:
        primary = blocks[0] if isinstance(blocks[0], dict) else {}
        inc_str = f" for {primary['incident']}" if primary.get("incident") else ""
        ev_str = ", ".join(evidence_ids) or primary.get("evidence", "evidence")
        reason_text = primary.get("reason", "Refuted fix")
        reason = (
            f"blocked: refuted by {ev_str}; "
            f"this edit repeats the fix tried{inc_str}; "
            f"{ev_str} refuted it: {reason_text}"
        )
        return {
            "decision": "block",
            "reason": reason,
            "evidence_ids": evidence_ids,
            "claim_ids": claim_ids,
            "incident_ids": incident_ids,
        }

    # Contextual warning for files associated with past incidents
    warn_incidents = sorted(
        {str(w["incident"]) for w in warnings if isinstance(w, dict) and w.get("incident")}
    )
    warn_evidence = sorted(
        {str(w["evidence"]) for w in warnings if isinstance(w, dict) and w.get("evidence")}
    )
    warn_claims = sorted(
        {str(w["claim"]) for w in warnings if isinstance(w, dict) and w.get("claim")}
    )

    if warn_incidents:
        return {
            "decision": "warn",
            "reason": (
                f"Files touched in prior incident(s) {', '.join(warn_incidents)}; "
                "alternative fix attempt allowed"
            ),
            "evidence_ids": warn_evidence,
            "claim_ids": warn_claims,
            "incident_ids": warn_incidents,
        }

    return {
        "decision": "ok",
        "reason": "Clean action",
        "evidence_ids": [],
        "claim_ids": [],
        "incident_ids": [],
    }


def preflight(
    graph: str,
    command: str,
    paths: list[str],
    override: bool = False,
    repo_root: str | Path | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Execute preflight check on proposed command and touched file paths."""
    effective_override = override or os.environ.get("SHELDON_PREFLIGHT_OVERRIDE") == "1"

    try:
        c_paths = canonicalize_paths(paths, repo_root)
    except ValueError as err:
        return {
            "decision": "warn",
            "reason": f"Path canonicalization warning: {err}",
            "evidence_ids": [],
            "claim_ids": [],
            "incident_ids": [],
        }

    fingerprint = compute_action_fingerprint(command, c_paths, repo_root)

    try:
        query_res = query_r2(graph, fingerprint, c_paths, db=db)
    except Exception as exc:  # noqa: BLE001
        return outage_decision("commit, push, and done", exc)

    return decide_preflight(
        query_res["blocks"],
        query_res["warnings"],
        override=effective_override,
    )


def preflight_result(
    graph: str,
    command: str,
    paths: list[str],
    override: bool = False,
    repo_root: str | Path | None = None,
    db: Any = None,
) -> CommandResult:
    """Return the preflight decision as a ``CommandResult``."""
    res = preflight(graph, command, paths, override=override, repo_root=repo_root, db=db)
    decision = res["decision"]
    text = res["reason"] if decision in {"block", "warn"} else ""
    return CommandResult(
        command="preflight",
        exit_code=2 if decision == "block" else 0,
        data=res,
        text=text,
        stream="stderr" if text else "stdout",
    )


def main(argv: list[str] | None = None, stdout=None, stderr=None, stdin=None) -> int:
    """CLI and Claude Code PreToolUse hook adapter."""
    import argparse

    parser = argparse.ArgumentParser(description="Sheldon preflight retry guard")
    parser.add_argument("--graph", default=os.environ.get("SHELDON_GRAPH", "sheldon:demo"))
    parser.add_argument("--command", default="")
    parser.add_argument("--paths", nargs="*", default=[])
    parser.add_argument("--override", action="store_true", default=False)
    parser.add_argument("--stdin", action="store_true", default=False)
    parser.add_argument("--json", action="store_true", help="print the result as JSON")

    args = parser.parse_args(argv)
    reader = stdin if stdin is not None else sys.stdin

    command = args.command
    paths = list(args.paths)
    graph = args.graph

    # Read from stdin if piped or --stdin flag given
    if args.stdin or not reader.isatty():
        try:
            stdin_data = reader.read().strip()
            if stdin_data:
                payload = json.loads(stdin_data)
                tool_name = payload.get("tool_name", "")
                tool_input = payload.get("tool_input", {})

                if tool_name in ("Edit", "Write"):
                    fpath = tool_input.get("file_path", "")
                    if fpath:
                        paths.append(fpath)
                    command = command or f"{tool_name.lower()} {fpath}"
                elif tool_name == "Bash":
                    cmd = tool_input.get("command", "")
                    command = command or cmd
                else:
                    command = command or payload.get("command", "")
                    paths.extend(payload.get("paths", []))
                graph = payload.get("graph", graph)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"sheldon: [WARN] could not parse hook stdin JSON: {exc}\n")

    result = preflight_result(graph, command, paths, override=args.override)
    return emit(result, as_json=args.json, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    sys.exit(main())
