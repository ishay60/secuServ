"""FLAW: served over HTTP with no authentication at all.

    python no_auth.py --http PORT
"""

import sys

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

mcp = MCPServer("no-auth")


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def get_note(name: str) -> str:
    """Return the text of a note."""
    return {"welcome": "hello"}.get(name, "")


if __name__ == "__main__":
    mcp.run("streamable-http", host="127.0.0.1", port=int(sys.argv[2]))
