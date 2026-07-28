import httpx
import pytest
import respx

from app.config import Environment
from app.integrations.ebay.media import EbayMediaClient, MediaUploadError
from app.integrations.ebay.rest import EbayRestClient


def _client() -> EbayMediaClient:
    rest_client = EbayRestClient(
        environment=Environment.SANDBOX, access_token_provider=lambda: "token-1"
    )
    return EbayMediaClient(rest_client)


def test_upload_returns_media_id_and_url() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.sandbox.ebay.com/commerce/media/v1_beta/image").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "PROCESSED",
                    "imageId": "img-1",
                    "imageUrl": "https://i.ebayimg.invalid/img-1.jpg",
                },
            )
        )
        image = _client().upload("lamp.jpg", "image/jpeg", b"fake-bytes")

    assert image.media_id == "img-1"
    assert image.url == "https://i.ebayimg.invalid/img-1.jpg"


def test_upload_rejects_unexpected_status() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.sandbox.ebay.com/commerce/media/v1_beta/image").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "REJECTED",
                    "imageId": "img-1",
                    "imageUrl": "https://i.ebayimg.invalid/img-1.jpg",
                },
            )
        )
        with pytest.raises(MediaUploadError):
            _client().upload("lamp.jpg", "image/jpeg", b"fake-bytes")
