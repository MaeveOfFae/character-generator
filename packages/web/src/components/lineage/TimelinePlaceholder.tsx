export interface TimelinePlaceholderProps {
  rootDraftId?: string;
}

export function TimelinePlaceholder({ rootDraftId }: TimelinePlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Timeline Placeholder</h3>
      <p className="mt-2">Planned integration point for lineage timelines, family trees, and affiliation views.</p>
      <p className="mt-2">Root draft: {rootDraftId ?? 'unset'}</p>
    </section>
  );
}

export default TimelinePlaceholder;