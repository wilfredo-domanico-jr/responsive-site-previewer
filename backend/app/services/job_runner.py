"""Runs preview jobs as in-process asyncio tasks.

This is the piece to replace with a real queue/worker later: ``schedule`` is
the only entry point the API uses, and the job state it mutates lives in the
``JobStore``.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

from app.models.job import Job
from app.models.preview import JobStatus, PreviewImage
from app.services.screenshot_service import CaptureFn
from app.utils.errors import PreviewError, playwright_error_to_message

logger = logging.getLogger(__name__)


class JobRunner:
    def __init__(self, capture: CaptureFn, screenshot_dir: Path, max_concurrent: int) -> None:
        self._capture = capture
        self._screenshot_dir = screenshot_dir
        self._semaphore = asyncio.Semaphore(max(1, max_concurrent))
        self._tasks: set[asyncio.Task[None]] = set()

    def schedule(self, job: Job) -> None:
        task = asyncio.create_task(self._run(job), name=f"preview-{job.job_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def shutdown(self) -> None:
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    def job_dir(self, job_id: str) -> Path:
        return self._screenshot_dir / job_id

    async def _run(self, job: Job) -> None:
        out_dir = self.job_dir(job.job_id)

        def on_step(step: str) -> None:
            job.step = step

        def on_preview(key: str, preview: PreviewImage) -> None:
            job.previews[key] = preview

        async with self._semaphore:
            job.status = JobStatus.RUNNING
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                await self._capture(job.url, out_dir, on_step, on_preview)
            except asyncio.CancelledError:
                job.status = JobStatus.FAILED
                job.error = "Preview was cancelled because the server shut down."
                raise
            except Exception as exc:  # noqa: BLE001 - any failure must become a friendly message
                if isinstance(exc, PreviewError):
                    logger.warning("Preview job %s failed for %s: %s", job.job_id, job.url, exc)
                else:
                    logger.exception("Preview job %s failed for %s", job.job_id, job.url)
                job.status = JobStatus.FAILED
                job.error = playwright_error_to_message(exc)
                job.previews.clear()
                shutil.rmtree(out_dir, ignore_errors=True)
            else:
                job.status = JobStatus.COMPLETED
