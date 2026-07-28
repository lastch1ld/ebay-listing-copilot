export function ApprovalSummary({
  draftVersionId,
  payloadHash,
  approvedAt,
}: {
  draftVersionId: string;
  payloadHash: string;
  approvedAt: string;
}) {
  return (
    <section aria-label="Approval summary" className="card">
      <h2>Approved</h2>
      <div className="stack" style={{ marginTop: "var(--space-2)" }}>
        <p>
          Draft version <code>{draftVersionId}</code>
        </p>
        <p>
          Hash <code>{payloadHash}</code>
        </p>
        <p className="section-label">At {approvedAt}</p>
      </div>
    </section>
  );
}
