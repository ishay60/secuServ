"""Well-behaved notes server: every check should pass (false-alarm control).

    python good_server.py              # stdio
    python good_server.py --http PORT  # streamable HTTP on 127.0.0.1, bearer auth
"""

import sys

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

TOKEN = "test-token"  # fake credential for the local test harness only
READ_ONLY = ToolAnnotations(read_only_hint=True)

mcp = MCPServer("good-server")
notes = {"welcome": "hello"}


@mcp.tool(annotations=READ_ONLY)
def list_notes() -> list[str]:
    """List note names."""
    return sorted(notes)


@mcp.tool(annotations=READ_ONLY)
def get_note(name: str) -> str:
    """Return the text of a note."""
    return notes.get(name, "")


@mcp.tool()
def add_note(name: str, text: str) -> str:
    """Create or replace a note."""
    notes[name] = text
    return "ok"


@mcp.tool(annotations=READ_ONLY)
def read_log(lines: int = 10) -> str:
    """Return the last lines of the server log, at most 100."""
    return "\n".join(f"log line {i}" for i in range(min(lines, 100)))


def require_bearer(app, token):
    async def guarded(scope, receive, send):
        if scope["type"] == "http":
            if dict(scope["headers"]).get(b"authorization") != f"Bearer {token}".encode():
                await send({"type": "http.response.start", "status": 401, "headers": []})
                await send({"type": "http.response.body", "body": b"unauthorized"})
                return
        await app(scope, receive, send)

    return guarded


if __name__ == "__main__":
    if sys.argv[1:2] == ["--http"]:
        import uvicorn

        app = require_bearer(mcp.streamable_http_app(), TOKEN)
        uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[2]), log_level="warning")
    else:
        mcp.run()
