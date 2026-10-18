"""Tests for sheldon.preflight.

Validates:
- Canonical path resolution and security rejection of escaping paths.
- Exact and syntactically equivalent action fingerprint matching.
- Live test on seed graph: INC-12 TTL retry returns block with E-41.
- Alternative fix on the same file is permitted with warn (not blocked).
- Clean action on unrelated file returns ok.
- Manual override turns block into warn with audit trail.
- Fail-open policy on database outage / timeout.
- CLI / Claude Code PreToolUse hook adapter exit codes (exit 2 on block, exit 0 on allow).
"""

import io
import json
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

from sheldon.db import connect
from sheldon.preflight import (
    canonicalize_paths,
    compute_action_fingerprint,
    normalize_command,
    preflight,
)
from sheldon.preflight import (
    main as cli_main,
)
from sheldon.seed.snapshot import load_seed

SEED_GRAPH = "test_preflight_seed"


@pytest.fixture(scope="module")
def seed_graph() -> Generator[str, None, None]:
    db = connect()
    g = db.select_graph(SEED_GRAPH)
    try:
        g.delete()
    except Exception:
        pass
    load_seed(SEED_GRAPH)
    yield SEED_GRAPH
    try:
        g.delete()
    except Exception:
        pass


# ==============================================================================
# Path Canonicalization & Fingerprinting Tests
# ==============================================================================


def test_path_canonicalization_relative_and_absolute(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    sub = repo_root / "src" / "pkg"
    sub.mkdir(parents=True)
    f = sub / "mod.py"
    f.touch()

    # Relative path
    rel_res = canonicalize_paths(["./src/pkg/mod.py"], repo_root)
    assert rel_res == ["src/pkg/mod.py"]

    # Absolute path
    abs_res = canonicalize_paths([str(f.resolve())], repo_root)
    assert abs_res == ["src/pkg/mod.py"]

    # Redundant separators and dots
    redundant = canonicalize_paths(["src/../src/pkg/./mod.py"], repo_root)
    assert redundant == ["src/pkg/mod.py"]

    # Idempotent
    assert canonicalize_paths(rel_res, repo_root) == rel_res


def test_path_canonicalization_rejects_escaping_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(ValueError, match="escapes repository root"):
        canonicalize_paths(["../outside.py"], repo_root)

    with pytest.raises(ValueError, match="escapes repository root"):
        canonicalize_paths(["/etc/passwd"], repo_root)


def test_normalize_command_collapses_whitespace() -> None:
    assert normalize_command("   edit    checkout/cache.py   ") == "edit checkout/cache.py"
    assert normalize_command("pytest   tests/checkout  -v") == "pytest tests/checkout -v"


def test_action_fingerprint_syntactic_equivalence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "checkout").mkdir()
    (repo / "checkout" / "cache.py").touch()

    # Seed compatibility: "edit checkout/cache.py"
    fp1 = compute_action_fingerprint("edit checkout/cache.py", ["checkout/cache.py"], repo)
    fp2 = compute_action_fingerprint("edit   ./checkout/cache.py", ["./checkout/cache.py"], repo)
    assert fp1 == "edit checkout/cache.py"
    assert fp2 == "edit checkout/cache.py"
    assert fp1 == fp2

    # Different command on same file produces distinct fingerprint
    fp_alt = compute_action_fingerprint(
        "refactor checkout/cache.py", ["checkout/cache.py"], repo
    )
    assert fp_alt != fp1


# ==============================================================================
# Graph Preflight Decision Tests on Seed
# ==============================================================================


def test_preflight_blocks_inc12_ttl_retry_with_e41(seed_graph: str) -> None:
    """Core TASKS.md requirement: Preflight on the INC-12 TTL retry returns block with E-41."""
    res = preflight(
        seed_graph,
        command="edit checkout/cache.py",
        paths=["checkout/cache.py"],
    )
    assert res["decision"] == "block"
    assert "E-41" in res["evidence_ids"]
    assert "C-5" in res["claim_ids"]
    assert "blocked: refuted by E-41" in res["reason"]
    assert "INC-12" in res["reason"]


def test_preflight_blocks_syntactic_variant_of_ttl_retry(seed_graph: str) -> None:
    res = preflight(
        seed_graph,
        command="edit    ./checkout/cache.py",
        paths=["./checkout/cache.py"],
    )
    assert res["decision"] == "block"
    assert "E-41" in res["evidence_ids"]


def test_preflight_warns_legitimate_alternative_on_same_file(seed_graph: str) -> None:
    """False-positive avoidance: Different fix on the same file is permitted (warn)."""
    res = preflight(
        seed_graph,
        command="refactor checkout/cache.py",
        paths=["checkout/cache.py"],
    )
    assert res["decision"] == "warn"
    assert "INC-12" in res["reason"] or "Files touched in prior incident" in res["reason"]
    assert "alternative" in res["reason"].lower() or "allowed" in res["reason"].lower()


def test_preflight_allows_clean_action_on_unrelated_file(seed_graph: str) -> None:
    res = preflight(
        seed_graph,
        command="edit checkout/api.py",
        paths=["checkout/api.py"],
    )
    assert res["decision"] == "ok"
    assert res["reason"] == "Clean action"
    assert res["evidence_ids"] == []


def test_preflight_manual_override_bypasses_block(seed_graph: str) -> None:
    res = preflight(
        seed_graph,
        command="edit checkout/cache.py",
        paths=["checkout/cache.py"],
        override=True,
    )
    assert res["decision"] == "warn"
    assert "Manual override" in res["reason"]
    assert "E-41" in res["evidence_ids"]


def test_preflight_blocks_on_db_outage(monkeypatch: pytest.MonkeyPatch) -> None:
    """A database outage blocks commit, push, and done. The old test expected warn."""
    monkeypatch.delenv("SHELDON_FAIL_OPEN", raising=False)

    class FailingDB:
        def select_graph(self, name: str) -> None:
            raise ConnectionError("Connection refused: FalkorDB is down")

    res = preflight(
        "any_graph",
        command="git commit",
        paths=["checkout/cache.py"],
        db=FailingDB(),  # type: ignore[arg-type]
    )
    assert res["decision"] == "block"
    assert "Database unavailable" in res["reason"]
    assert "blocked" in res["reason"]


def test_preflight_fail_open_escape_hatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHELDON_FAIL_OPEN", "1")

    class FailingDB:
        def select_graph(self, name: str) -> None:
            raise ConnectionError("Connection refused: FalkorDB is down")

    res = preflight(
        "any_graph",
        command="git push",
        paths=["checkout/cache.py"],
        db=FailingDB(),  # type: ignore[arg-type]
    )
    assert res["decision"] == "warn"
    assert "Database unavailable" in res["reason"]


# ==============================================================================
# Claude Code PreToolUse Hook CLI Adapter Tests
# ==============================================================================


def test_cli_hook_exits_2_on_block(
    seed_graph: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = json.dumps(
        {
            "graph": seed_graph,
            "tool_name": "Edit",
            "tool_input": {"file_path": "checkout/cache.py"},
        }
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    monkeypatch.setattr(sys, "argv", ["sheldon.preflight", "--stdin"])

    stderr_buf = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr_buf)

    code = cli_main()
    assert code == 2
    assert "blocked: refuted by E-41" in stderr_buf.getvalue()


def test_cli_hook_exits_0_on_clean_action(
    seed_graph: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = json.dumps(
        {
            "graph": seed_graph,
            "tool_name": "Edit",
            "tool_input": {"file_path": "checkout/api.py"},
        }
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    monkeypatch.setattr(sys, "argv", ["sheldon.preflight", "--stdin"])

    code = cli_main()
    assert code == 0


def test_cli_hook_exits_0_on_alternative_fix_warning(
    seed_graph: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = json.dumps(
        {
            "graph": seed_graph,
            "command": "refactor checkout/cache.py",
            "paths": ["checkout/cache.py"],
        }
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    monkeypatch.setattr(sys, "argv", ["sheldon.preflight", "--stdin"])

    stderr_buf = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr_buf)

    code = cli_main()
    assert code == 0
    val = stderr_buf.getvalue().lower()
    assert "alternative" in val or "files touched" in val
