"""Plain-text, colored, and JSON output (docs/plan/cli-spec.md).

Command functions return a ``CommandResult``. ``emit`` is the one place that
writes it. On a terminal with ``NO_COLOR`` unset it prints the banner and colored
status lines per the CLI spec. Otherwise the output is plain text.
"""

import contextlib
import json
import os
import re
import sys
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, TextIO

BANNER = " sheldon\n one graph per repo\n"

# ANSI color codes per docs/plan/cli-spec.md
# blocked: red, passed/clear: green, stale/warn: amber
RED = "\033[31m"
GREEN = "\033[32m"
AMBER = "\033[33m"
RESET = "\033[0m"


def plain(stream: TextIO) -> bool:
    """True when ``stream`` gets plain text: not a TTY, or ``NO_COLOR`` set and not empty."""
    isatty = getattr(stream, "isatty", None)
    return not (isatty and isatty()) or bool(os.environ.get("NO_COLOR"))


def paint(text: str, color: str) -> str:
    """Wrap ``text`` in ``color`` and ``RESET``."""
    return f"{color}{text}{RESET}"


def colorize(text: str) -> str:
    """Color status words per docs/plan/cli-spec.md.

    - blocked: red
    - passed, clear: green
    - stale, warn: amber
    Color is decoration. The status word is still in the text.
    """
    if not text:
        return text

    text = re.sub(r"\bblocked\b", f"{RED}blocked{RESET}", text)
    text = re.sub(r"\bpassed\b", f"{GREEN}passed{RESET}", text)
    text = re.sub(r"\bclear\b", f"{GREEN}clear{RESET}", text)
    text = re.sub(r"\bstale\b", f"{AMBER}stale{RESET}", text)
    text = re.sub(r"\bwarn\b", f"{AMBER}warn{RESET}", text)
    return text


@contextlib.contextmanager
def spinner(status: str, stream: TextIO | None = None) -> Generator[None, None, None]:
    """Display an interactive spinner on a TTY while work is in flight."""
    target = stream if stream is not None else sys.stderr
    if plain(target):
        yield
        return
    try:
        from rich.console import Console

        console = Console(file=target, force_terminal=True, no_color=False)
        status_cm = console.status(status)
    except Exception:  # noqa: BLE001
        yield
        return

    with status_cm:
        yield


@dataclass(frozen=True)
class CommandResult:
    """One command's result. ``data`` is the structured payload. ``text`` is the plain line."""

    command: str
    exit_code: int
    data: dict[str, Any]
    text: str = ""
    stream: str = "stdout"
    # ``envelope`` prints command, exit_code, text, and data.
    # ``payload`` prints ``data`` alone. The check command uses that so its
    # existing ``--json`` document stays the check-run payload.
    json_style: str = "envelope"


def to_json(result: CommandResult) -> str:
    """Serialize ``result`` the way ``--json`` prints it."""
    if result.json_style == "payload":
        body: Any = result.data
    else:
        body = {
            "command": result.command,
            "exit_code": result.exit_code,
            "text": result.text,
            "data": result.data,
        }
    return json.dumps(body, indent=2, default=str)


def render(result: CommandResult, stream: TextIO) -> str:
    """Render result for ``stream``, applying banner and color on a TTY."""
    if plain(stream):
        if not result.text:
            return ""
        return result.text if result.text.endswith("\n") else result.text + "\n"

    # Terminal rendering
    if not result.text:
        return ""

    if result.command == "run" and result.data:
        cmd_str = result.data.get("command", "")
        ev_id = result.data.get("id", "")
        exit_code = result.exit_code
        running_line = f" running  {cmd_str}" if cmd_str else ""
        if exit_code == 0:
            status_line = f" {paint('passed', GREEN)}   evidence {ev_id}  exit 0"
        else:
            status_line = f" recorded evidence {ev_id}  exit {exit_code}"
        lines = [BANNER.rstrip("\n"), ""]
        if running_line:
            lines.append(running_line)
        lines.append(status_line)
        return "\n".join(lines) + "\n"

    if result.command == "preflight" and result.data.get("decision") == "block":
        incidents = result.data.get("incident_ids") or []
        lines = [BANNER.rstrip("\n")]
        if incidents:
            lines.extend(["", f" {paint('blocked', RED)}  {', '.join(incidents)}"])
        else:
            lines.append("")
        colored_text = colorize(result.text)
        lines.append(colored_text)
        return "\n".join(lines) + "\n"

    # Default command rendering on a TTY (check, warn, resume, etc.)
    lines = [BANNER.rstrip("\n"), colorize(result.text)]
    return "\n".join(lines) + "\n"


def emit(
    result: CommandResult,
    *,
    as_json: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Write ``result`` and return its exit code. Plain text is the default."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    if as_json:
        out.write(to_json(result) + "\n")
        return result.exit_code
    target = err if result.stream == "stderr" else out
    output = render(result, target)
    if output:
        target.write(output)
    return result.exit_code
