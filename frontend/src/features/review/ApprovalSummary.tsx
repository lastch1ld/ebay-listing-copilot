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
    <section aria-label="Approval summary">
      <p>
        Approved draft version <code>{draftVersionId}</code>
      </p>
      <p>
        Hash: <code>{payloadHash}</code>
      </p>
      <p>At: {approvedAt}</p>
    </section>
  );
}
