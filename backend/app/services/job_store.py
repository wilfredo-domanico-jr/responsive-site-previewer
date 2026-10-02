"""In-memory job storage.

Swap this class for a persistent implementation (database, Redis, ...) when
moving to a real background-job system; the API only relies on ``create``
and ``get``.
"""

from app.models.job import Job
from app.utils.ids import new_job_id


class JobNotFound(KeyError):
    pass


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, url: str) -> Job:
        job = Job(job_id=new_job_id(), url=url)
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Job:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise JobNotFound(job_id) from exc
