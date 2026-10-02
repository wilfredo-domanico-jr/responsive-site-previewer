"""Translate low-level failures into messages that are safe to show to users."""

from __future__ import annotations

from playwright.async_api import TimeoutError as PlaywrightTimeoutError


class PreviewError(Exception):
    """A failure whose message is already user-friendly."""


MSG_DNS = "We couldn't find that website. Check the address and try again."
MSG_CONNECT = "We couldn't connect to the website."
MSG_TIMEOUT = "The website took too long to respond."
MSG_SSL = "The website has an SSL/certificate problem, so it couldn't be loaded securely."
MSG_REDIRECTS = "The website redirected too many times."
MSG_BLOCKED = "The website blocked the request."
MSG_GENERIC = "Something went wrong while capturing the website. Please try again."

# Ordered: first matching substring wins.
_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("ERR_NAME_NOT_RESOLVED",), MSG_DNS),
    (("ERR_CONNECTION_TIMED_OUT", "Timeout"), MSG_TIMEOUT),
    (
        (
            "ERR_CONNECTION_REFUSED",
            "ERR_CONNECTION_RESET",
            "ERR_CONNECTION_CLOSED",
            "ERR_CONNECTION_FAILED",
            "ERR_ADDRESS_UNREACHABLE",
            "ERR_NETWORK_CHANGED",
            "ERR_INTERNET_DISCONNECTED",
        ),
        MSG_CONNECT,
    ),
    (("ERR_CERT_", "ERR_SSL_", "SSL"), MSG_SSL),
    (("ERR_TOO_MANY_REDIRECTS",), MSG_REDIRECTS),
    (("ERR_BLOCKED_BY_CLIENT", "ERR_ABORTED", "ERR_BLOCKED_BY_RESPONSE"), MSG_BLOCKED),
)


def playwright_error_to_message(exc: BaseException) -> str:
    """Return a user-facing message for any exception raised during capture."""
    if isinstance(exc, PreviewError):
        return str(exc)
    if isinstance(exc, PlaywrightTimeoutError):
        return MSG_TIMEOUT

    text = str(exc)
    for needles, message in _PATTERNS:
        if any(needle in text for needle in needles):
            return message
    return MSG_GENERIC
