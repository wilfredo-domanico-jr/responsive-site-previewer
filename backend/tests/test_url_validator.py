import pytest

from app.services.url_validator import UrlValidationError, validate_url


def _resolver_to(*ips: str):
    """Fake DNS resolver returning the given IPs for any hostname."""

    def resolve(_hostname: str) -> list[str]:
        return list(ips)

    return resolve


PUBLIC = _resolver_to("93.184.216.34")


def test_accepts_public_https_url():
    assert validate_url("https://example.com", resolve=PUBLIC) == "https://example.com"


def test_accepts_http_scheme():
    assert validate_url("http://example.com/path?q=1", resolve=PUBLIC) == "http://example.com/path?q=1"


def test_prepends_https_when_scheme_missing():
    assert validate_url("example.com", resolve=PUBLIC) == "https://example.com"


def test_strips_surrounding_whitespace():
    assert validate_url("  https://example.com  ", resolve=PUBLIC) == "https://example.com"


def test_rejects_empty_url():
    with pytest.raises(UrlValidationError, match="Please enter a website URL."):
        validate_url("   ", resolve=PUBLIC)


@pytest.mark.parametrize("url", ["ftp://example.com", "file:///etc/passwd", "javascript:alert(1)", "data:text/html,hi"])
def test_rejects_unsupported_schemes(url):
    with pytest.raises(UrlValidationError, match="Only http:// and https:// URLs are supported."):
        validate_url(url, resolve=PUBLIC)


def test_rejects_url_without_hostname():
    with pytest.raises(UrlValidationError, match="That doesn't look like a valid website URL."):
        validate_url("https:///nohost", resolve=PUBLIC)


def test_rejects_userinfo_in_url():
    with pytest.raises(UrlValidationError, match="Credentials in the URL are not supported."):
        validate_url("https://user:pass@example.com", resolve=PUBLIC)


@pytest.mark.parametrize("host", ["localhost", "LOCALHOST", "foo.localhost", "router.local", "db.internal", "metadata.google.internal"])
def test_rejects_internal_hostnames(host):
    with pytest.raises(UrlValidationError, match="Local and internal addresses cannot be previewed."):
        validate_url(f"http://{host}/", resolve=PUBLIC)


@pytest.mark.parametrize(
    "ip",
    ["127.0.0.1", "0.0.0.0", "10.1.2.3", "172.16.0.9", "192.168.1.1", "169.254.169.254", "[::1]", "[fc00::1]", "[fe80::1]"],
)
def test_rejects_private_ip_literals(ip):
    with pytest.raises(UrlValidationError, match="Local and internal addresses cannot be previewed."):
        validate_url(f"http://{ip}:8080/", resolve=PUBLIC)


def test_accepts_public_ip_literal():
    assert validate_url("http://93.184.216.34/", resolve=PUBLIC) == "http://93.184.216.34/"


def test_rejects_hostname_resolving_to_private_ip():
    with pytest.raises(UrlValidationError, match="Local and internal addresses cannot be previewed."):
        validate_url("https://evil.example", resolve=_resolver_to("93.184.216.34", "127.0.0.1"))


def test_dns_failure_is_user_friendly():
    def failing(_hostname: str) -> list[str]:
        raise OSError("getaddrinfo failed")

    with pytest.raises(UrlValidationError, match="We couldn't find that website."):
        validate_url("https://does-not-exist.invalid", resolve=failing)


def test_real_resolver_rejects_localhost_without_fake():
    # No fake resolver: still blocked by the hostname rule before any DNS lookup.
    with pytest.raises(UrlValidationError):
        validate_url("http://localhost:8000")
