from secuserv.checks import auth_required, read_only, secret_leak, size_cap, untrusted_output
from secuserv.checks.base import Check

ALL: list[Check] = [auth_required, read_only, untrusted_output, secret_leak, size_cap]
BY_NAME: dict[str, Check] = {c.name: c for c in ALL}
