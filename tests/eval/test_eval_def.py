"""Tests for docs/plan/eval-def.md and the repeated failed step taxonomy.

Verifies:
- Definition exists and satisfies TASKS.md requirements (MAST step repetition FM-1.3,
  arXiv 2503.13657, TIDE definition-only arXiv 2602.02196).
- No empirical counts or measurement results appear in the file.
- The 7-case operational taxonomy is complete and verifiable.
- Classification logic correctly distinguishes exact/syntactic retries (block),
  legitimate alternatives on the same file (warn/allow), unexecuted evidence (unverified),
  and clean actions (ok).
"""

import re
from enum import StrEnum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DEF_PATH = ROOT / "docs" / "plan" / "eval-def.md"


class ActionDecision(StrEnum):
    BLOCK = "block"
    WARN = "warn"
    OK = "ok"
    UNVERIFIED = "unverified"
    FAIL_OPEN = "fail_open"


def normalize_cmd(cmd: str) -> str:
    return " ".join(cmd.strip().split())


def normalize_paths(paths: list[str], root: Path | None = None) -> list[str]:
    repo_root = (root or ROOT).resolve()
    clean = []
    for p in paths:
        raw = p.strip()
        if not raw:
            continue
        path_obj = Path(raw)
        resolved = (path_obj if path_obj.is_absolute() else (repo_root / path_obj)).resolve()
        try:
            rel = resolved.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError(f"Path outside repository: {p}") from exc
        posix = rel.as_posix()
        if posix != ".":
            clean.append(posix)
    return sorted(set(clean))


def compute_fp(cmd: str, paths: list[str], root: Path | None = None) -> str:
    n_cmd = normalize_cmd(cmd)
    c_paths = normalize_paths(paths, root)
    for prefix in ("edit ", "write "):
        if n_cmd.startswith(prefix):
            raw_arg = n_cmd[len(prefix):].strip()
            try:
                norm_arg = normalize_paths([raw_arg], root)
                if norm_arg:
                    n_cmd = f"{prefix}{norm_arg[0]}"
            except ValueError:
                pass
    if n_cmd.startswith("edit ") and len(c_paths) == 1 and n_cmd == f"edit {c_paths[0]}":
        return n_cmd
    return f"{n_cmd}|{','.join(c_paths)}"


def classify_attempt(
    command: str,
    paths: list[str],
    historical_actions: list[dict],
    touched_incidents: list[str] | None = None,
    override: bool = False,
    db_available: bool = True,
    repo_root: Path | None = None,
) -> tuple[ActionDecision, str, list[str]]:
    """Operational classifier implementing the 7-case benchmark taxonomy."""
    if not db_available:
        return ActionDecision.FAIL_OPEN, "Database unavailable, safety check bypassed", []

    if override:
        return ActionDecision.WARN, "Manual override provided; execution allowed with audit", []

    try:
        candidate_fp = compute_fp(command, paths, repo_root)
    except ValueError as err:
        return ActionDecision.FAIL_OPEN, str(err), []

    # Check for exact / syntactic match against refuted historical actions
    refuted_evidence_ids = []
    for act in historical_actions:
        if act.get("fingerprint") == candidate_fp:
            claim = act.get("claim", {})
            evidence = act.get("evidence", {})
            # Verify evidence is executed and refuted
            if (
                claim.get("status") == "refuted"
                and evidence.get("executed") is True
                and evidence.get("exit_code") not in (None, 0)
            ):
                refuted_evidence_ids.append(evidence.get("id"))

    if refuted_evidence_ids:
        return (
            ActionDecision.BLOCK,
            f"blocked: refuted by {', '.join(refuted_evidence_ids)}",
            refuted_evidence_ids,
        )

    # Check if touching files involved in an incident (contextual warning)
    if touched_incidents:
        return (
            ActionDecision.WARN,
            f"Files touched in incident {', '.join(touched_incidents)}; verified alternative",
            [],
        )

    return ActionDecision.OK, "Clean action", []


def test_eval_def_file_exists() -> None:
    assert EVAL_DEF_PATH.exists(), f"Missing required file: {EVAL_DEF_PATH}"
    content = EVAL_DEF_PATH.read_text(encoding="utf-8")
    assert len(content) > 500


def test_eval_def_cites_mast_and_fm_1_3() -> None:
    content = EVAL_DEF_PATH.read_text(encoding="utf-8")
    assert "MAST" in content
    assert "FM-1.3" in content
    assert "2503.13657" in content
    assert "step repetition" in content.lower()


def test_eval_def_tide_is_definition_only() -> None:
    content = EVAL_DEF_PATH.read_text(encoding="utf-8")
    assert "TIDE" in content
    assert "2602.02196" in content
    lowered = content.lower()
    assert "loop ratio" in lowered
    # Must explicitly state it is a definition or external metric, not our result
    assert "definition only" in lowered or "external definition" in lowered
    assert "never as a sheldon memory result" in lowered or "never as a memory result" in lowered


def test_eval_def_contains_no_measurement_counts() -> None:
    """TASKS.md locks: 'No count is in the file.'"""
    content = EVAL_DEF_PATH.read_text(encoding="utf-8")
    # Must not contain measurement phrasing
    assert "we measured" not in content.lower()
    assert "our benchmark achieved" not in content.lower()
    assert "pass rate: 0." not in content.lower()
    assert "tokens saved" not in content.lower()

    # Must not have hardcoded evaluation count results
    pattern = re.compile(r"\b\d+\s+(runs|tasks|failures)\s+measured\b", re.IGNORECASE)
    assert not pattern.search(content)


def test_eval_def_contains_seven_taxonomy_cases() -> None:
    content = EVAL_DEF_PATH.read_text(encoding="utf-8")
    for i in range(1, 8):
        assert f"Case {i}" in content


def test_eval_def_paired_eval_formulas() -> None:
    content = EVAL_DEF_PATH.read_text(encoding="utf-8")
    assert "Pass Rate" in content
    assert "Invalid Completion Attempts" in content
    assert "Invalid Completions Prevented" in content
    assert "Refuted-Fix Retries" in content
    assert "Retry Blocks" in content
    assert "Regression Count" in content
    assert "False-Block Rate" in content
    assert "GRAPH.COPY" in content


# ==============================================================================
# Executable Taxonomy Classification Unit Tests
# ==============================================================================

SEED_HISTORICAL_ACTION = {
    "id": "ACT-1",
    "fingerprint": "edit checkout/cache.py",
    "cmd": "edit checkout/cache.py",
    "paths": ["checkout/cache.py"],
    "claim": {
        "id": "C-5",
        "status": "refuted",
        "text": "Raising cache TTL fixes timeout",
    },
    "evidence": {
        "id": "E-41",
        "kind": "ci_run",
        "executed": True,
        "exit_code": 1,
    },
}


def test_case_1_exact_repeat_of_refuted_fix() -> None:
    decision, reason, ev_ids = classify_attempt(
        command="edit checkout/cache.py",
        paths=["checkout/cache.py"],
        historical_actions=[SEED_HISTORICAL_ACTION],
    )
    assert decision == ActionDecision.BLOCK
    assert "E-41" in reason
    assert ev_ids == ["E-41"]


def test_case_2_syntactically_equivalent_fix() -> None:
    decision, reason, ev_ids = classify_attempt(
        command="edit   ./checkout/cache.py",
        paths=["./checkout/cache.py"],
        historical_actions=[SEED_HISTORICAL_ACTION],
    )
    assert decision == ActionDecision.BLOCK
    assert "E-41" in reason
    assert ev_ids == ["E-41"]


def test_case_3_different_fix_on_same_file_is_allowed() -> None:
    decision, reason, ev_ids = classify_attempt(
        command="refactor checkout/cache.py",
        paths=["checkout/cache.py"],
        historical_actions=[SEED_HISTORICAL_ACTION],
        touched_incidents=["INC-12"],
    )
    assert decision == ActionDecision.WARN
    assert "INC-12" in reason
    assert ev_ids == []


def test_case_4_override_allows_with_audit() -> None:
    decision, reason, ev_ids = classify_attempt(
        command="edit checkout/cache.py",
        paths=["checkout/cache.py"],
        historical_actions=[SEED_HISTORICAL_ACTION],
        override=True,
    )
    assert decision == ActionDecision.WARN
    assert "override" in reason.lower()
    assert ev_ids == []


def test_case_5_unexecuted_run_cannot_block_as_refutation() -> None:
    unexecuted_action = {
        "id": "ACT-2",
        "fingerprint": "edit checkout/session.py",
        "claim": {"id": "C-9", "status": "refuted"},
        "evidence": {"id": "E-52", "executed": False},
    }
    decision, _, ev_ids = classify_attempt(
        command="edit checkout/session.py",
        paths=["checkout/session.py"],
        historical_actions=[unexecuted_action],
    )
    # Since evidence was not executed, it cannot validly block
    assert decision != ActionDecision.BLOCK
    assert ev_ids == []


def test_case_6_clean_action_allowed() -> None:
    decision, reason, ev_ids = classify_attempt(
        command="edit checkout/api.py",
        paths=["checkout/api.py"],
        historical_actions=[SEED_HISTORICAL_ACTION],
        touched_incidents=None,
    )
    assert decision == ActionDecision.OK
    assert "clean" in reason.lower()
    assert ev_ids == []


def test_case_7_db_outage_fails_open() -> None:
    decision, reason, _ = classify_attempt(
        command="edit checkout/cache.py",
        paths=["checkout/cache.py"],
        historical_actions=[SEED_HISTORICAL_ACTION],
        db_available=False,
    )
    assert decision == ActionDecision.FAIL_OPEN
    assert "bypassed" in reason.lower()


def test_executed_run_with_exit_code_zero_does_not_block() -> None:
    passing_action = {
        "id": "ACT-PASS",
        "fingerprint": "edit checkout/cache.py",
        "claim": {"id": "C-5", "status": "refuted"},
        "evidence": {
            "id": "E-PASS",
            "kind": "test_run",
            "executed": True,
            "exit_code": 0,
        },
    }
    decision, _, ev_ids = classify_attempt(
        command="edit checkout/cache.py",
        paths=["checkout/cache.py"],
        historical_actions=[passing_action],
    )
    assert decision != ActionDecision.BLOCK
    assert ev_ids == []
