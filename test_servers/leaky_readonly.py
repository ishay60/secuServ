"""FLAW: get_note is marked read-only but writes to an access log on every call."""

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

READ_ONLY = ToolAnnotations(read_only_hint=True)

mcp = MCPServer("leaky-readonly")
notes = {"welcome": "hello"}
access_log: list[str] = []


@mcp.tool(annotations=READ_ONLY)
def get_note(name: str) -> str:
    """Return the text of a note."""
    access_log.append(name)  # the flaw: a "read-only" tool mutating state
    return notes.get(name, "")


@mcp.tool(annotations=READ_ONLY)
def get_access_log() -> str:
    """Return the names of notes read so far."""
    return ",".join(access_log)


if __name__ == "__main__":
    mcp.run()
