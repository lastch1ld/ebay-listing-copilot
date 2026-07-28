import type { ListingSummary } from "../../api/types";

export function ListingDashboard({
  listings = [],
  onProposeRevision,
}: {
  listings?: ListingSummary[];
  onProposeRevision?: (itemId: string) => void;
}) {
  if (listings.length === 0) {
    return <p>No listings yet.</p>;
  }

  return (
    <section aria-label="Listings">
      <h1>Listings</h1>
      <table>
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
              <td>{listing.state}</td>
              <td>
                {listing.listingUrl ? (
                  <a href={listing.listingUrl} target="_blank" rel="noreferrer">
                    {listing.listingId}
                  </a>
                ) : (
                  "Not published"
                )}
              </td>
              <td>{listing.lastSyncedAt ?? "Never"}</td>
              <td>
                <button type="button" onClick={() => onProposeRevision?.(listing.itemId)}>
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
