from datetime import UTC, datetime, timedelta

import pytest

from app.application.jobs import JobRunner
from app.persistence.database import create_session_factory
from app.persistence.models import Base, JobModel


@pytest.fixture
def session_factory():
    factory = create_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(factory.kw["bind"])
    return factory


def test_enqueue_is_idempotent_for_the_same_active_job(session_factory):
    clock = {"now": datetime(2026, 1, 1, tzinfo=UTC)}
    runner = JobRunner(session_factory, clock=lambda: clock["now"])

    first_id = runner.enqueue("ITEM_RESEARCH", {"item_id": "item-1"})
    second_id = runner.enqueue("ITEM_RESEARCH", {"item_id": "item-1"})

    assert first_id == second_id


def test_expired_lease_is_resumed_and_completes_exactly_once(session_factory):
    clock = {"now": datetime(2026, 1, 1, tzinfo=UTC)}

    def now() -> datetime:
        return clock["now"]

    runner_before_crash = JobRunner(
        session_factory, clock=now, lease_duration=timedelta(minutes=5)
    )
    job_id = runner_before_crash.enqueue("ITEM_RESEARCH", {"item_id": "item-1"})
    leased_first = runner_before_crash.lease_due()
    assert len(leased_first) == 1
    # The worker "crashes" here without completing or failing the job.

    clock["now"] += timedelta(minutes=10)

    runner_after_restart = JobRunner(
        session_factory, clock=now, lease_duration=timedelta(minutes=5)
    )
    leased_second = runner_after_restart.lease_due()
    assert len(leased_second) == 1
    assert leased_second[0].id == job_id

    runner_after_restart.complete(job_id, result_ref="research-result-1")

    with session_factory() as session:
        job = session.get(JobModel, job_id)
        assert job is not None
        assert job.status == "COMPLETED"
        assert job.attempt_count == 2
        assert job.result_ref == "research-result-1"


@pytest.mark.asyncio
async def test_process_due_runs_handler_and_completes_job(session_factory):
    clock = {"now": datetime(2026, 1, 1, tzinfo=UTC)}
    runner = JobRunner(session_factory, clock=lambda: clock["now"])
    job_id = runner.enqueue("ITEM_RESEARCH", {"item_id": "item-1"})

    async def handler(input_data: dict[str, object]) -> str:
        assert input_data == {"item_id": "item-1"}
        return "done"

    await runner.process_due({"ITEM_RESEARCH": handler})

    with session_factory() as session:
        job = session.get(JobModel, job_id)
        assert job is not None
        assert job.status == "COMPLETED"
        assert job.result_ref == "done"


@pytest.mark.asyncio
async def test_process_due_retries_transient_handler_failure(session_factory):
    clock = {"now": datetime(2026, 1, 1, tzinfo=UTC)}
    runner = JobRunner(session_factory, clock=lambda: clock["now"])
    job_id = runner.enqueue("ITEM_RESEARCH", {"item_id": "item-1"})

    async def failing_handler(input_data: dict[str, object]) -> str:
        raise RuntimeError("temporary provider outage")

    await runner.process_due({"ITEM_RESEARCH": failing_handler})

    with session_factory() as session:
        job = session.get(JobModel, job_id)
        assert job is not None
        assert job.status == "PENDING"
        assert job.error_json is not None
        assert "temporary provider outage" in job.error_json
