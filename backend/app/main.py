import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import health, preview
from app.config import Settings, get_settings
from app.services.job_runner import JobRunner
from app.services.job_store import JobStore
from app.services.screenshot_service import CaptureFn, ScreenshotService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, capture: CaptureFn | None = None) -> FastAPI:
    """Build the FastAPI application.

    ``capture`` lets tests inject a fake screenshot function; when omitted the
    real Playwright-backed ``ScreenshotService`` is started in the lifespan.
    """
    settings = settings or get_settings()
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        playwright = None
        capture_fn = capture
        if capture_fn is None:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            capture_fn = ScreenshotService(playwright, settings).capture_all

        app.state.job_store = JobStore()
        app.state.job_runner = JobRunner(
            capture=capture_fn,
            screenshot_dir=settings.screenshot_dir,
            max_concurrent=settings.max_concurrent_jobs,
        )
        try:
            yield
        finally:
            await app.state.job_runner.shutdown()
            if playwright is not None:
                await playwright.stop()

    app = FastAPI(title="Responsive Site Previewer API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.include_router(health.router)
    app.include_router(preview.router)
    app.mount("/screenshots", StaticFiles(directory=settings.screenshot_dir), name="screenshots")
    return app


app = create_app()
