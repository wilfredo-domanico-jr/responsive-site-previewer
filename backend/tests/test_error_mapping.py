import pytest

from app.utils.errors import PreviewError, playwright_error_to_message


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Page.goto: net::ERR_NAME_NOT_RESOLVED at https://x", "We couldn't find that website. Check the address and try again."),
        ("net::ERR_CONNECTION_REFUSED", "We couldn't connect to the website."),
        ("net::ERR_CONNECTION_RESET", "We couldn't connect to the website."),
        ("net::ERR_ADDRESS_UNREACHABLE", "We couldn't connect to the website."),
        ("net::ERR_CONNECTION_TIMED_OUT", "The website took too long to respond."),
        ("Timeout 30000ms exceeded.", "The website took too long to respond."),
        ("net::ERR_CERT_AUTHORITY_INVALID", "The website has an SSL/certificate problem, so it couldn't be loaded securely."),
        ("net::ERR_SSL_PROTOCOL_ERROR", "The website has an SSL/certificate problem, so it couldn't be loaded securely."),
        ("net::ERR_TOO_MANY_REDIRECTS", "The website redirected too many times."),
        ("net::ERR_ABORTED", "The website blocked the request."),
        ("Something weird happened", "Something went wrong while capturing the website. Please try again."),
    ],
)
def test_maps_playwright_messages(raw, expected):
    assert playwright_error_to_message(Exception(raw)) == expected


def test_preview_error_message_passes_through_unchanged():
    err = PreviewError("The website responded with HTTP 404.")
    assert playwright_error_to_message(err) == "The website responded with HTTP 404."


def test_timeout_error_type_maps_to_timeout_message():
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    assert playwright_error_to_message(PlaywrightTimeoutError("whatever")) == "The website took too long to respond."
