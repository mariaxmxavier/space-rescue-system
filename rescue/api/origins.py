"""Browser origin checks for the local HTTP entrypoint."""

from __future__ import annotations

from collections.abc import Collection
from urllib.parse import urlsplit

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_HTTP_SCHEMES = frozenset({"http", "https"})


def origin_is_allowed(origin: str | None, allowed_origins: Collection[str]) -> bool:
    """Return whether a request Origin may access this local API.

    Requests without an Origin are allowed for local command-line clients. Browser
    requests must use an explicitly configured origin on a loopback host.
    """
    if origin is None:
        return True
    if origin not in allowed_origins:
        return False
    try:
        parsed = urlsplit(origin)
        return (
            parsed.scheme in _HTTP_SCHEMES
            and parsed.hostname in _LOCAL_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.path == ""
            and parsed.query == ""
            and parsed.fragment == ""
        )
    except ValueError:
        return False
