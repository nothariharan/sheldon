"""Guards that do not need a running engine."""

import inspect
from pathlib import Path

from sheldon import cypher
from sheldon.belief import refute as refute_mod
from sheldon.coordination import board
from sheldon.schema import (
    FALKORDB_IMAGE,
    FALKORDB_MODULE_VERSION,
    TASK_TO_HYPOTHESIS,
    HypothesisStatus,
    investigation_graph,
)

ROOT = Path(__file__).resolve().parents[1]

# Shapes of notes that do not belong in a public tree: a removed filename,
# a writeup about other entries in this event, or a note about what people
# at the sponsor posted. Built so this file is not itself a reference.
REMOVED_NOTES = (
    "check" + ".md",
    "learnings" + ".md",
    "intel" + ".md",
)

COMPETITIVE_SHAPES = (
    "field-scout",
    "field scout",
    "rival repo",
    "rival team",
    "other submission",
    "sponsor-intel",
    "idea-validator",
    "x.com/falkordb",
)

FORBIDDEN_IN_CODE = (
    "only possible on falkordb",
    "nobody else measures",
    "no competitor has graph.copy",
    "reaching the task board is ours",
)


def test_queries_load_as_one_statement() -> None:
    for name in cypher.RUNNABLE:
        text = cypher.load_query(name)
        assert text
        assert ";" not in text
        assert "MULTI" not in text.upper()
        assert "*0.." not in text


def test_vector_index_is_not_runnable_until_the_dimension_is_locked() -> None:
    try:
        cypher.load_query("create_vector_index_event")
    except ValueError as exc:
        assert "not runnable" in str(exc)
    else:
        raise AssertionError("vector index sketch should not load yet")
    raw = (cypher.QUERIES / "create_vector_index_event.cypher").read_text()
    assert "EMBEDDING_DIM" in raw


def test_refute_query_is_the_gate() -> None:
    raw = (cypher.QUERIES / "refute_hypothesis.cypher").read_text()
    text = cypher.load_query("refute_hypothesis")
    assert "DELETE" not in text.upper()
    assert "*1..3" in text
    assert "size(evidence)" in text
    assert "FOREACH" in text
    assert TASK_TO_HYPOTHESIS in raw
    assert "$refuted" in text
    assert "'refuted'" not in text


def test_no_inline_cypher_in_python() -> None:
    for path in (ROOT / "sheldon").rglob("*.py"):
        source = path.read_text()
        assert "MATCH (" not in source
        assert "CREATE (" not in source
        assert "MERGE (" not in source


def test_stub_flags_match_the_function_body() -> None:
    for flag, fn in (
        (board.CLAIM_IS_STUB, board.claim_task),
        (refute_mod.REFUTE_IS_STUB, refute_mod.refute_hypothesis),
    ):
        source = inspect.getsource(fn)
        assert flag is ("NotImplementedError" in source)


def test_image_pin_is_shared_and_exact() -> None:
    assert FALKORDB_IMAGE == "falkordb/falkordb:v4.22.1"
    assert FALKORDB_MODULE_VERSION == 42201
    compose = (ROOT / "docker-compose.yml").read_text()
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    for text in (compose, ci):
        assert FALKORDB_IMAGE in text
        assert ":latest" not in text
        assert ":edge" not in text


def test_pitch_files_do_not_make_forbidden_claims() -> None:
    files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"]
    files += list((ROOT / "sheldon").rglob("*.py"))
    files += list((ROOT / "queries").rglob("*.cypher"))
    blob = "\n".join(path.read_text().lower() for path in files)
    for phrase in FORBIDDEN_IN_CODE:
        assert phrase not in blob


def _tracked_text() -> str:
    blobs = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        if path.suffix not in {".md", ".py", ".cypher", ".yml", ".yaml"}:
            continue
        if path.name == "test_contracts.py":
            continue
        blobs.append(path.read_text().lower())
    return "\n".join(blobs)


def test_removed_notes_and_competitive_shapes_are_absent() -> None:
    for name in REMOVED_NOTES:
        assert list(ROOT.rglob(name)) == []
    blob = _tracked_text()
    for shape in (*REMOVED_NOTES, *COMPETITIVE_SHAPES):
        assert shape not in blob


def test_docs_say_what_wins() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    index = (ROOT / "docs" / "README.md").read_text()
    docs_agents = (ROOT / "docs" / "AGENTS.md").read_text()
    for text in (agents, index, docs_agents):
        assert "REPORT.md" in text
        assert "facts.md" in text
        assert "papers.md" in text
        assert "override" in text
    assert "pains.md" in agents
    assert "opened" in agents
    pains = (ROOT / "docs" / "research" / "pains.md").read_text().lower()
    assert "archive" in pains
    assert "do not copy" in pains


def test_investigation_graph_key() -> None:
    assert investigation_graph("checkout_1") == "inv_checkout_1"
    try:
        investigation_graph("has space")
    except ValueError:
        return
    raise AssertionError("bad investigation id was accepted")


def test_hypothesis_status_is_the_chosen_set() -> None:
    assert [item.value for item in HypothesisStatus] == ["open", "supported", "refuted"]
