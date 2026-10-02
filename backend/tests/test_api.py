import re

from tests.conftest import PUBLIC_URL, wait_for_terminal


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_preview_returns_job_immediately(client):
    response = client.post("/api/preview", json={"url": PUBLIC_URL})
    assert response.status_code == 202
    body = response.json()
    assert re.fullmatch(r"[0-9a-f]{12}", body["job_id"])
    assert body["url"] == PUBLIC_URL
    assert body["status"] in ("queued", "running")
    assert body["error"] is None
    assert body["previews"] == {}


def test_job_completes_with_four_previews(client, settings):
    job_id = client.post("/api/preview", json={"url": PUBLIC_URL}).json()["job_id"]
    body = wait_for_terminal(client, job_id)

    assert body["status"] == "completed"
    assert body["step"] == "Finishing..."
    assert body["previews"] == {
        "desktop": {"width": 1920, "height": 1080, "image": f"/screenshots/{job_id}/desktop.png"},
        "laptop": {"width": 1440, "height": 900, "image": f"/screenshots/{job_id}/laptop.png"},
        "tablet": {"width": 768, "height": 1024, "image": f"/screenshots/{job_id}/tablet.png"},
        "mobile": {"width": 390, "height": 844, "image": f"/screenshots/{job_id}/mobile.png"},
    }
    for key in ("desktop", "laptop", "tablet", "mobile"):
        assert (settings.screenshot_dir / job_id / f"{key}.png").is_file()


def test_screenshots_are_served_statically(client):
    job_id = client.post("/api/preview", json={"url": PUBLIC_URL}).json()["job_id"]
    wait_for_terminal(client, job_id)

    response = client.get(f"/screenshots/{job_id}/mobile.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_download_endpoint_sends_attachment(client):
    job_id = client.post("/api/preview", json={"url": PUBLIC_URL}).json()["job_id"]
    wait_for_terminal(client, job_id)

    response = client.get(f"/api/preview/{job_id}/download/tablet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"] == 'attachment; filename="93.184.216.34-tablet-768x1024.png"'
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_download_unknown_device_is_rejected(client):
    job_id = client.post("/api/preview", json={"url": PUBLIC_URL}).json()["job_id"]
    wait_for_terminal(client, job_id)
    assert client.get(f"/api/preview/{job_id}/download/watch").status_code == 422


def test_download_unknown_job_is_404(client):
    response = client.get("/api/preview/000000000000/download/desktop")
    assert response.status_code == 404
    assert response.json() == {"detail": "Preview job not found."}


def test_invalid_url_returns_400_with_friendly_message(client):
    response = client.post("/api/preview", json={"url": "ftp://example.com"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Only http:// and https:// URLs are supported."}


def test_empty_url_returns_400(client):
    response = client.post("/api/preview", json={"url": "   "})
    assert response.status_code == 400
    assert response.json() == {"detail": "Please enter a website URL."}


def test_internal_url_returns_400(client):
    response = client.post("/api/preview", json={"url": "http://127.0.0.1:8000/admin"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Local and internal addresses cannot be previewed."}


def test_missing_url_field_returns_422(client):
    assert client.post("/api/preview", json={}).status_code == 422


def test_unknown_job_returns_404(client):
    response = client.get("/api/preview/000000000000")
    assert response.status_code == 404
    assert response.json() == {"detail": "Preview job not found."}


def test_malformed_job_id_returns_404(client):
    assert client.get("/api/preview/..%2F..%2Fetc").status_code == 404
    assert client.get("/api/preview/not-a-job-id").status_code == 404


def test_capture_failure_marks_job_failed_and_server_survives(failing_client):
    job_id = failing_client.post("/api/preview", json={"url": PUBLIC_URL}).json()["job_id"]
    body = wait_for_terminal(failing_client, job_id)

    assert body["status"] == "failed"
    assert body["error"] == "We couldn't find that website. Check the address and try again."
    assert "Traceback" not in str(body)
    assert body["previews"] == {}
    assert failing_client.get("/api/health").status_code == 200


def test_download_for_failed_job_is_404(failing_client):
    job_id = failing_client.post("/api/preview", json={"url": PUBLIC_URL}).json()["job_id"]
    wait_for_terminal(failing_client, job_id)
    assert failing_client.get(f"/api/preview/{job_id}/download/desktop").status_code == 404


def test_cors_allows_configured_origin(client):
    response = client.options(
        "/api/preview",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
