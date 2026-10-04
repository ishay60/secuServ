"""Check protocol, Result, and the shared probing helpers.

Checks only ever call tools the server itself marks read-only: probing a
mutating tool with made-up arguments could damage the developer's data.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from mcp import Client
from mcp_types import Tool

from secuserv.target import Target


class Status(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    N_A = "n_a"


@dataclass
class Result:
    check: str
    status: Status
    evidence: str


@dataclass
class Context:
    target: Target
    client: Client
    tools: list[Tool]


class Check(Protocol):
    """Each module in secuserv.checks satisfies this: name, description, run()."""

    name: str
    description: str

    async def run(self, ctx: Context) -> Result: ...


def read_only_tools(ctx: Context) -> list[Tool]:
    return [t for t in ctx.tools if t.annotations and t.annotations.read_only_hint]


PROBE = {"string": "secuserv-probe", "integer": 1, "number": 1, "boolean": False, "array": [], "object": {}}
BIG = 1_000_000


def probe_args(tool: Tool, big: bool = False) -> dict:
    """Minimal arguments satisfying the tool's schema. big=True asks for as much as possible."""
    schema = tool.input_schema or {}
    args = {}
    for name, prop in schema.get("properties", {}).items():
        kind = prop.get("type")
        if big and kind in ("integer", "number"):
            args[name] = BIG
        elif name in schema.get("required", []):
            args[name] = PROBE.get(kind, "secuserv-probe")
    return args


async def call_text(client: Client, tool: Tool, args: dict) -> str:
    try:
        result = await client.call_tool(tool.name, args)
    except Exception as e:  # a refused probe is an answer, not a crash
        return f"<error: {e}>"
    return "\n".join(getattr(block, "text", "") for block in result.content)


async def probe_read_only(ctx: Context, big: bool = False) -> dict[str, str]:
    """Call every read-only tool once; tool name -> text output."""
    return {t.name: await call_text(ctx.client, t, probe_args(t, big)) for t in read_only_tools(ctx)}


def clip(text: str, n: int = 80) -> str:
    return text if len(text) <= n else text[:n] + "…"
