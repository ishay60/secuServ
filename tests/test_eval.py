"""The eval: run the agent against every server in test_servers/ and score it.

    uv run pytest tests/test_eval.py -s     # prints the table

Two numbers: flaws flagged on the broken servers, false alarms on good_server.
Uses Claude for planning when Anthropic credentials are set, else the default plan.
"""

import asyncio

from conftest import stdio_command

from secuserv import agent
from secuserv.agent import Step, has_credentials, run_agent
from secuserv.checks.base import Status
from secuserv.target import Target

TOKEN = {"Authorization": "Bearer test-token"}

# (label, script, transport, headers, the one check that must FAIL or None for the control)
CASES = [
    ("good_server (stdio)", "good_server.py", "stdio", {}, None),
    ("good_server (http)", "good_server.py", "http", TOKEN, None),
    ("leaky_readonly", "leaky_readonly.py", "stdio", {}, "read_only"),
    ("no_auth", "no_auth.py", "http", {}, "auth_required"),
    ("secret_in_output", "secret_in_output.py", "stdio", {}, "secret_leak"),
]


def make_target(script, transport, headers, boot_http) -> Target:
    if transport == "http":
        return Target(transport="http", url=boot_http(script), headers=headers)
    return Target(transport="stdio", command=stdio_command(script))


def test_eval(boot_http):
    rows, flagged, flaws, false_alarms, control_checks = [], 0, 0, 0, 0
    for label, script, transport, headers, flaw in CASES:
        state = asyncio.run(run_agent(make_target(script, transport, headers, boot_http)))
        failed = {r.check for r in state["results"] if r.status == Status.FAIL}
        if flaw:
            flaws += 1
            flagged += flaw in failed
            extra = failed - {flaw}
            verdict = "flagged" if flaw in failed else "MISSED"
        else:
            control_checks += len(state["results"])
            false_alarms += len(failed)
            extra = failed
            verdict = "clean" if not failed else "FALSE ALARM"
        rows.append((label, flaw or "none", ", ".join(sorted(failed)) or "none", verdict, extra))

    planner = f"Claude ({agent.DEFAULT_MODEL})" if has_credentials() else "default plan (no LLM)"
    print(f"\n\nplanner: {planner}\n")
    print(f"{'server':<22}{'planted flaw':<16}{'checks failed':<16}verdict")
    for label, flaw, failed, verdict, _ in rows:
        print(f"{label:<22}{flaw:<16}{failed:<16}{verdict}")
    print(f"\nflaws flagged: {flagged}/{flaws}")
    print(f"false alarms on good_server: {false_alarms}/{control_checks} checks\n")

    assert flagged == flaws
    assert false_alarms == 0
    assert all(not extra for *_, extra in rows), "a broken server failed a check other than its planted flaw"


def test_planner_skip_is_reported_and_forgotten_checks_still_run(monkeypatch):
    """A planner may skip a check with a reason; a check it omits runs anyway."""

    async def fake_plan(model, target, tools):
        return [
            Step(check="size_cap", run=True, reason="first"),
            Step(check="auth_required", run=False, reason="stdio transport"),
        ]

    async def fake_summary(model, results):
        return "summary"

    monkeypatch.setattr(agent, "llm_plan", fake_plan)
    monkeypatch.setattr(agent, "llm_summary", fake_summary)
    target = Target(transport="stdio", command=stdio_command("secret_in_output.py"))
    state = asyncio.run(run_agent(target, llm=True))

    by_name = {r.check: r for r in state["results"]}
    assert [r.check for r in state["results"]][:2] == ["size_cap", "auth_required"]
    assert by_name["auth_required"].status == Status.N_A
    assert "skipped by planner" in by_name["auth_required"].evidence
    assert by_name["secret_leak"].status == Status.FAIL  # omitted from the plan, run anyway
    assert len(by_name) == 5
