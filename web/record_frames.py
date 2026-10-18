"""Record the frames the site replays that ``sheldon.export`` does not write.

``python web/record_frames.py --out web/fixtures``

``sheldon.export`` records the three summary moments. The landing page also
shows the evidence gate turning green after a real ``sheldon run``, the
``refute_claim`` call itself, and the graph after that refute. This script
records those against the demo seed, on scratch graph keys it deletes after.

Writes:

- ``evidence-gate-run.json``: three commands on one seed whose PR 7 head is
  ``git rev-parse HEAD``: the check citing E-52, ``sheldon run -- <tests>``,
  and the check citing the evidence id that run stored.
- ``refute.json``: ``refute_claim(C-7, [E-60])`` on a seed copy, its return
  value, and the check after it.
- ``graph-after.json``: the ``sheldon.export.v1`` nodes and edges after that
  refute. ``graph.json`` stays the before state.

Each command entry is ``{argv, exit_code, stdout, stderr}``, the same shape as
the export moments. ``argv`` starts after the interpreter or ``sheldon``.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from sheldon.belief.refute import refute_claim
from sheldon.db import connect
from sheldon.export import SCHEMA, export_graph
from sheldon.seed.snapshot import copy_graph, load_seed

ROOT = Path(__file__).resolve().parent.parent
GATE_GRAPH = "sheldon_site_gate"
SEED_GRAPH = "sheldon_site_seed"
AFTER_GRAPH = "sheldon_site_after"
TESTS = [sys.executable, "-m", "pytest", "tests/test_output.py", "-q"]


def _drop(graph: str) -> None:
    try:
        connect().select_graph(graph).delete()
    except Exception:  # noqa: BLE001 - the key may not exist
        pass


def _run(exe: str, args: list[str]) -> dict[str, Any]:
    done = subprocess.run(
        [exe, *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        cwd=ROOT,
    )
    return {
        "argv": args,
        "exit_code": done.returncode,
        "stdout": done.stdout,
        "stderr": done.stderr,
    }


def _check(graph: str, sha: str, evidence: str) -> dict[str, Any]:
    return _run(
        sys.executable,
        ["-m", "sheldon.check", "--graph", graph, "7", sha, "--evidence", evidence],
    )


def record_gate(sha: str) -> dict[str, Any]:
    """The check refuses E-52, a real run records evidence, the check clears."""
    _drop(GATE_GRAPH)
    load_seed(GATE_GRAPH, head_sha=sha)
    try:
        refused = _check(GATE_GRAPH, sha, "E-52")
        sheldon = shutil.which("sheldon", path=str(Path(sys.executable).parent))
        if sheldon is None:
            raise SystemExit("the sheldon console script is not installed in this venv")
        run = _run(
            sheldon,
            [
                "run",
                "--graph",
                GATE_GRAPH,
                "--model",
                "agent-model-b",
                "--session",
                "S-3",
                "--",
                *TESTS,
            ],
        )
        # The child runs with this interpreter; argv keeps the plain name.
        found = re.search(r"recorded evidence (E-[0-9a-f]+)", run["stdout"] + run["stderr"])
        if not found:
            raise SystemExit(f"sheldon run did not print an evidence id: {run}")
        cleared = _check(GATE_GRAPH, sha, found.group(1))
    finally:
        _drop(GATE_GRAPH)
    return {"head_sha": sha, "evidence_id": found.group(1), "frames": [refused, run, cleared]}


def record_refute() -> tuple[dict[str, Any], dict[str, Any]]:
    """W2 on a seed copy. Returns the moment and the after snapshot."""
    _drop(SEED_GRAPH)
    load_seed(SEED_GRAPH)
    copy_graph(SEED_GRAPH, AFTER_GRAPH)
    try:
        ok = refute_claim(AFTER_GRAPH, "C-7", ["E-60"], "ci", "ci", "CI-60")
        after = export_graph(AFTER_GRAPH)
        check = _check(AFTER_GRAPH, "b2", "E-31")
    finally:
        _drop(AFTER_GRAPH)
        _drop(SEED_GRAPH)
    call = 'refute_claim(graph, "C-7", ["E-60"], agent="ci", model="ci", session="CI-60")'
    moment = {"call": call, "returned": ok, "check": check}
    return moment, {"schema": SCHEMA, "graph": AFTER_GRAPH, **after}


def _python_to_plain(frame: dict[str, Any]) -> dict[str, Any]:
    frame["argv"] = [arg if arg != sys.executable else "python" for arg in frame["argv"]]
    return frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python web/record_frames.py")
    parser.add_argument("--out", default=str(ROOT / "web" / "fixtures"))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.strip()
    gate = record_gate(sha)
    gate["frames"] = [_python_to_plain(frame) for frame in gate["frames"]]
    refute, after = record_refute()

    def dump(name: str, data: Any) -> None:
        (out / name).write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")

    dump("evidence-gate-run.json", gate)
    dump("refute.json", refute)
    dump("graph-after.json", after)
    print(f"wrote evidence-gate-run.json, refute.json, graph-after.json to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
