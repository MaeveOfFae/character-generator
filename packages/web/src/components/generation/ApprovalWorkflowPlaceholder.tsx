export interface ApprovalWorkflowPlaceholderProps {
  templateName?: string;
  assetCount?: number;
}

export function ApprovalWorkflowPlaceholder({
  templateName,
  assetCount,
}: ApprovalWorkflowPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Approval Workflow Placeholder</h3>
      <p className="mt-2">
        Planned integration point for checkpointed asset approval in the generation flow.
      </p>
      <p className="mt-2">
        Template: {templateName ?? 'default'} · Assets: {assetCount ?? 'unknown'}
      </p>
    </section>
  );
}

export default ApprovalWorkflowPlaceholder;