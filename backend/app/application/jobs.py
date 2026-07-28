import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.persistence.database import SessionFactory
from app.persistence.models import JobModel

Clock = Callable[[], datetime]

_ACTIVE_STATUSES = ("PENDING", "LEASED")


def utcnow() -> datetime:
    return datetime.now(UTC)


class JobRunner:
    def __init__(
        self,
        session_factory: SessionFactory,
        clock: Clock = utcnow,
        lease_duration: timedelta = timedelta(minutes=5),
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock
        self._lease_duration = lease_duration

    def enqueue(self, job_type: str, input_data: dict[str, object]) -> str:
        input_json = json.dumps(input_data, sort_keys=True)
        with self._session_factory() as session:
            existing = session.scalar(
                select(JobModel).where(
                    JobModel.job_type == job_type,
                    JobModel.input_json == input_json,
                    JobModel.status.in_(_ACTIVE_STATUSES),
                )
            )
            if existing is not None:
                return existing.id

            job = JobModel(
                job_type=job_type,
                input_json=input_json,
                status="PENDING",
                next_attempt_at=self._clock(),
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job.id

    def lease_due(self, limit: int = 10) -> list[JobModel]:
        now = self._clock()
        leased: list[JobModel] = []
        with self._session_factory() as session:
            candidates = session.scalars(
                select(JobModel).where(JobModel.status.in_(_ACTIVE_STATUSES)).limit(limit)
            ).all()
            for job in candidates:
                pending_due = job.status == "PENDING" and job.next_attempt_at <= now
                lease_expired = (
                    job.status == "LEASED"
                    and job.lease_expires_at is not None
                    and job.lease_expires_at <= now
                )
                if not (pending_due or lease_expired):
                    continue
                job.status = "LEASED"
                job.attempt_count += 1
                job.lease_expires_at = now + self._lease_duration
                session.add(job)
                leased.append(job)
            session.commit()
            for job in leased:
                session.refresh(job)
        return leased

    def complete(self, job_id: str, result_ref: str | None = None) -> None:
        with self._session_factory() as session:
            job = session.get(JobModel, job_id)
            if job is None:
                raise LookupError(f"job not found: {job_id}")
            job.status = "COMPLETED"
            job.result_ref = result_ref
            session.commit()

    def fail(self, job_id: str, error: str, retry_delay: timedelta) -> None:
        with self._session_factory() as session:
            job = session.get(JobModel, job_id)
            if job is None:
                raise LookupError(f"job not found: {job_id}")
            job.status = "PENDING"
            job.error_json = json.dumps({"error": error})
            job.next_attempt_at = self._clock() + retry_delay
            job.lease_expires_at = None
            session.commit()

    async def process_due(
        self, handlers: dict[str, Callable[[dict[str, object]], Awaitable[str | None]]]
    ) -> None:
        for job in self.lease_due():
            handler = handlers.get(job.job_type)
            if handler is None:
                continue
            try:
                result_ref = await handler(json.loads(job.input_json))
            except Exception as error:  # transient failure, retried with backoff
                self.fail(job.id, str(error), timedelta(seconds=30))
            else:
                self.complete(job.id, result_ref)
