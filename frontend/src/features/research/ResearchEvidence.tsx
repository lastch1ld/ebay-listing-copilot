import type { ResearchField } from "../../api/types";

const PROVENANCE_LABEL: Record<ResearchField["provenance"], string> = {
  USER_PROVIDED: "User provided",
  OBSERVED: "Observed in photos",
  SOURCE_VERIFIED: "Source verified",
  INFERRED: "Inferred",
  UNKNOWN: "Unknown",
};

export function ResearchEvidence({ fields }: { fields: ResearchField[] }) {
  if (fields.length === 0) {
    return null;
  }
  return (
    <section aria-label="Research evidence">
      <h2>Research evidence</h2>
      <ul>
        {fields.map((field) => (
          <li key={field.fieldName}>
            <strong>{field.fieldName}:</strong> {field.value ?? "Unknown"} (
            {PROVENANCE_LABEL[field.provenance]}, confidence {Math.round(field.confidence * 100)}%)
            {field.sources.length > 0 && (
              <ul>
                {field.sources.map((source) => (
                  <li key={source}>
                    <a href={source} target="_blank" rel="noreferrer">
                      {source}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
