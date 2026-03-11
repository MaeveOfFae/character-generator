export interface DraftComparisonPlaceholderProps {
  leftDraftId?: string;
  rightDraftId?: string;
}

export function DraftComparisonPlaceholder({
  leftDraftId,
  rightDraftId,
}: DraftComparisonPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Draft Comparison Placeholder</h3>
      <p className="mt-2">Planned integration point for side-by-side review, branching, and merge tooling.</p>
      <p className="mt-2">Left: {leftDraftId ?? 'unset'} · Right: {rightDraftId ?? 'unset'}</p>
    </section>
  );
}

export default DraftComparisonPlaceholder;