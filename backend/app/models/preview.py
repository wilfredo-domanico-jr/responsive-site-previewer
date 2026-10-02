from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PreviewRequest(BaseModel):
    url: str = Field(..., description="Publicly reachable http(s) URL to capture.")


class PreviewImage(BaseModel):
    width: int
    height: int
    image: str = Field(..., description="Path to the PNG, relative to the API host, e.g. /screenshots/<job>/desktop.png")


class JobResponse(BaseModel):
    job_id: str
    url: str
    status: JobStatus
    step: str
    error: str | None = None
    previews: dict[str, PreviewImage]
    created_at: datetime
