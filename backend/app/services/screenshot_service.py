"""Capture full-page screenshots of a URL at several viewport sizes."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Browser, Playwright, Response
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.config import Settings
from app.models.preview import PreviewImage
from app.services.url_validator import UrlValidationError, check_host
from app.utils.errors import PreviewError

logger = logging.getLogger(__name__)

StepCallback = Callable[[str], None]
PreviewCallback = Callable[[str, PreviewImage], None]
CaptureFn = Callable[[str, Path, StepCallback, PreviewCallback], Awaitable[None]]


@dataclass(frozen=True)
class Device:
    key: str
    label: str
    width: int
    height: int


DEVICES: tuple[Device, ...] = (
    Device("desktop", "Desktop", 1920, 1080),
    Device("laptop", "Laptop", 1440, 900),
    Device("tablet", "Tablet", 768, 1024),
    Device("mobile", "Mobile", 390, 844),
)
DEVICE_KEYS: tuple[str, ...] = tuple(device.key for device in DEVICES)

STEP_OPENING = "Opening website..."
STEP_FINISHING = "Finishing..."


def capture_step(device: Device) -> str:
    return f"Capturing {device.label.lower()}..."


class ScreenshotService:
    """Drives one Chromium browser per job and writes one PNG per device."""

    def __init__(self, playwright: Playwright, settings: Settings) -> None:
        self._playwright = playwright
        self._settings = settings

    async def capture_all(
        self,
        url: str,
        out_dir: Path,
        on_step: StepCallback,
        on_preview: PreviewCallback,
    ) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        on_step(STEP_OPENING)
        browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"],
        )
        try:
            for device in DEVICES:
                on_step(capture_step(device))
                image_path = await self._capture_device(browser, url, out_dir, device)
                on_preview(
                    device.key,
                    PreviewImage(
                        width=device.width,
                        height=device.height,
                        image=f"/screenshots/{out_dir.name}/{image_path.name}",
                    ),
                )
        finally:
            await browser.close()
        on_step(STEP_FINISHING)

    async def _capture_device(self, browser: Browser, url: str, out_dir: Path, device: Device) -> Path:
        settings = self._settings
        context = await browser.new_context(
            viewport={"width": device.width, "height": device.height},
            device_scale_factor=1,
            ignore_https_errors=False,
        )
        try:
            page = await context.new_page()
            response = await page.goto(url, wait_until="load", timeout=settings.navigation_timeout_ms)
            self._check_response(response)

            # Let JS run and network settle; neither is guaranteed, so best effort.
            try:
                await page.wait_for_load_state("networkidle", timeout=settings.network_idle_timeout_ms)
            except PlaywrightTimeoutError:
                logger.info("networkidle not reached for %s at %s; continuing", url, device.key)
            await page.wait_for_timeout(settings.settle_delay_ms)

            image_path = out_dir / f"{device.key}.png"
            await page.screenshot(path=str(image_path), **self._screenshot_bounds(await self._page_height(page), device))
            return image_path
        finally:
            await context.close()

    def _check_response(self, response: Response | None) -> None:
        if response is None:
            raise PreviewError("The website did not return a response.")
        if response.status >= 400:
            raise PreviewError(f"The website responded with HTTP {response.status}.")
        final_host = urlsplit(response.url).hostname
        if final_host:
            try:
                check_host(final_host)
            except UrlValidationError as exc:
                raise PreviewError("The website redirected to a blocked address.") from exc

    @staticmethod
    async def _page_height(page) -> int:
        try:
            height = await page.evaluate("() => document.documentElement.scrollHeight")
            return int(height or 0)
        except Exception:  # noqa: BLE001 - page may have navigated away or thrown
            return 0

    def _screenshot_bounds(self, page_height: int, device: Device) -> dict:
        """Full page unless it exceeds the configured maximum, in which case clip."""
        max_height = self._settings.max_full_page_height
        if page_height > max_height:
            return {"full_page": True, "clip": {"x": 0, "y": 0, "width": device.width, "height": max_height}}
        return {"full_page": True}
