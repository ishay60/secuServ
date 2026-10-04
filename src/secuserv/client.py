"""Connect to the target MCP server and list its tools.

Only accepts a Target, which cannot exist for a non-local host (see target.py).
The SDK's HTTP transport never follows a redirect off the endpoint's origin, so
a local server cannot bounce us to a remote one.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp import Client, StdioServerParameters
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp_types import Tool

from secuserv.target import Target


@asynccontextmanager
async def connect(target: Target) -> AsyncIterator[Client]:
    if target.transport == "stdio":
        params = StdioServerParameters(command=target.command[0], args=target.command[1:])
        async with Client(params) as client:
            yield client
    else:
        async with (
            create_mcp_http_client(headers=target.headers) as http,
            Client(streamable_http_client(target.url, http_client=http)) as client,
        ):
            yield client


async def list_tools(client: Client) -> list[Tool]:
    tools, cursor = [], None
    while True:
        page = await client.list_tools(cursor=cursor)
        tools += page.tools
        cursor = page.next_cursor
        if not cursor:
            return tools
