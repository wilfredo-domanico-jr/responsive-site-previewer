from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.models.preview import JobResponse, JobStatus, PreviewImage

STEP_QUEUED = "Queued..."


@dataclass
class Job:
    """Mutable in-process state of one preview job."""

    job_id: str
    url: str
    status: JobStatus = JobStatus.QUEUED
    step: str = STEP_QUEUED
    error: str | None = None
    previews: dict[str, PreviewImage] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_response(self) -> JobResponse:
        return JobResponse(
            job_id=self.job_id,
            url=self.url,
            status=self.status,
            step=self.step,
            error=self.error,
            previews=dict(self.previews),
            created_at=self.created_at,
        )
