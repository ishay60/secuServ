import re

from secuserv.checks.base import Context, Result, Status, clip, probe_read_only

name = "untrusted_output"
description = "Tool descriptions and results are plain data, with no text addressed to the model as instructions."

# ponytail: phrase list, not a classifier. Catches the blunt cases; an LLM judge
# is the upgrade if these prove too easy to dodge.
INSTRUCTION = re.compile(
    r"ignore (all |any )?(previous|prior|above|earlier) (instructions|messages)"
    r"|disregard [^.\n]{0,40}(instructions|system prompt)"
    r"|</?(system|assistant|instructions?)>"
    r"|\[/?INST\]"
    r"|^\s*(system|assistant)\s*:"
    r"|you (must|should) now\b"
    r"|do not (tell|inform|reveal [^.\n]{0,20} to) the user",
    re.IGNORECASE | re.MULTILINE,
)


async def run(ctx: Context) -> Result:
    if not ctx.tools:
        return Result(name, Status.N_A, "server exposes no tools")
    outputs = await probe_read_only(ctx)
    texts = {f"description of '{t.name}'": t.description or "" for t in ctx.tools}
    texts |= {f"output of '{tool}'": text for tool, text in outputs.items()}
    for where, text in texts.items():
        if m := INSTRUCTION.search(text):
            return Result(name, Status.FAIL, f"{where} contains instruction-like text: {clip(m.group(0).strip())!r}")
    return Result(name, Status.PASS, f"no instruction-like text in {len(ctx.tools)} descriptions and {len(outputs)} outputs")
