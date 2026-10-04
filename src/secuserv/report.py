import json

from secuserv.checks.base import Result

LABEL = {"pass": "PASS", "fail": "FAIL", "n_a": "n/a"}


def render_text(results: list[Result], summary: str = "") -> str:
    width = max(len(r.check) for r in results)
    lines = [f"{'CHECK'.ljust(width)}  RESULT  EVIDENCE"]
    lines += [f"{r.check.ljust(width)}  {LABEL[r.status].ljust(6)}  {r.evidence}" for r in results]
    if summary:
        lines += ["", summary]
    return "\n".join(lines)


def render_json(results: list[Result], summary: str = "") -> str:
    rows = [{"check": r.check, "status": str(r.status), "evidence": r.evidence} for r in results]
    return json.dumps({"results": rows, "summary": summary}, indent=2)
