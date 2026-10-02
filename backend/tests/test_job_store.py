import pytest

from app.models.job import JobStatus
from app.services.job_store import JobNotFound, JobStore


def test_create_assigns_unique_ids_and_queued_status():
    store = JobStore()
    a = store.create("https://a.example")
    b = store.create("https://b.example")
    assert a.job_id != b.job_id
    assert a.status is JobStatus.QUEUED
    assert a.step == "Queued..."
    assert a.previews == {}


def test_get_returns_same_object():
    store = JobStore()
    job = store.create("https://a.example")
    assert store.get(job.job_id) is job


def test_get_unknown_raises():
    with pytest.raises(JobNotFound):
        JobStore().get("deadbeef0000")


def test_job_to_response_serialises_fields():
    store = JobStore()
    job = store.create("https://a.example")
    body = job.to_response().model_dump(mode="json")
    assert body["job_id"] == job.job_id
    assert body["url"] == "https://a.example"
    assert body["status"] == "queued"
    assert body["error"] is None
    assert body["previews"] == {}
    assert body["created_at"].endswith("Z") or "+00:00" in body["created_at"]
