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
    return <p className="empty-state">No draft selected.</p>;
  }

  const blockingWarnings =
    draft.warnings.length > 0 ||
    draft.ebayWarnings.length > 0 ||
    draft.shippingZones.some((zone) => !zone.publishable);
  const approveDisabled = draft.isStale || blockingWarnings;

  return (
    <article aria-label="Draft review" className="stack">
      <div className="card">
        <h1>{draft.title}</h1>
        <p className="section-label" style={{ marginTop: "var(--space-2)" }}>
          {draft.category}
        </p>
      </div>

      <section aria-label="Condition" className="card">
        <h2>Condition</h2>
        <p style={{ marginTop: "var(--space-2)" }}>{draft.conditionDescription}</p>
      </section>

      <div className="card">
        <ResearchEvidence fields={draft.researchFields} />
      </div>

      <section aria-label="Price" className="card">
        <h2>Price</h2>
        <div className="stack" style={{ marginTop: "var(--space-2)" }}>
          <p>Target {formatMoney(draft.targetPrice)}</p>
          {draft.recommendedPrice && <p>Recommended {formatMoney(draft.recommendedPrice)}</p>}
          {draft.feeEstimate ? (
            <p>Estimated eBay fees: {formatMoney(draft.feeEstimate)}</p>
          ) : (
            <p className="section-label">Estimated eBay fees: unavailable</p>
          )}
        </div>
      </section>

      <section aria-label="Shipping" className="card">
        <h2>Shipping</h2>
        <div className="stack" style={{ marginTop: "var(--space-2)" }}>
          {draft.shippingZones.map((zone) => (
            <div key={zone.zone}>
              <p>
                {ZONE_LABEL[zone.zone] ?? zone.zone}:{" "}
                {zone.selectedPriceLabel ?? "no confirmed rate yet"}
                {!zone.publishable && (
                  <span className="badge" style={{ marginLeft: "var(--space-2)" }}>
                    not publishable
                  </span>
                )}
              </p>
              {zone.customsWarning && (
                <p className="alert" role="alert" style={{ marginTop: "var(--space-2)" }}>
                  Non-EU customs warning: {zone.customsWarning}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section aria-label="Policies" className="card">
        <h2>Policies</h2>
        <div className="stack" style={{ marginTop: "var(--space-2)" }}>
          <p>Payment: {draft.policies.payment}</p>
          <p>Returns: {draft.policies.return}</p>
          <p>Fulfillment: {draft.policies.fulfillment}</p>
        </div>
      </section>

      {(draft.warnings.length > 0 || draft.ebayWarnings.length > 0) && (
        <section aria-label="Warnings" className="card">
          <h2>Warnings</h2>
          <div className="stack" style={{ marginTop: "var(--space-2)" }}>
            {[...draft.warnings, ...draft.ebayWarnings].map((warning) => (
              <p className="alert" role="alert" key={warning}>
                {warning}
              </p>
            ))}
          </div>
        </section>
      )}

      {draft.questions.length > 0 && (
        <section aria-label="Unresolved questions" className="card">
          <h2>Unresolved questions</h2>
          <ul style={{ marginTop: "var(--space-2)" }}>
            {draft.questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </section>
      )}

      <button
        type="button"
        className="button button--primary"
        disabled={approveDisabled}
        onClick={onApprove}
      >
        Approve this exact draft
      </button>
    </article>
  );
}
