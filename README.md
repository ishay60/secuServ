# secuserv

A command-line self-test for the safety guardrails of **your own, locally-run MCP server**.
It connects to one server, lists its tools, runs five checks, and prints a pass/fail report.

It is a conformance test, not an attack tool: it refuses to connect to anything that is not on
this machine, and it only ever calls tools the server itself marks read-only.

## Eval

The agent is run against deliberately-flawed local servers (`test_servers/`, one planted flaw
each) and a well-behaved control server.

| Server | Planted flaw | Checks failed | Verdict |
|---|---|---|---|
| `good_server.py` (stdio) | none | none | clean |
| `good_server.py` (http, bearer auth) | none | none | clean |
| `leaky_readonly.py` | read-only tool that writes | `read_only` | flagged |
| `no_auth.py` | HTTP with no auth | `auth_required` | flagged |
| `secret_in_output.py` | fake API key in output | `secret_leak` | flagged |

| Score | Result |
|---|---|
| Flaws flagged on broken servers | **3 / 3** |
| False alarms on `good_server.py` | **0 / 10** checks |

This table was produced with the default planner (no model calls). With Anthropic credentials set,
the same eval runs with Claude planning; reproduce either with:

```bash
uv run pytest tests/test_eval.py -s
```

`untrusted_output` and `size_cap` have no flawed server in `test_servers/`; they are covered by
in-process flawed servers in `tests/test_checks.py`.

## Usage

```bash
uv sync
uv run secuserv run --config server.json            # text report
uv run secuserv run --config server.json --json     # JSON report
uv run secuserv run --config server.json --no-llm   # no model calls
```

`server.json` is one of:

```json
{"transport": "stdio", "command": ["python", "my_server.py"]}
```

```json
{"transport": "http", "url": "http://127.0.0.1:8000/mcp", "headers": {"Authorization": "Bearer ..."}}
```

Example output:

```
CHECK             RESULT  EVIDENCE
auth_required     n/a     stdio target has no network auth surface
read_only         PASS    1 read-only tools gave identical output across two rounds
untrusted_output  PASS    no instruction-like text in 1 descriptions and 1 outputs
secret_leak       FAIL    output of 'get_config' contains a sk- API key (sk-FAK…, 35 chars)
size_cap          PASS    largest result was 62 chars from 'get_config' (cap 100,000)

3 passed, 1 failed, 1 not applicable. FAILED: secret_leak.
```

Exit code: `0` no failures, `1` at least one check failed, `2` target refused or config invalid.

## Local-only guard

Enforced in `src/secuserv/target.py` before any connection is opened:

- **stdio** targets are always allowed (a subprocess on this machine).
- **http** targets must have a host that is exactly `localhost`, `127.0.0.1` or `::1`, or that ends
  in `.localhost` or `.test`. Anything else raises `NonLocalTargetError` and nothing is sent.
- URLs with userinfo (`http://localhost@evil.com`), backslashes, or a non-http(s) scheme are refused.

A `Target` object cannot be constructed for a non-local host, and the client only accepts a `Target`.
Redirects that leave the endpoint's origin are not followed. The guard trusts the name: a `.test`
host that your DNS points at a remote machine is not caught.

## Checks

| Check | Passes when | How it looks |
|---|---|---|
| `auth_required` | an HTTP server refuses a request with no credentials | reconnects without the configured headers; n/a for stdio |
| `read_only` | tools marked read-only do not mutate state | calls every read-only tool twice with the same arguments and compares output |
| `untrusted_output` | descriptions and results contain no text addressed to the model as instructions | phrase patterns ("ignore previous instructions", `<system>` tags, ...) |
| `secret_leak` | no keys or tokens appear in descriptions or results | patterns for private keys, AWS/GitHub/Slack tokens, `sk-` keys, `api_key=...` |
| `size_cap` | results stay under 100,000 characters | asks read-only tools for as much as possible via their numeric parameters |

Known limits: the checks are black-box. `read_only` only sees mutation that changes what read-only
tools return, and will false-alarm on a read-only tool whose output is a clock or random.
`untrusted_output` and `secret_leak` are pattern lists, not classifiers. Tools not marked read-only
are never called, so their output is not inspected.

## Agent

`src/secuserv/agent.py` is a four-node LangGraph: discover tools, plan, run checks, summarize.
With `ANTHROPIC_API_KEY` set, Claude (`claude-opus-4-8` by default, `--model` to change) decides
which checks apply and in what order, and writes the summary. Without credentials, or with
`--no-llm`, every check runs in the default order and reports n/a for itself where it does not apply.

Tool names and descriptions come from the server under test, so they are passed to the model as
delimited untrusted data; the plan is schema-constrained to the five check names, and a check the
plan leaves out is run anyway.

## Development

```bash
uv run pytest
```
