import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

SERVERS = Path(__file__).parent.parent / "test_servers"


def stdio_command(script: str) -> list[str]:
    return [sys.executable, str(SERVERS / script)]


@pytest.fixture
def boot_http():
    """boot_http("good_server.py") -> "http://127.0.0.1:<port>/mcp", server killed at teardown."""
    procs = []

    def boot(script: str) -> str:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        proc = subprocess.Popen([*stdio_command(script), "--http", str(port)])
        procs.append(proc)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            assert proc.poll() is None, f"{script} exited early"
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                return f"http://127.0.0.1:{port}/mcp"
            except OSError:
                time.sleep(0.05)
        raise TimeoutError(f"{script} did not start listening")

    yield boot
    for proc in procs:
        proc.terminate()
        proc.wait(timeout=5)
