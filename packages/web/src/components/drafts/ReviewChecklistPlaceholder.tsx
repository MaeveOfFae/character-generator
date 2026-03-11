export interface ReviewChecklistPlaceholderProps {
  draftId?: string;
}

export function ReviewChecklistPlaceholder({ draftId }: ReviewChecklistPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Review Checklist Placeholder</h3>
      <p className="mt-2">Planned integration point for structured review notes, scoring, and asset health checks.</p>
      <p className="mt-2">Draft: {draftId ?? 'unset'}</p>
    </section>
  );
}

export default ReviewChecklistPlaceholder;