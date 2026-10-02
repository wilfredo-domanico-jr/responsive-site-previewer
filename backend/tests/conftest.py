import asyncio
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.models.preview import PreviewImage
from app.services.screenshot_service import DEVICES

# 1x1 transparent PNG
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)

# A public IP literal so URL validation needs no DNS lookup in tests.
PUBLIC_URL = "http://93.184.216.34/"


async def fake_capture(url: str, out_dir: Path, on_step, on_preview) -> None:
    on_step("Opening website...")
    for device in DEVICES:
        on_step(f"Capturing {device.label.lower()}...")
        await asyncio.sleep(0.01)
        (out_dir / f"{device.key}.png").write_bytes(TINY_PNG)
        on_preview(
            device.key,
            PreviewImage(
                width=device.width,
                height=device.height,
                image=f"/screenshots/{out_dir.name}/{device.key}.png",
            ),
        )
    on_step("Finishing...")


async def failing_capture(url: str, out_dir: Path, on_step, on_preview) -> None:
    on_step("Opening website...")
    raise Exception("Page.goto: net::ERR_NAME_NOT_RESOLVED at http://x/")


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(screenshot_dir=tmp_path / "shots", cors_origins="http://localhost:3000")


@pytest.fixture
def client(settings: Settings):
    get_settings.cache_clear()
    app = create_app(settings=settings, capture=fake_capture)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def failing_client(settings: Settings):
    get_settings.cache_clear()
    app = create_app(settings=settings, capture=failing_capture)
    with TestClient(app) as test_client:
        yield test_client


def wait_for_terminal(client: TestClient, job_id: str, timeout: float = 5.0) -> dict:
    """Poll the job endpoint until it is completed or failed."""
    deadline = time.monotonic() + timeout
    body: dict = {}
    while time.monotonic() < deadline:
        body = client.get(f"/api/preview/{job_id}").json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not finish in time: {body}")
