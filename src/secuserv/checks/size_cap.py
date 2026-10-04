from secuserv.checks.base import Context, Result, Status, probe_read_only

name = "size_cap"
description = "Tool results stay under a size cap even when asked for as much as possible."

MAX_CHARS = 100_000  # roughly 25k tokens, about what one result can cost a model's context


async def run(ctx: Context) -> Result:
    outputs = await probe_read_only(ctx, big=True)
    if not outputs:
        return Result(name, Status.N_A, "no read-only tools to probe safely")
    tool, text = max(outputs.items(), key=lambda kv: len(kv[1]))
    if len(text) > MAX_CHARS:
        return Result(name, Status.FAIL, f"'{tool}' returned {len(text):,} chars (cap {MAX_CHARS:,})")
    return Result(name, Status.PASS, f"largest result was {len(text):,} chars from '{tool}' (cap {MAX_CHARS:,})")
