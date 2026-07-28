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
    <form onSubmit={handleSubmit} aria-label="Item intake">
      <label htmlFor="description">Description</label>
      <textarea
        id="description"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />

      <label htmlFor="defects">Known defects</label>
      <textarea
        id="defects"
        value={defectsText}
        disabled={noKnownDefects}
        onChange={(event) => setDefectsText(event.target.value)}
      />
      <label htmlFor="no-known-defects">
        <input
          id="no-known-defects"
          type="checkbox"
          checked={noKnownDefects}
          onChange={(event) => setNoKnownDefects(event.target.checked)}
        />
        No known defects
      </label>

      <label htmlFor="target-price">Target price (EUR)</label>
      <input
        id="target-price"
        type="text"
        inputMode="decimal"
        value={targetPriceValue}
        onChange={(event) => setTargetPriceValue(event.target.value)}
      />

      <label htmlFor="photos">Photos</label>
      <input
        id="photos"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        multiple
        onChange={(event) => setPhotos(Array.from(event.target.files ?? []))}
      />

      {error && <p role="alert">{error}</p>}

      <button type="submit">Continue</button>
    </form>
  );
}
