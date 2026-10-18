"""Banner, help, and the plain-text fallback (docs/plan/cli-spec.md, cli-ux row)."""

import contextlib
import io
import json
import sys

import pytest

from sheldon.cli import main as run_main
from sheldon.output import (
    AMBER,
    BANNER,
    GREEN,
    RED,
    RESET,
    CommandResult,
    colorize,
    emit,
    paint,
    plain,
    spinner,
)


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
    assert err.getvalue() == BANNER + f"\n{RED}blocked{RESET}: refuted by E-41\n"


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


def test_no_args_on_a_tty_opens_the_prompt_and_quits(monkeypatch: pytest.MonkeyPatch) -> None:
    out = Tty()
    monkeypatch.setattr("sys.stdin", Tty("quit\n"))
    monkeypatch.setattr("sys.stdout", out)
    assert run_main([]) == 0
    text = out.getvalue()
    assert text.startswith(BANNER)
    for word in ("preflight", "run", "check", "help"):
        assert f"  {word}" in text
    assert "> " in text


def test_prompt_runs_a_command_and_keeps_going(monkeypatch: pytest.MonkeyPatch) -> None:
    from sheldon import interactive

    calls = []
    monkeypatch.setitem(interactive.COMMANDS, "check", lambda argv: calls.append(argv) or 1)
    out = Tty()
    assert interactive.prompt(Tty("check --graph g 7 abc\nnope\n"), out, out) == 0
    assert calls == [["--graph", "g", "7", "abc"]]
    assert "unknown command: nope" in out.getvalue()


def test_prompt_survives_a_usage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from sheldon import interactive

    def bad(argv: list[str]) -> int:
        raise SystemExit(2)

    monkeypatch.setitem(interactive.COMMANDS, "check", bad)
    out = Tty()
    assert interactive.prompt(Tty("check\nhelp\n"), out, out) == 0
    assert "usage: sheldon run -- <cmd>" in out.getvalue()


def test_colored_status_words_on_a_tty() -> None:
    assert paint("alert", RED) == f"{RED}alert{RESET}"
    text = "blocked: E-52, stale: A-3, passed: test, clear: success, warn: outage"
    colored = colorize(text)
    assert f"{RED}blocked{RESET}" in colored
    assert f"{AMBER}stale{RESET}" in colored
    assert f"{GREEN}passed{RESET}" in colored
    assert f"{GREEN}clear{RESET}" in colored
    assert f"{AMBER}warn{RESET}" in colored


def test_sheldon_run_frame_on_a_tty() -> None:
    ok_res = CommandResult(
        command="run",
        exit_code=0,
        data={"command": "pytest", "id": "E-ok123", "executed": True},
        text="recorded evidence E-ok123 exit 0",
    )
    out = Tty()
    assert emit(ok_res, stdout=out, stderr=Tty()) == 0
    val = out.getvalue()
    assert val.startswith(BANNER)
    assert " running  pytest\n" in val
    assert f" {GREEN}passed{RESET}   evidence E-ok123  exit 0\n" in val

    # Nonzero exit line
    fail_res = CommandResult(
        command="run",
        exit_code=3,
        data={"command": "pytest", "id": "E-fail123", "executed": True},
        text="recorded evidence E-fail123 exit 3",
    )
    out_fail = Tty()
    assert emit(fail_res, stdout=out_fail, stderr=Tty()) == 3
    val_fail = out_fail.getvalue()
    assert " running  pytest\n" in val_fail
    assert " recorded evidence E-fail123  exit 3\n" in val_fail


def test_sheldon_run_frame_off_a_tty() -> None:
    ok_res = CommandResult(
        command="run",
        exit_code=0,
        data={"command": "pytest", "id": "E-ok123", "executed": True},
        text="recorded evidence E-ok123 exit 0",
    )
    out = io.StringIO()
    assert emit(ok_res, stdout=out, stderr=io.StringIO()) == 0
    assert out.getvalue() == "recorded evidence E-ok123 exit 0\n"


def test_preflight_frame_with_incident_on_a_tty() -> None:
    res = CommandResult(
        command="preflight",
        exit_code=2,
        data={"decision": "block", "incident_ids": ["INC-12"]},
        text="blocked: refuted by E-41",
        stream="stderr",
    )
    err = Tty()
    assert emit(res, stdout=Tty(), stderr=err) == 2
    val = err.getvalue()
    assert val.startswith(BANNER)
    assert f"\n {RED}blocked{RESET}  INC-12\n" in val
    assert f"{RED}blocked{RESET}: refuted by E-41\n" in val


def test_preflight_ok_leaves_streams_empty_on_a_tty() -> None:
    res = CommandResult(command="preflight", exit_code=0, data={"decision": "ok"}, text="")
    out = Tty()
    err = Tty()
    assert emit(res, stdout=out, stderr=err) == 0
    assert out.getvalue() == ""
    assert err.getvalue() == ""


def test_spinner_context_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    err_plain = io.StringIO()
    with spinner("running test", stream=err_plain):
        pass
    assert err_plain.getvalue() == ""

    err_tty = Tty()
    monkeypatch.setenv("NO_COLOR", "1")
    with spinner("running test", stream=err_tty):
        pass
    assert err_tty.getvalue() == ""

    # Exception thrown inside with block propagates cleanly without RuntimeError
    monkeypatch.delenv("NO_COLOR", raising=False)
    with pytest.raises(FileNotFoundError), spinner("running test", stream=Tty()):
        raise FileNotFoundError("not found")


def test_sheldon_run_json_does_not_enter_spinner(monkeypatch: pytest.MonkeyPatch) -> None:
    from sheldon import cli, output

    spinner_calls: list[str] = []
    monkeypatch.setattr(cli, "record_run", lambda *a, **kw: None)

    @contextlib.contextmanager
    def record_spinner(status: str, stream=None):
        spinner_calls.append(status)
        yield

    monkeypatch.setattr(output, "spinner", record_spinner)

    out = Tty()
    err = Tty()
    code = run_main(
        ["run", "--json", "--", sys.executable, "-c", "pass"],
        stdout=out,
        stderr=err,
    )
    assert code == 0
    assert spinner_calls == []
    assert err.getvalue() == ""
    out_val = out.getvalue()
    assert "\x1b" not in out_val
    payload = json.loads(out_val)
    assert payload["command"] == "run"
    assert payload["exit_code"] == 0


def test_sheldon_run_piped_stdout_does_not_enter_spinner(monkeypatch: pytest.MonkeyPatch) -> None:
    from sheldon import cli, output

    spinner_calls: list[str] = []
    monkeypatch.setattr(cli, "record_run", lambda *a, **kw: None)

    @contextlib.contextmanager
    def record_spinner(status: str, stream=None):
        spinner_calls.append(status)
        yield

    monkeypatch.setattr(output, "spinner", record_spinner)

    out = io.StringIO()
    err = Tty()
    code = run_main(
        ["run", "--", sys.executable, "-c", "pass"],
        stdout=out,
        stderr=err,
    )
    assert code == 0
    assert spinner_calls == []
    val = out.getvalue()
    assert val.startswith("recorded evidence E-")
    assert val.endswith(" exit 0\n")
