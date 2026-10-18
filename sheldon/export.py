"""Write the seed graph and the three demo moments as JSON.

``python -m sheldon.export --seed --graph sheldon_export --out web/fixtures``
replaces that graph with the seed, then writes the files the site replays.
``--serve PORT`` is a read-only GET of the same document. It does not write.
"""

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from sheldon.belief.refute import refute_claim
from sheldon.db import connect, read
from sheldon.seed.snapshot import copy_graph, load_seed

SCHEMA = "sheldon.export.v1"
_MOMENTS = {
    "retry_block": "retry-block",
    "evidence_gate": "evidence-gate",
    "stale_cascade": "stale-cascade",
}


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _node_key(labels: list[str], props: dict[str, Any]) -> str:
    if props.get("id"):
        return str(props["id"])
    if props.get("path"):
        return str(props["path"])
    if "number" in props:
        return f"PR-{props['number']}"
    if props.get("name"):
        return str(props["name"])
    return "+".join(labels)


def _node(labels: Any, props: Any) -> dict[str, Any]:
    label_list = [str(label) for label in (labels or [])]
    properties = _plain(dict(props or {}))
    return {
        "key": _node_key(label_list, properties),
        "labels": label_list,
        "properties": properties,
    }


def export_graph(graph: str) -> dict[str, list]:
    """Return nodes and edges for ``graph``. One read, ``queries/export_graph.cypher``."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in read(graph, "export_graph"):
        start = _node(row.get("start_labels"), row.get("start_props"))
        nodes[start["key"]] = start
        if not row.get("rel") or row.get("end_props") is None:
            continue
        end = _node(row.get("end_labels"), row.get("end_props"))
        nodes[end["key"]] = end
        edge = {
            "type": str(row["rel"]),
            "from": start["key"],
            "to": end["key"],
            "properties": _plain(dict(row.get("rel_props") or {})),
        }
        ident = json.dumps(edge, sort_keys=True, default=str)
        if ident not in seen:
            seen.add(ident)
            edges.append(edge)
    return {
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": sorted(edges, key=lambda edge: (edge["type"], edge["from"], edge["to"])),
    }


def _cli(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    return {
        "argv": args,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def record_moments(graph: str) -> dict[str, dict[str, Any]]:
    """Run the three demo commands and keep their real stdout, stderr, and exit codes."""
    retry = _cli(
        [
            "-m",
            "sheldon.preflight",
            "--graph",
            graph,
            "--command",
            "edit checkout/cache.py",
            "--paths",
            "checkout/cache.py",
        ]
    )
    gate = _cli(
        ["-m", "sheldon.check", "--graph", graph, "7", "b2", "--evidence", "E-52"]
    )
    refute_claim(graph, "C-7", ["E-60"], "export", "export", "export")
    cascade = _cli(
        ["-m", "sheldon.check", "--graph", graph, "7", "b2", "--evidence", "E-31"]
    )
    return {"retry_block": retry, "evidence_gate": gate, "stale_cascade": cascade}


def export_document(graph: str) -> dict[str, Any]:
    """Seed snapshot, plus the three moments recorded on a copy so the snapshot stays put."""
    snapshot = export_graph(graph)
    moments_graph = f"{graph}_moments"
    copy_graph(graph, moments_graph)
    try:
        moments = record_moments(moments_graph)
    finally:
        try:
            connect().select_graph(moments_graph).delete()
        except Exception:  # noqa: BLE001 - the copy may already be gone
            pass
    return {
        "schema": SCHEMA,
        "graph": graph,
        "nodes": snapshot["nodes"],
        "edges": snapshot["edges"],
        "moments": moments,
    }


def write_fixtures(document: dict[str, Any], directory: str | Path) -> None:
    """Write ``graph.json`` and one ``.txt`` / ``.json`` pair per demo moment."""
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(
        json.dumps(document, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    for key, stem in _MOMENTS.items():
        moment = document["moments"][key]
        transcript = moment["stderr"] if key == "retry_block" else moment["stdout"]
        (out / f"{stem}.txt").write_text(transcript, encoding="utf-8")
        (out / f"{stem}.json").write_text(
            json.dumps(moment, indent=2) + "\n",
            encoding="utf-8",
        )


def serve_document(document: dict[str, Any], port: int = 8765) -> str:
    """Serve the document on ``127.0.0.1``. GET only. Returns the URL."""
    payload = json.dumps(document, default=str).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib name
            path = self.path.split("?", 1)[0]
            if path not in {"/", "/export.json"}:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self) -> None:  # noqa: N802 - stdlib name
            self.send_error(405)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    host, bound = server.server_address
    return f"http://{host}:{bound}/export.json"


def main(argv: list[str] | None = None) -> int:
    """Load the seed when asked, write fixtures, and optionally serve them."""
    import argparse

    parser = argparse.ArgumentParser(prog="python -m sheldon.export")
    parser.add_argument("--graph", required=True)
    parser.add_argument(
        "--seed",
        action="store_true",
        help="replace --graph with the demo seed, then export that",
    )
    parser.add_argument("--out", help="directory for graph.json and the moment transcripts")
    parser.add_argument("--serve", type=int, metavar="PORT", help="read-only GET port")
    args = parser.parse_args(argv)
    if args.seed:
        try:
            connect().select_graph(args.graph).delete()
        except Exception:  # noqa: BLE001 - the key may not exist yet
            pass
        load_seed(args.graph)
    document = export_document(args.graph)
    if args.out:
        write_fixtures(document, args.out)
    if args.serve is not None:
        url = serve_document(document, args.serve)
        print(url)
        threading.Event().wait()
    elif not args.out:
        print(json.dumps(document, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
