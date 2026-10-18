"""mem0 arm for the trap suite. Optional: it runs only when mem0 is installed.

Install with ``pip install -r requirements-eval.txt``. mem0 stores the same text
S0 searches (incident titles and claim text) with ``infer=False``, so no LLM
rewrites it, and embeds it with a local HuggingFace model, so no API key is
needed. The LLM entry names a local provider that ``infer=False`` never calls;
without it mem0 builds an OpenAI client and asks for a key.

The block rule is the search-only baseline's: search ``scenario['text']``, then
block when a hit is a refuted claim or an incident whose ``HAS_CAUSE`` claim is
refuted. A vector search always returns its top k, so a hit also needs a cosine
score of at least ``THRESHOLD``. ``LIMIT`` and ``THRESHOLD`` were set before the
first run and are not tuned to the scenarios.
"""

import os
import tempfile
from typing import Any

from eval.traps.arms import REFUTED, _compact_status
from sheldon.db import read

os.environ.setdefault("MEM0_TELEMETRY", "False")

EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"
DIMS = 384
LIMIT = 5
THRESHOLD = 0.5
USER = "trap-suite"


def available() -> bool:
    """True when mem0 and the local embedder's package import."""
    try:
        import mem0  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


class Mem0Arm:
    """Vector recall in mem0 over the seed's stored text. Not given the graph walk."""

    name = "mem0 (infer=False, local embedder)"

    def __init__(self) -> None:
        self._memory = None

    def _load(self, graph: str) -> Any:
        # Every scenario's graph is a copy of the same frozen seed, so the
        # stored text is the same. Store it once; later checks only search.
        if self._memory is not None:
            return self._memory
        from mem0 import Memory

        memory = Memory.from_config(
            {
                "llm": {"provider": "ollama", "config": {"model": "unused-with-infer-false"}},
                "embedder": {
                    "provider": "huggingface",
                    "config": {"model": EMBEDDER, "embedding_dims": DIMS},
                },
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": "trap_suite",
                        "path": tempfile.mkdtemp(prefix="mem0-trap-"),
                        "on_disk": True,
                        "embedding_model_dims": DIMS,
                    },
                },
            }
        )
        for row in read(graph, "trap_memory_rows"):
            memory.add(row["text"], user_id=USER, metadata={"node_id": row["id"]}, infer=False)
        self._memory = memory
        return memory

    def blocks(self, graph: str, scenario: dict[str, Any]) -> bool:
        memory = self._load(graph)
        found = memory.search(
            scenario["text"], filters={"user_id": USER}, limit=LIMIT, threshold=THRESHOLD
        )
        hits = found.get("results", []) if isinstance(found, dict) else found
        ids = [hit["metadata"]["node_id"] for hit in hits]
        rows = read(graph, "trap_hit_status", {"ids": ids}) if ids else []
        blocked = any(
            row.get("claim_status") == REFUTED or row.get("incident_cause_status") == REFUTED
            for row in rows
        )
        scores = [round(hit.get("score", 0.0), 3) for hit in hits]
        self.trace = (
            f"mem0 search limit={LIMIT} threshold={THRESHOLD} hits={ids} scores={scores} "
            f"trap_hit_status={_compact_status(rows)} blocked={blocked}"
        )
        return blocked
