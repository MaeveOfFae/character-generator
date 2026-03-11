export interface PublishingPlaceholderProps {
  draftId?: string;
}

export function PublishingPlaceholder({ draftId }: PublishingPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Publishing Placeholder</h3>
      <p className="mt-2">Planned integration point for shareable bundles, preview pages, and publishing workflows.</p>
      <p className="mt-2">Draft: {draftId ?? 'unset'}</p>
    </section>
  );
}

export default PublishingPlaceholder;