from mcp import Client

from secuserv.checks.base import Context, Result, Status, clip

name = "auth_required"
description = "An HTTP server refuses requests that carry no credentials."


def _leaf(e: BaseException) -> BaseException:
    while isinstance(e, BaseExceptionGroup) and e.exceptions:
        e = e.exceptions[0]
    return e


async def run(ctx: Context) -> Result:
    if ctx.target.transport != "http":
        return Result(name, Status.N_A, "stdio target has no network auth surface")
    # ctx.client already connected with the configured headers, so the server is
    # up: a failure here means the credential-less request itself was refused.
    try:
        async with Client(ctx.target.url) as anonymous:
            tools = (await anonymous.list_tools()).tools
    except Exception as e:
        e = _leaf(e)
        return Result(name, Status.PASS, f"request without credentials refused: {clip(f'{type(e).__name__}: {e}', 120)}")
    return Result(name, Status.FAIL, f"listed {len(tools)} tools with no credentials")
