from dataclasses import dataclass

from app.integrations.ebay.rest import EbayRestClient


class MediaUploadError(RuntimeError):
    pass


@dataclass(frozen=True)
class EbayImage:
    media_id: str
    url: str


class EbayMediaClient:
    """Uploads local images through eBay's Media API and returns hosted URLs."""

    def __init__(self, rest_client: EbayRestClient) -> None:
        self._rest_client = rest_client

    def upload(self, filename: str, content_type: str, content: bytes) -> EbayImage:
        payload = self._rest_client.upload_binary(
            "/commerce/media/v1_beta/image", filename, content_type, content
        )
        status = payload.get("status")
        if status not in (None, "ACCEPTED", "PROCESSED"):
            raise MediaUploadError(f"unexpected media upload status: {status}")

        media_id = payload.get("imageId")
        url = payload.get("imageUrl")
        if not isinstance(media_id, str) or not isinstance(url, str):
            raise MediaUploadError("media upload response is missing imageId/imageUrl")
        return EbayImage(media_id=media_id, url=url)
