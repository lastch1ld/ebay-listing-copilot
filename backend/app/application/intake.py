import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.domain.common import Money
from app.domain.state import ItemState
from app.persistence.database import SessionFactory
from app.persistence.models import ItemModel, PhotoModel

ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}
MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024


class IntakeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Upload:
    filename: str
    mime_type: str
    content: bytes


class IntakeService:
    def __init__(self, session_factory: SessionFactory, photo_storage_dir: Path) -> None:
        self._session_factory = session_factory
        self._photo_storage_dir = photo_storage_dir
        self._photo_storage_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        description: str,
        defects: str | None,
        target_price: Money,
        photos: list[Upload],
    ) -> str:
        if not description.strip():
            raise IntakeValidationError("description is required")
        if defects is None or not defects.strip():
            raise IntakeValidationError(
                "defects acknowledgement is required: describe known defects or "
                "state 'No known defects'"
            )
        if not photos:
            raise IntakeValidationError("at least one photo is required")

        total_bytes = 0
        decoded_photos: list[tuple[Upload, str, int, int]] = []
        for upload in photos:
            expected_format = ALLOWED_MIME_TYPES.get(upload.mime_type)
            if expected_format is None:
                raise IntakeValidationError(
                    f"unsupported image type: {upload.mime_type}"
                )
            if len(upload.content) > MAX_PHOTO_BYTES:
                raise IntakeValidationError(f"{upload.filename} exceeds the per-file size limit")
            total_bytes += len(upload.content)

            decoded_format, width, height = self._decode_image(upload)
            if decoded_format != expected_format:
                raise IntakeValidationError(
                    f"{upload.filename} content does not match claimed type {upload.mime_type}"
                )
            decoded_photos.append((upload, decoded_format, width, height))

        if total_bytes > MAX_TOTAL_BYTES:
            raise IntakeValidationError("total photo size exceeds the allowed limit")

        item = ItemModel(
            state=ItemState.INTAKE,
            description=description,
            defects=defects,
            target_price_currency=target_price.currency,
            target_price_value=str(target_price.value),
        )
        with self._session_factory() as session:
            session.add(item)
            session.flush()

            for upload, _decoded_format, width, height in decoded_photos:
                content_id = hashlib.sha256(upload.content).hexdigest()
                destination = self._photo_storage_dir / content_id
                if not destination.exists():
                    destination.write_bytes(upload.content)

                session.add(
                    PhotoModel(
                        item_id=item.id,
                        sha256=content_id,
                        filename=upload.filename,
                        mime_type=upload.mime_type,
                        size_bytes=len(upload.content),
                        width=width,
                        height=height,
                    )
                )

            session.commit()
            return item.id

    @staticmethod
    def _decode_image(upload: Upload) -> tuple[str, int, int]:
        try:
            with Image.open(io.BytesIO(upload.content)) as image:
                image.verify()
            with Image.open(io.BytesIO(upload.content)) as image:
                return image.format or "", image.width, image.height
        except UnidentifiedImageError as error:
            raise IntakeValidationError(
                f"{upload.filename} content does not match claimed type {upload.mime_type}"
            ) from error
