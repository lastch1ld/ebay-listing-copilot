import { useState } from "react";

export type IntakeSubmission = {
  description: string;
  defects: string;
  targetPriceValue: string;
  photos: File[];
};

const NO_KNOWN_DEFECTS = "No known defects";

export function ItemIntakeForm({
  onSubmit,
}: {
  onSubmit: (submission: IntakeSubmission) => void;
}) {
  const [description, setDescription] = useState("");
  const [defectsText, setDefectsText] = useState("");
  const [noKnownDefects, setNoKnownDefects] = useState(false);
  const [targetPriceValue, setTargetPriceValue] = useState("");
  const [photos, setPhotos] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!description.trim()) {
      setError("Description is required.");
      return;
    }
    if (!noKnownDefects && !defectsText.trim()) {
      setError('Describe known defects, or check "No known defects".');
      return;
    }
    if (!targetPriceValue.trim()) {
      setError("Target price is required.");
      return;
    }
    if (photos.length === 0) {
      setError("At least one photo is required.");
      return;
    }

    onSubmit({
      description,
      defects: noKnownDefects ? NO_KNOWN_DEFECTS : defectsText,
      targetPriceValue,
      photos,
    });
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Item intake" className="card intake-card">
      <header className="page-heading">
        <span className="eyebrow">Create a listing</span>
        <h1>Tell us what you’re selling.</h1>
        <p>Start with honest details and clear photos. The copilot will turn them into a reviewable draft.</p>
      </header>

      <div className="intake-layout">
        <section className="photo-workspace" aria-label="Photo upload workspace">
          <div className="field photo-field">
            <span className="section-number">01</span>
            <label id="photo-heading" htmlFor="photos">Add your photos</label>
            <p className="field-hint">JPEG, PNG or WebP · use bright, sharp images</p>
            <label className="photo-dropzone" htmlFor="photos">
              <span className="photo-dropzone__icon" aria-hidden="true">+</span>
              <strong>Choose photos</strong>
              <span>or drop them here</span>
            </label>
            <input
              className="visually-hidden"
              id="photos"
              aria-label="Photos"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={(event) => setPhotos(Array.from(event.target.files ?? []))}
            />
            {photos.length > 0 && (
              <>
                <span className="selection-status" aria-live="polite">
                  {photos.length} photo{photos.length === 1 ? "" : "s"} ready
                </span>
                <ul className="photo-preview-grid" aria-label="Selected photos">
                  {photos.map((photo, index) => (
                    <li key={`${photo.name}-${photo.lastModified}`}>
                      <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
                      <strong>{photo.name}</strong>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </section>

        <section className="details-workspace" aria-labelledby="details-heading">
          <div className="section-heading">
            <span className="section-number">02</span>
            <div>
              <h2 id="details-heading">Item details</h2>
              <p className="field-hint">Specifics help research find better matches.</p>
            </div>
          </div>
          <div className="field">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              placeholder="Brand, model, material, age, colour…"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="defects">Known defects</label>
            <textarea
              id="defects"
              placeholder="Scratches, missing parts, wear or repairs…"
              value={defectsText}
              disabled={noKnownDefects}
              onChange={(event) => setDefectsText(event.target.value)}
            />
          </div>
          <div className="field field--checkbox">
            <input
              id="no-known-defects"
              type="checkbox"
              checked={noKnownDefects}
              onChange={(event) => setNoKnownDefects(event.target.checked)}
            />
            <label htmlFor="no-known-defects">No known defects</label>
          </div>

          <div className="field">
            <label htmlFor="target-price">Target price (EUR)</label>
            <input
              id="target-price"
              type="text"
              inputMode="decimal"
              value={targetPriceValue}
              placeholder="0.00"
              onChange={(event) => setTargetPriceValue(event.target.value)}
            />
          </div>
        </section>
      </div>

      {error && (
        <p className="alert" role="alert" style={{ marginTop: "var(--space-4)" }}>
          {error}
        </p>
      )}

      <footer className="form-actions">
        <span>Your draft stays private until you explicitly approve it.</span>
        <button type="submit" className="button button--primary">
          Continue <span aria-hidden="true">→</span>
        </button>
      </footer>
    </form>
  );
}
