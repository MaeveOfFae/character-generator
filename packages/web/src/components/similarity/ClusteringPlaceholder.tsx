export interface ClusteringPlaceholderProps {
  draftIds?: string[];
}

export function ClusteringPlaceholder({ draftIds = [] }: ClusteringPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Clustering Placeholder</h3>
      <p className="mt-2">Planned integration point for duplicate detection, clustering, and scorecard-style analysis.</p>
      <p className="mt-2">Draft count: {draftIds.length}</p>
    </section>
  );
}

export default ClusteringPlaceholder;