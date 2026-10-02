import asyncio
from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.models.job import Job
from app.models.preview import JobResponse, JobStatus, PreviewRequest
from app.services.job_runner import JobRunner
from app.services.job_store import JobNotFound, JobStore
from app.services.url_validator import UrlValidationError, validate_url
from app.utils.ids import is_valid_job_id

router = APIRouter(prefix="/api/preview", tags=["preview"])

DeviceKey = Literal["desktop", "laptop", "tablet", "mobile"]
NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview job not found.")


def _store(request: Request) -> JobStore:
    return request.app.state.job_store


def _runner(request: Request) -> JobRunner:
    return request.app.state.job_runner


def _load_job(request: Request, job_id: str) -> Job:
    if not is_valid_job_id(job_id):
        raise NOT_FOUND
    try:
        return _store(request).get(job_id)
    except JobNotFound:
        raise NOT_FOUND from None


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def create_preview(payload: PreviewRequest, request: Request) -> JobResponse:
    try:
        # DNS resolution happens inside validate_url; keep it off the event loop.
        url = await asyncio.to_thread(validate_url, payload.url)
    except UrlValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job = _store(request).create(url)
    _runner(request).schedule(job)
    return job.to_response()


@router.get("/{job_id}", response_model=JobResponse)
async def get_preview(job_id: str, request: Request) -> JobResponse:
    return _load_job(request, job_id).to_response()


@router.get("/{job_id}/download/{device}")
async def download_preview(job_id: str, device: DeviceKey, request: Request) -> FileResponse:
    job = _load_job(request, job_id)
    preview = job.previews.get(device)
    if job.status is not JobStatus.COMPLETED or preview is None:
        raise NOT_FOUND

    path = _runner(request).job_dir(job_id) / f"{device}.png"
    if not path.is_file():
        raise NOT_FOUND

    host = urlsplit(job.url).hostname or "site"
    filename = f"{host}-{device}-{preview.width}x{preview.height}.png"
    return FileResponse(path, media_type="image/png", filename=filename)
