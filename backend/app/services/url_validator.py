"""Validation of user-submitted URLs.

The checks here are the first layer of SSRF protection. They are deliberately
kept in one place so they can be tightened later, for example by:

* re-validating every redirect target (the screenshot service already re-checks
  the final URL after navigation),
* filtering sub-resource requests via ``page.route`` with the same ``check_host``,
* adding an allow-list of domains.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit, urlunsplit

from app.config import get_settings

Resolver = Callable[[str], list[str]]

ALLOWED_SCHEMES = frozenset({"http", "https"})
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal")
ALWAYS_BLOCKED_HOSTNAMES = frozenset({"localhost"})
SCHEME_ONLY_PREFIXES = frozenset({"javascript", "data", "mailto", "file", "about", "blob", "vbscript", "ftp"})

MSG_EMPTY = "Please enter a website URL."
MSG_SCHEME = "Only http:// and https:// URLs are supported."
MSG_INVALID = "That doesn't look like a valid website URL."
MSG_USERINFO = "Credentials in the URL are not supported."
MSG_INTERNAL = "Local and internal addresses cannot be previewed."
MSG_DNS = "We couldn't find that website. Check the address and try again."


class UrlValidationError(ValueError):
    """Raised with a user-friendly message when a URL must be rejected."""


def default_resolver(hostname: str) -> list[str]:
    """Resolve ``hostname`` to all of its IP addresses (A and AAAA)."""
    infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    return [str(info[4][0]) for info in infos]


def is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True for loopback, private, link-local, multicast, reserved or unspecified addresses."""
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _parse_ip(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return None


def _is_blocked_hostname(hostname: str) -> bool:
    name = hostname.lower().rstrip(".")
    if name in ALWAYS_BLOCKED_HOSTNAMES or name in get_settings().blocked_hostname_set:
        return True
    return name.endswith(BLOCKED_SUFFIXES)


def check_host(hostname: str, resolve: Resolver = default_resolver) -> None:
    """Reject hostnames or IPs that point at local/internal networks.

    Raises ``UrlValidationError``. Reused for the final URL after redirects.
    """
    if _is_blocked_hostname(hostname):
        raise UrlValidationError(MSG_INTERNAL)

    literal = _parse_ip(hostname)
    if literal is not None:
        if is_blocked_ip(literal):
            raise UrlValidationError(MSG_INTERNAL)
        return

    try:
        addresses = resolve(hostname)
    except (OSError, UnicodeError) as exc:
        raise UrlValidationError(MSG_DNS) from exc
    if not addresses:
        raise UrlValidationError(MSG_DNS)

    for address in addresses:
        ip = _parse_ip(address)
        if ip is None or is_blocked_ip(ip):
            raise UrlValidationError(MSG_INTERNAL)


def validate_url(raw_url: str, resolve: Resolver = default_resolver) -> str:
    """Validate and normalise a user-submitted URL.

    Returns the URL to navigate to, or raises ``UrlValidationError`` with a
    message that is safe to show to the user.
    """
    url = raw_url.strip()
    if not url:
        raise UrlValidationError(MSG_EMPTY)

    if "://" not in url:
        # "javascript:alert(1)", "data:..." etc. have a scheme but no authority.
        if url.split(":", 1)[0].lower() in SCHEME_ONLY_PREFIXES:
            raise UrlValidationError(MSG_SCHEME)
        url = f"https://{url}"  # convenience: "example.com" -> "https://example.com"

    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise UrlValidationError(MSG_INVALID) from exc

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UrlValidationError(MSG_SCHEME)
    if not parts.hostname:
        raise UrlValidationError(MSG_INVALID)
    if parts.username is not None or parts.password is not None:
        raise UrlValidationError(MSG_USERINFO)

    check_host(parts.hostname, resolve)

    return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path, parts.query, parts.fragment))
