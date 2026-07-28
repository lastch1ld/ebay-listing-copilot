import httpx
import pytest
import respx

from app.domain.tracking import TrackingStatus
from app.integrations.tracking.base import TrackingLookupError
from app.integrations.tracking.carrier_adapter import AggregatorTrackingProvider


@pytest.mark.asyncio
async def test_lookup_parses_status_and_checkpoints():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://tracking.invalid/v1/trackings/dhl/JD0001").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "IN_TRANSIT",
                    "checkpoints": [
                        {
                            "description": "Departed facility",
                            "location": "Milan, IT",
                            "timestamp": "2026-01-01T00:00:00+00:00",
                        }
                    ],
                    "last_update": "2026-01-01T00:00:00+00:00",
                },
            )
        )
        async with httpx.AsyncClient() as http_client:
            provider = AggregatorTrackingProvider("https://tracking.invalid", http_client)
            snapshot = await provider.lookup("dhl", "JD0001")

    assert snapshot.status is TrackingStatus.IN_TRANSIT
    assert len(snapshot.checkpoints) == 1
    assert snapshot.checkpoints[0].location == "Milan, IT"


@pytest.mark.asyncio
async def test_unknown_status_string_maps_to_unknown():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://tracking.invalid/v1/trackings/dhl/JD0001").mock(
            return_value=httpx.Response(
                200, json={"status": "SOME_NEW_CARRIER_STATUS", "checkpoints": []}
            )
        )
        async with httpx.AsyncClient() as http_client:
            provider = AggregatorTrackingProvider("https://tracking.invalid", http_client)
            snapshot = await provider.lookup("dhl", "JD0001")

    assert snapshot.status is TrackingStatus.UNKNOWN


@pytest.mark.asyncio
async def test_http_failure_raises_normalized_lookup_error():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://tracking.invalid/v1/trackings/dhl/JD0001").mock(
            return_value=httpx.Response(503)
        )
        async with httpx.AsyncClient() as http_client:
            provider = AggregatorTrackingProvider("https://tracking.invalid", http_client)
            with pytest.raises(TrackingLookupError):
                await provider.lookup("dhl", "JD0001")
