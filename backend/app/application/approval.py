import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.domain.draft import ListingDraft
from app.persistence.database import SessionFactory
from app.persistence.models import ApprovalModel, DraftVersionModel


def draft_to_canonical_dict(draft: ListingDraft) -> dict[str, Any]:
    return {
        "sku": draft.sku,
        "marketplace_id": draft.marketplace_id,
        "title": draft.title,
        "category_id": draft.category_id,
        "condition_id": draft.condition_id,
        "condition_description": draft.condition_description,
        "description": draft.description,
        "quantity": draft.quantity,
        "price": {"currency": draft.price.currency, "value": str(draft.price.value)},
        "payment_policy_id": draft.payment_policy_id,
        "return_policy_id": draft.return_policy_id,
        "fulfillment_policy_id": draft.fulfillment_policy_id,
        "merchant_location_key": draft.merchant_location_key,
        "packed_weight_kg": draft.packed_weight_kg,
        "length_cm": draft.length_cm,
        "width_cm": draft.width_cm,
        "height_cm": draft.height_cm,
    }


def canonicalize(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonicalize(payload)).hexdigest()


@dataclass(frozen=True)
class DraftVersion:
    draft_version_id: str
    item_id: str
    payload_hash: str


@dataclass(frozen=True)
class Approval:
    draft_version_id: str
    item_id: str
    payload_hash: str


class ApprovalService:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def create_draft_version(self, item_id: str, draft: ListingDraft) -> DraftVersion:
        """Records a new canonical draft version without approving it."""
        payload = draft_to_canonical_dict(draft)
        hash_value = payload_hash(payload)

        with self._session_factory() as session:
            latest_version = session.scalar(
                select(DraftVersionModel)
                .where(DraftVersionModel.item_id == item_id)
                .order_by(DraftVersionModel.version_number.desc())
            )
            next_version = (latest_version.version_number + 1) if latest_version else 1

            draft_version = DraftVersionModel(
                item_id=item_id,
                version_number=next_version,
                payload_json=canonicalize(payload).decode("utf-8"),
                payload_hash=hash_value,
            )
            session.add(draft_version)
            session.commit()

            return DraftVersion(
                draft_version_id=draft_version.id,
                item_id=item_id,
                payload_hash=hash_value,
            )

    def approve(self, item_id: str, draft: ListingDraft) -> Approval:
        version = self.create_draft_version(item_id, draft)
        with self._session_factory() as session:
            approval = ApprovalModel(
                draft_version_id=version.draft_version_id,
                payload_hash=version.payload_hash,
                action="APPROVE",
            )
            session.add(approval)
            session.commit()

        return Approval(
            draft_version_id=version.draft_version_id,
            item_id=item_id,
            payload_hash=version.payload_hash,
        )

    def approve_existing_version(self, version: DraftVersion) -> Approval:
        with self._session_factory() as session:
            approval = ApprovalModel(
                draft_version_id=version.draft_version_id,
                payload_hash=version.payload_hash,
                action="APPROVE",
            )
            session.add(approval)
            session.commit()

        return Approval(
            draft_version_id=version.draft_version_id,
            item_id=version.item_id,
            payload_hash=version.payload_hash,
        )

    def matches(self, approval: Approval, draft: ListingDraft) -> bool:
        return approval.payload_hash == payload_hash(draft_to_canonical_dict(draft))
