import type { TrackingDirection, TrackingRecordDTO } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { ...init, signal });
  if (!response.ok) {
    // Never surface the raw provider/body text to the UI.
    throw new ApiError(`Request to ${path} failed`, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function createItem(
  params: {
    description: string;
    defects: string;
    targetPriceCurrency: string;
    targetPriceValue: string;
    photos: File[];
  },
  signal?: AbortSignal,
): Promise<{ item_id: string }> {
  const body = new FormData();
  body.set("description", params.description);
  body.set("defects", params.defects);
  body.set("target_price_currency", params.targetPriceCurrency);
  body.set("target_price_value", params.targetPriceValue);
  for (const photo of params.photos) {
    body.append("photos", photo);
  }
  return request("/api/items", { method: "POST", body }, signal);
}

export function listTracking(signal?: AbortSignal): Promise<TrackingRecordDTO[]> {
  return request<TrackingRecordDTO[]>("/api/tracking", undefined, signal);
}

export function addTracking(
  params: {
    direction: TrackingDirection;
    carrier: string;
    trackingNumber: string;
    label: string;
    itemId?: string;
  },
  signal?: AbortSignal,
): Promise<{ id: string; direction: TrackingDirection; status: string }> {
  const query = new URLSearchParams({
    direction: params.direction,
    carrier: params.carrier,
    tracking_number: params.trackingNumber,
    label: params.label,
    ...(params.itemId ? { item_id: params.itemId } : {}),
  });
  return request(`/api/tracking?${query.toString()}`, { method: "POST" }, signal);
}

export function refreshTracking(
  recordId: string,
  signal?: AbortSignal,
): Promise<{ checked: number; updated: number }> {
  return request(`/api/tracking/${recordId}/refresh`, { method: "POST" }, signal);
}
