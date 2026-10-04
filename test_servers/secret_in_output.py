"""FLAW: a tool returns a credential in its output (the key below is fake)."""

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

mcp = MCPServer("secret-in-output")


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def get_config() -> str:
    """Return the service configuration."""
    return "region=local\nupstream_key=sk-FAKE0000000000000000000000000000\n"


if __name__ == "__main__":
    mcp.run()
