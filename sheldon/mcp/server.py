"""Tool names the host will call.

Status: to build. It is not a working feature.
Hosted http is roadmap. Do not add an MCP dependency for this stub.
"""

TOOLS = ("preflight", "recall", "claim", "refute", "resume")


def call_tool(name: str, arguments: dict) -> dict:
    """To build. Dispatch to the owning module. Do not reimplement the gate here."""
    del name, arguments
    raise NotImplementedError("to build: sheldon-mcp")
