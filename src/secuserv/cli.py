"""secuserv run --config server.json  ->  pass/fail report. Exit 0 clean, 1 failures, 2 refused."""

import argparse
import asyncio
import sys

from pydantic import ValidationError

from secuserv.agent import DEFAULT_MODEL, run_agent
from secuserv.checks.base import Status
from secuserv.report import render_json, render_text
from secuserv.target import NonLocalTargetError, load_target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secuserv", description="Safety self-test for your own local MCP server.")
    run = parser.add_subparsers(dest="command", required=True).add_parser("run", help="run the checks")
    run.add_argument("--config", required=True, help="target config JSON (stdio command or local http url)")
    run.add_argument("--json", action="store_true", help="print the report as JSON")
    run.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model for planning (default {DEFAULT_MODEL})")
    run.add_argument("--no-llm", action="store_true", help="run every check in the default order, no model calls")
    args = parser.parse_args(argv)

    try:
        target = load_target(args.config)  # the local-only guard runs here, before any connection
    except NonLocalTargetError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError, ValidationError) as e:
        print(f"bad config: {e}", file=sys.stderr)
        return 2

    state = asyncio.run(run_agent(target, model=args.model, llm=False if args.no_llm else None))
    render = render_json if args.json else render_text
    print(render(state["results"], state["summary"]))
    return 1 if any(r.status == Status.FAIL for r in state["results"]) else 0


if __name__ == "__main__":
    sys.exit(main())
