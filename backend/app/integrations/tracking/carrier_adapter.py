from datetime import datetime

import httpx

from app.domain.tracking import TrackingCheckpoint, TrackingStatus
from app.integrations.tracking.base import TrackingLookupError, TrackingSnapshot

_STATUS_MAP = {
    "INFO_RECEIVED": TrackingStatus.INFO_RECEIVED,
    "IN_TRANSIT": TrackingStatus.IN_TRANSIT,
    "OUT_FOR_DELIVERY": TrackingStatus.OUT_FOR_DELIVERY,
    "DELIVERED": TrackingStatus.DELIVERED,
    "EXCEPTION": TrackingStatus.EXCEPTION,
}


class AggregatorTrackingProvider:
    """Provider-neutral adapter for a multi-carrier tracking API/aggregator.

    The concrete aggregator is a deferred decision (see the design spec);
    this adapter only assumes a JSON response shaped as
    {"status": str, "checkpoints": [{"description", "location", "timestamp"}], "last_update": str}
    reachable at `{base_url}/v1/trackings/{carrier}/{tracking_number}`.
    """

    def __init__(self, base_url: str, http_client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.AsyncClient(timeout=15.0)

    async def lookup(self, carrier: str, tracking_number: str) -> TrackingSnapshot:
        try:
            response = await self._http_client.get(
                f"{self._base_url}/v1/trackings/{carrier}/{tracking_number}"
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise TrackingLookupError(
                f"tracking lookup failed for {carrier}/{tracking_number}: {error}"
            ) from error

        status = _STATUS_MAP.get(str(payload.get("status", "")), TrackingStatus.UNKNOWN)
        checkpoints = tuple(
            TrackingCheckpoint(
                description=str(entry.get("description", "")),
                location=str(entry.get("location", "")),
                provider_timestamp=datetime.fromisoformat(str(entry["timestamp"])),
            )
            for entry in payload.get("checkpoints", [])
            if isinstance(entry, dict) and "timestamp" in entry
        )
        last_update_raw = payload.get("last_update")
        last_update = (
            datetime.fromisoformat(str(last_update_raw))
            if last_update_raw
            else (checkpoints[-1].provider_timestamp if checkpoints else datetime.min)
        )
        return TrackingSnapshot(status=status, checkpoints=checkpoints, last_update=last_update)


class UnconfiguredTrackingProvider:
    """Placeholder used until a real tracking aggregator base URL is set."""

    async def lookup(self, carrier: str, tracking_number: str) -> TrackingSnapshot:
        raise TrackingLookupError(
            "tracking lookups are not configured; set TRACKING_PROVIDER_BASE_URL"
        )
