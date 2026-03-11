export interface LibraryCollectionsPlaceholderProps {
  collectionName?: string;
}

export function LibraryCollectionsPlaceholder({
  collectionName,
}: LibraryCollectionsPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Library Collections Placeholder</h3>
      <p className="mt-2">Planned integration point for saved searches, collections, archive flows, and dashboard summaries.</p>
      <p className="mt-2">Collection: {collectionName ?? 'default library view'}</p>
    </section>
  );
}

export default LibraryCollectionsPlaceholder;