import json

import pytest
from pydantic import ValidationError

from secuserv.target import NonLocalTargetError, Target, assert_local_url, load_target


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/mcp",
        "http://LOCALHOST/mcp",
        "http://127.0.0.1:8000/mcp",
        "http://[::1]:8000/mcp",
        "https://api.localhost/mcp",
        "http://myserver.test:9000/mcp",
    ],
)
def test_local_urls_allowed(url):
    assert_local_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/mcp",
        "https://api.github.com/mcp",
        "http://10.0.0.5:8000/mcp",  # private LAN is still not this machine
        "http://192.168.1.1/mcp",
        "http://0.0.0.0:8000/mcp",
        "http://127.0.0.2/mcp",  # only the exact address is allowed
        "http://127.0.0.1.evil.com/mcp",
        "http://localhost.evil.com/mcp",
        "http://evillocalhost/mcp",  # suffix needs the dot
        "http://eviltest/mcp",
        "http://localhost@evil.com/mcp",  # userinfo trick
        "http://evil.com@localhost/mcp",  # userinfo refused even when host is local
        "http://evil.com\\@localhost/mcp",  # parser-differential trick
        "http://localhost./mcp",
        "ftp://localhost/mcp",
        "file:///etc/passwd",
        "localhost:8000",  # no scheme
        "http:///mcp",  # no host
        "http://[::1/mcp",  # malformed
        "",
    ],
)
def test_non_local_urls_rejected(url):
    with pytest.raises(NonLocalTargetError):
        assert_local_url(url)


def test_stdio_always_allowed():
    t = Target(transport="stdio", command=["python", "server.py"])
    assert t.command == ["python", "server.py"]


def test_target_cannot_be_built_for_non_local_host():
    with pytest.raises(NonLocalTargetError):
        Target(transport="http", url="https://example.com/mcp")


def test_load_target(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps({"transport": "http", "url": "http://127.0.0.1:8000/mcp"}))
    assert load_target(good).url == "http://127.0.0.1:8000/mcp"

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"transport": "http", "url": "http://example.com/mcp"}))
    with pytest.raises(NonLocalTargetError):
        load_target(bad)


def test_incomplete_configs_rejected():
    with pytest.raises(ValidationError):
        Target(transport="stdio")
    with pytest.raises(ValidationError):
        Target(transport="http")
