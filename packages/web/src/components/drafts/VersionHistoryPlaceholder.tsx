export interface VersionHistoryPlaceholderProps {
  draftId?: string;
  assetName?: string;
}

export function VersionHistoryPlaceholder({
  draftId,
  assetName,
}: VersionHistoryPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Version History Placeholder</h3>
      <p className="mt-2">Planned integration point for restore points, edit history, and asset-level provenance.</p>
      <p className="mt-2">Draft: {draftId ?? 'unset'} · Asset: {assetName ?? 'all assets'}</p>
    </section>
  );
}

export default VersionHistoryPlaceholder;