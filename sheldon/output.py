"""Plain-text and JSON output.

Banner, color, and spinners stay out of this module. Command functions return
a ``CommandResult``. ``emit`` is the one place that writes it.
"""

import json
import sys
from dataclasses import dataclass
from typing import Any, TextIO


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
    if result.text:
        target = err if result.stream == "stderr" else out
        target.write(result.text if result.text.endswith("\n") else result.text + "\n")
    return result.exit_code
