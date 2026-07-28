export type Provenance =
  | "USER_PROVIDED"
  | "OBSERVED"
  | "SOURCE_VERIFIED"
  | "INFERRED"
  | "UNKNOWN";

export type Money = {
  currency: string;
  value: string;
};

export type ResearchField = {
  fieldName: string;
  value: string | null;
  provenance: Provenance;
  confidence: number;
  sources: string[];
};

export type ShippingZoneSummary = {
  zone: "ITALY" | "EU_CONTINENTAL" | "NON_EU_CONTINENTAL";
  publishable: boolean;
  customsWarning: string | null;
  selectedPriceLabel: string | null;
};

export type DraftReviewData = {
  photos: string[];
  title: string;
  category: string;
  conditionDescription: string;
  targetPrice: Money;
  recommendedPrice: Money | null;
  researchFields: ResearchField[];
  shippingZones: ShippingZoneSummary[];
  feeEstimate: Money | null;
  policies: { payment: string; return: string; fulfillment: string };
  warnings: string[];
  questions: string[];
  ebayWarnings: string[];
  isStale: boolean;
};

export type ListingSummary = {
  itemId: string;
  state: string;
  offerId: string | null;
  listingId: string | null;
  listingUrl: string | null;
  lastSyncedAt: string | null;
};

export type ActivityEventDTO = {
  eventType: string;
  listingTitle: string;
  amount: string | null;
  currency: string | null;
  status: string;
  time: string;
  readState: "READ" | "UNREAD";
};

export type TrackingDirection = "OUTBOUND" | "INBOUND";

export type TrackingRecordDTO = {
  id: string;
  direction: TrackingDirection;
  carrier: string;
  tracking_number: string;
  label: string;
  item_id: string | null;
  status: string;
  last_refreshed_at: string | null;
};
