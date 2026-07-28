import type { DraftReviewData, Money } from "../../api/types";
import { ResearchEvidence } from "../research/ResearchEvidence";

const CURRENCY_SYMBOLS: Record<string, string> = { EUR: "€" };

function formatMoney(money: Money): string {
  const symbol = CURRENCY_SYMBOLS[money.currency] ?? `${money.currency} `;
  return `${symbol}${money.value}`;
}

const ZONE_LABEL: Record<string, string> = {
  ITALY: "Italy",
  EU_CONTINENTAL: "EU continental Europe",
  NON_EU_CONTINENTAL: "Non-EU continental Europe",
};

export function DraftReview({
  draft,
  onApprove,
}: {
  draft: DraftReviewData | null;
  onApprove?: () => void;
}) {
  if (draft === null) {
    return <p>No draft selected.</p>;
  }

  const blockingWarnings =
    draft.warnings.length > 0 ||
    draft.ebayWarnings.length > 0 ||
    draft.shippingZones.some((zone) => !zone.publishable);
  const approveDisabled = draft.isStale || blockingWarnings;

  return (
    <article aria-label="Draft review">
      <h1>{draft.title}</h1>
      <p>Category: {draft.category}</p>

      <section aria-label="Condition">
        <h2>Condition</h2>
        <p>{draft.conditionDescription}</p>
      </section>

      <ResearchEvidence fields={draft.researchFields} />

      <section aria-label="Price">
        <h2>Price</h2>
        <p>Target {formatMoney(draft.targetPrice)}</p>
        {draft.recommendedPrice && <p>Recommended {formatMoney(draft.recommendedPrice)}</p>}
        {draft.feeEstimate ? (
          <p>Estimated eBay fees: {formatMoney(draft.feeEstimate)}</p>
        ) : (
          <p>Estimated eBay fees: unavailable</p>
        )}
      </section>

      <section aria-label="Shipping">
        <h2>Shipping</h2>
        {draft.shippingZones.map((zone) => (
          <div key={zone.zone}>
            <p>
              {ZONE_LABEL[zone.zone] ?? zone.zone}:{" "}
              {zone.selectedPriceLabel ?? "no confirmed rate yet"}
              {!zone.publishable && " (not publishable)"}
            </p>
            {zone.customsWarning && (
              <p role="alert">
                Non-EU customs warning: {zone.customsWarning}
              </p>
            )}
          </div>
        ))}
      </section>

      <section aria-label="Policies">
        <h2>Policies</h2>
        <p>Payment: {draft.policies.payment}</p>
        <p>Returns: {draft.policies.return}</p>
        <p>Fulfillment: {draft.policies.fulfillment}</p>
      </section>

      {(draft.warnings.length > 0 || draft.ebayWarnings.length > 0) && (
        <section aria-label="Warnings">
          <h2>Warnings</h2>
          <ul>
            {[...draft.warnings, ...draft.ebayWarnings].map((warning) => (
              <li key={warning} role="alert">
                {warning}
              </li>
            ))}
          </ul>
        </section>
      )}

      {draft.questions.length > 0 && (
        <section aria-label="Unresolved questions">
          <h2>Unresolved questions</h2>
          <ul>
            {draft.questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </section>
      )}

      <button type="button" disabled={approveDisabled} onClick={onApprove}>
        Approve this exact draft
      </button>
    </article>
  );
}
