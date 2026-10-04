import re

from secuserv.checks.base import Context, Result, Status, probe_read_only

name = "secret_leak"
description = "No API keys, tokens or private keys appear in tool descriptions or output."

SECRETS = {
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
    "Slack token": r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
    "sk- API key": r"\bsk-[A-Za-z0-9_-]{20,}",
    "credential assignment": r"(?i)\b(api[_-]?key|secret|token|passw(or)?d)\b[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_\-/+]{16,}",
}


async def run(ctx: Context) -> Result:
    if not ctx.tools:
        return Result(name, Status.N_A, "server exposes no tools")
    outputs = await probe_read_only(ctx)
    texts = {f"description of '{t.name}'": t.description or "" for t in ctx.tools}
    texts |= {f"output of '{tool}'": text for tool, text in outputs.items()}
    for where, text in texts.items():
        for kind, pattern in SECRETS.items():
            if m := re.search(pattern, text):
                # never echo the secret itself into a report
                return Result(name, Status.FAIL, f"{where} contains a {kind} ({m.group(0)[:6]}…, {len(m.group(0))} chars)")
    return Result(name, Status.PASS, f"no secrets in {len(ctx.tools)} descriptions and {len(outputs)} outputs")
