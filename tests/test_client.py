import asyncio

import pytest
from conftest import stdio_command

from secuserv.client import connect, list_tools
from secuserv.target import Target

EXPECTED = {"list_notes": True, "get_note": True, "add_note": False, "read_log": True}  # name -> read-only?


async def tool_summary(target: Target) -> dict[str, bool]:
    async with connect(target) as client:
        tools = await list_tools(client)
        result = await client.call_tool("get_note", {"name": "welcome"})
        assert result.content[0].text == "hello"
    return {t.name: bool(t.annotations and t.annotations.read_only_hint) for t in tools}


def test_stdio_connect_and_list_tools():
    target = Target(transport="stdio", command=stdio_command("good_server.py"))
    assert asyncio.run(tool_summary(target)) == EXPECTED


def test_http_connect_and_list_tools(boot_http):
    url = boot_http("good_server.py")
    target = Target(transport="http", url=url, headers={"Authorization": "Bearer test-token"})
    assert asyncio.run(tool_summary(target)) == EXPECTED


def test_http_without_token_is_refused(boot_http):
    target = Target(transport="http", url=boot_http("good_server.py"))
    with pytest.raises(Exception):
        asyncio.run(tool_summary(target))
