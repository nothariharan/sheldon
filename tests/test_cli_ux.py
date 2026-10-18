"""Banner, help, and the plain-text fallback (docs/plan/cli-spec.md, cli-ux row)."""

import io
import json

import pytest

from sheldon.cli import main as run_main
from sheldon.output import BANNER, CommandResult, emit, plain


class Tty(io.StringIO):
    """A stream that reports itself as a terminal."""

    def isatty(self) -> bool:
        return True


BLOCK = CommandResult(
    command="preflight",
    exit_code=2,
    data={"decision": "block"},
    text="blocked: refuted by E-41",
    stream="stderr",
)


@pytest.fixture(autouse=True)
def no_color_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)


def test_plain_unless_tty_and_no_color_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    assert plain(io.StringIO())
    assert not plain(Tty())
    monkeypatch.setenv("NO_COLOR", "1")
    assert plain(Tty())
    # An empty NO_COLOR does not count as set.
    monkeypatch.setenv("NO_COLOR", "")
    assert not plain(Tty())


def test_banner_on_a_tty_before_the_status() -> None:
    err = Tty()
    assert emit(BLOCK, stdout=Tty(), stderr=err) == 2
    assert err.getvalue() == BANNER + "\nblocked: refuted by E-41\n"


def test_no_banner_when_not_a_tty() -> None:
    err = io.StringIO()
    assert emit(BLOCK, stdout=io.StringIO(), stderr=err) == 2
    assert err.getvalue() == "blocked: refuted by E-41\n"


def test_no_banner_when_no_color_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    err = Tty()
    assert emit(BLOCK, stdout=Tty(), stderr=err) == 2
    assert err.getvalue() == "blocked: refuted by E-41\n"


def test_json_never_carries_the_banner() -> None:
    out = Tty()
    assert emit(BLOCK, as_json=True, stdout=out, stderr=Tty()) == 2
    assert json.loads(out.getvalue())["text"] == "blocked: refuted by E-41"


def test_no_banner_when_there_is_no_text() -> None:
    ok = CommandResult(command="preflight", exit_code=0, data={"decision": "ok"})
    err = Tty()
    assert emit(ok, stdout=Tty(), stderr=err) == 0
    assert err.getvalue() == ""


def test_help_lists_run_and_the_module_commands(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as exc:
        run_main(["--help"])
    assert exc.value.code == 0
    text = capsys.readouterr().out
    assert text.startswith("usage: sheldon run -- <cmd>")
    assert BANNER not in text
    for line in (
        "run     run a command and record one executed Evidence node",
        "python -m sheldon.preflight    block a repeated refuted edit (exit 2)",
        "python -m sheldon.check        print the PR check",
        "python -m sheldon.mcp.server   MCP on stdin/stdout",
    ):
        assert line in text


def test_help_has_the_banner_on_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    out = Tty()
    monkeypatch.setattr("sys.stdout", out)
    with pytest.raises(SystemExit):
        run_main(["--help"])
    assert out.getvalue().startswith(BANNER + "\nusage: sheldon run -- <cmd>")


def test_no_args_is_still_a_usage_error_off_a_tty() -> None:
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0
