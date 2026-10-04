"""Target config and the local-only guard.

A Target cannot be constructed for a non-local host: the guard runs as a model
validator, so every code path that holds a Target has already passed it.
"""

import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, model_validator

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
LOCAL_SUFFIXES = (".localhost", ".test")


class NonLocalTargetError(Exception):
    """The target is not on this machine. Nothing was sent."""


def assert_local_url(url: str) -> None:
    """Raise NonLocalTargetError unless url points at this machine. No network I/O."""
    # Backslashes and userinfo are where URL parsers disagree about the host
    # (http://localhost@evil.com, http://evil.com\@localhost), so refuse both outright.
    if "\\" in url:
        raise NonLocalTargetError(f"backslash in URL: {url!r}")
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError as e:
        raise NonLocalTargetError(f"unparseable URL {url!r}: {e}") from e
    if parts.scheme not in ("http", "https"):
        raise NonLocalTargetError(f"scheme must be http or https: {url!r}")
    if parts.username is not None or parts.password is not None:
        raise NonLocalTargetError(f"userinfo not allowed in URL: {url!r}")
    if not host or not (host in LOCAL_HOSTS or host.endswith(LOCAL_SUFFIXES)):
        raise NonLocalTargetError(
            f"host {host!r} is not local; secuserv only runs against localhost, "
            "127.0.0.1, ::1, *.localhost or *.test"
        )


class Target(BaseModel):
    transport: Literal["stdio", "http"]
    command: list[str] | None = None  # stdio: argv of the server subprocess
    url: str | None = None  # http: server endpoint
    headers: dict[str, str] = {}  # http: auth headers etc.

    @model_validator(mode="after")
    def _guard(self):
        if self.transport == "stdio":
            if not self.command:
                raise ValueError("stdio target needs a non-empty 'command'")
        else:
            if not self.url:
                raise ValueError("http target needs a 'url'")
            assert_local_url(self.url)
        return self


def load_target(path: str | Path) -> Target:
    return Target.model_validate(json.loads(Path(path).read_text()))
