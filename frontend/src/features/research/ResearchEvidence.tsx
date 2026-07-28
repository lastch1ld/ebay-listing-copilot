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
      <div className="stack" style={{ marginTop: "var(--space-2)" }}>
        {fields.map((field) => (
          <div key={field.fieldName}>
            <p>
              <strong>{field.fieldName}:</strong> {field.value ?? "Unknown"}{" "}
              <span className="badge badge--accent">{PROVENANCE_LABEL[field.provenance]}</span>{" "}
              <span className="badge">confidence {Math.round(field.confidence * 100)}%</span>
            </p>
            {field.sources.length > 0 && (
              <ul style={{ marginTop: "var(--space-1)" }}>
                {field.sources.map((source) => (
                  <li key={source}>
                    <a href={source} target="_blank" rel="noreferrer">
                      {source}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
