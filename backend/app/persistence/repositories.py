from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.persistence.database import SessionFactory
from app.persistence.models import (
    ActivityEventModel,
    ApprovalModel,
    CheckpointModel,
    DraftVersionModel,
    ItemModel,
    OperationModel,
)


class OperationRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def begin(self, operation_key: str) -> OperationModel:
        with self._session_factory() as session:
            operation = OperationModel(operation_key=operation_key, status="PENDING")
            session.add(operation)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                existing = session.scalar(
                    select(OperationModel).where(OperationModel.operation_key == operation_key)
                )
                if existing is None:
                    raise
                return existing
            session.refresh(operation)
            return operation

    def get_by_key(self, operation_key: str) -> OperationModel | None:
        with self._session_factory() as session:
            return session.scalar(
                select(OperationModel).where(OperationModel.operation_key == operation_key)
            )

    def complete(self, operation_id: str, result_json: str) -> None:
        with self._session_factory() as session:
            operation = session.get(OperationModel, operation_id)
            if operation is None:
                raise LookupError(f"operation not found: {operation_id}")
            operation.status = "COMPLETED"
            operation.result_json = result_json
            session.commit()


class ItemRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def add(self, item: ItemModel) -> ItemModel:
        with self._session_factory() as session:
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    def get(self, item_id: str) -> ItemModel | None:
        with self._session_factory() as session:
            return session.get(ItemModel, item_id)


class DraftRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def add_version(self, draft_version: DraftVersionModel) -> DraftVersionModel:
        with self._session_factory() as session:
            session.add(draft_version)
            session.commit()
            session.refresh(draft_version)
            return draft_version

    def latest_for_item(self, item_id: str) -> DraftVersionModel | None:
        with self._session_factory() as session:
            return session.scalar(
                select(DraftVersionModel)
                .where(DraftVersionModel.item_id == item_id)
                .order_by(DraftVersionModel.version_number.desc())
            )


class ApprovalRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def approve(self, approval: ApprovalModel) -> ApprovalModel:
        with self._session_factory() as session:
            session.add(approval)
            session.commit()
            session.refresh(approval)
            return approval

    def for_draft_version(self, draft_version_id: str) -> ApprovalModel | None:
        with self._session_factory() as session:
            return session.scalar(
                select(ApprovalModel).where(ApprovalModel.draft_version_id == draft_version_id)
            )


class ActivityRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def record_if_new(self, event: ActivityEventModel) -> ActivityEventModel | None:
        with self._session_factory() as session:
            session.add(event)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return None
            session.refresh(event)
            return event


class CheckpointRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def get(self, source_name: str) -> datetime | None:
        with self._session_factory() as session:
            checkpoint = session.get(CheckpointModel, source_name)
            return checkpoint.last_processed_at if checkpoint else None

    def advance(self, source_name: str, processed_at: datetime) -> None:
        with self._session_factory() as session:
            checkpoint = session.get(CheckpointModel, source_name)
            if checkpoint is None:
                session.add(
                    CheckpointModel(source_name=source_name, last_processed_at=processed_at)
                )
            else:
                checkpoint.last_processed_at = processed_at
            session.commit()
