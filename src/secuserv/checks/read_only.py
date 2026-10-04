from secuserv.checks.base import Context, Result, Status, clip, probe_read_only

name = "read_only"
description = "Tools marked read-only do not mutate server state."


async def run(ctx: Context) -> Result:
    # ponytail: black-box, so mutation is only seen if it changes what read-only
    # tools return on an identical second round. Misses writes that are invisible
    # or idempotent after the first call; false-alarms on clocks/random output.
    # Upgrade path: a server-side state-hash hook.
    first = await probe_read_only(ctx)
    if not first:
        return Result(name, Status.N_A, "no tools are marked read-only")
    second = await probe_read_only(ctx)
    for tool, before in first.items():
        if second[tool] != before:
            return Result(
                name,
                Status.FAIL,
                f"calling only read-only tools changed the output of '{tool}': "
                f"{clip(before)!r} -> {clip(second[tool])!r}",
            )
    return Result(name, Status.PASS, f"{len(first)} read-only tools gave identical output across two rounds")
