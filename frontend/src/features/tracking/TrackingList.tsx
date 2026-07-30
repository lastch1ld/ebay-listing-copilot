import { useState } from "react";

import type { TrackingDirection, TrackingRecordDTO } from "../../api/types";

export function TrackingList({
  records = [],
  onAdd,
  onRefresh,
}: {
  records?: TrackingRecordDTO[];
  onAdd?: (params: {
    direction: TrackingDirection;
    carrier: string;
    trackingNumber: string;
    label: string;
    itemId?: string;
  }) => void;
  onRefresh?: (recordId: string) => void;
}) {
  const [direction, setDirection] = useState<TrackingDirection>("OUTBOUND");
  const [carrier, setCarrier] = useState("");
  const [trackingNumber, setTrackingNumber] = useState("");
  const [label, setLabel] = useState("");
  const [itemId, setItemId] = useState("");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onAdd?.({
      direction,
      carrier,
      trackingNumber,
      label,
      itemId: direction === "OUTBOUND" && itemId ? itemId : undefined,
    });
    setCarrier("");
    setTrackingNumber("");
    setLabel("");
    setItemId("");
  };

  return (
    <section aria-label="Tracking" className="stack">
      <div className="card tracking-card">
        <h1>Tracking</h1>
        <p className="tracking-intro">Keep sold items and incoming parcels in one simple list.</p>

        <form onSubmit={handleSubmit} aria-label="Add tracking number" className="tracking-form">
          <div className="tracking-fields">
            <div className="numbered-field" role="group" aria-label="1 Direction">
              <span className="field-number" aria-hidden="true">1</span>
              <div className="field-heading">
                <label htmlFor="tracking-direction">Direction</label>
                <span className="field-hint">— Is it going out or coming to you?</span>
              </div>
              <select
                id="tracking-direction"
                value={direction}
                onChange={(event) => setDirection(event.target.value as TrackingDirection)}
              >
                <option value="OUTBOUND">Outbound (sold item)</option>
                <option value="INBOUND">Inbound (personal package)</option>
              </select>
            </div>

            <div className="numbered-field" role="group" aria-label="2 Carrier">
              <span className="field-number" aria-hidden="true">2</span>
              <div className="field-heading">
                <label htmlFor="tracking-carrier">Carrier</label>
                <span className="field-hint">— The delivery company.</span>
              </div>
              <input
                id="tracking-carrier"
                value={carrier}
                onChange={(event) => setCarrier(event.target.value)}
              />
            </div>

            <div className="numbered-field" role="group" aria-label="3 Tracking number">
              <span className="field-number" aria-hidden="true">3</span>
              <div className="field-heading">
                <label htmlFor="tracking-number">Tracking number</label>
                <span className="field-hint">— Copy it exactly as provided.</span>
              </div>
              <input
                id="tracking-number"
                value={trackingNumber}
                onChange={(event) => setTrackingNumber(event.target.value)}
              />
            </div>

            <div className="numbered-field" role="group" aria-label="4 Label">
              <span className="field-number" aria-hidden="true">4</span>
              <div className="field-heading">
                <label htmlFor="tracking-label">Label</label>
                <span className="field-hint">— A name you will recognise later.</span>
              </div>
              <input
                id="tracking-label"
                value={label}
                onChange={(event) => setLabel(event.target.value)}
              />
            </div>

            {direction === "OUTBOUND" && (
              <div className="numbered-field" role="group" aria-label="5 Linked item">
                <span className="field-number" aria-hidden="true">5</span>
                <div className="field-heading">
                <label htmlFor="tracking-item-id">Linked item (optional)</label>
                  <span className="field-hint">— Connect this parcel to a listing.</span>
                </div>
                <input
                  id="tracking-item-id"
                  value={itemId}
                  onChange={(event) => setItemId(event.target.value)}
                />
              </div>
            )}
          </div>

          <button type="submit" className="button button--primary">
            Add tracking number
          </button>
        </form>
      </div>

      {records.length === 0 ? (
        <p className="empty-state">No tracked packages yet.</p>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Direction</th>
                <th>Label</th>
                <th>Item</th>
                <th>Carrier</th>
                <th>Tracking number</th>
                <th>Status</th>
                <th>Last refreshed</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.id}>
                  <td>{record.direction}</td>
                  <td>{record.label}</td>
                  <td>{record.item_id ?? "—"}</td>
                  <td>{record.carrier}</td>
                  <td>{record.tracking_number}</td>
                  <td>
                    <span className="badge">{record.status}</span>
                  </td>
                  <td>{record.last_refreshed_at ?? "Never"}</td>
                  <td>
                    <button type="button" className="button" onClick={() => onRefresh?.(record.id)}>
                      Refresh now
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
