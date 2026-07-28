import type { ListingSummary } from "../../api/types";

export function ListingDashboard({
  listings = [],
  onProposeRevision,
}: {
  listings?: ListingSummary[];
  onProposeRevision?: (itemId: string) => void;
}) {
  if (listings.length === 0) {
    return <p className="empty-state">No listings yet. Create an item to get started.</p>;
  }

  return (
    <section aria-label="Listings" className="card">
      <h1>Listings</h1>
      <table className="table" style={{ marginTop: "var(--space-4)" }}>
        <thead>
          <tr>
            <th>State</th>
            <th>Listing</th>
            <th>Last synced</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {listings.map((listing) => (
            <tr key={listing.itemId}>
              <td>
                <span className="badge">{listing.state}</span>
              </td>
              <td>
                {listing.listingUrl ? (
                  <a href={listing.listingUrl} target="_blank" rel="noreferrer">
                    {listing.listingId}
                  </a>
                ) : (
                  <span className="section-label">Not published</span>
                )}
              </td>
              <td>{listing.lastSyncedAt ?? "Never"}</td>
              <td>
                <button
                  type="button"
                  className="button"
                  onClick={() => onProposeRevision?.(listing.itemId)}
                >
                  Propose revision
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
