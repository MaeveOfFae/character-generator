export interface ExportPreviewPlaceholderProps {
  draftId?: string;
  presetName?: string;
}

export function ExportPreviewPlaceholder({
  draftId,
  presetName,
}: ExportPreviewPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Export Preview Placeholder</h3>
      <p className="mt-2">Planned integration point for dry runs, platform capability checks, and export profile previews.</p>
      <p className="mt-2">Draft: {draftId ?? 'unset'} · Preset: {presetName ?? 'unset'}</p>
    </section>
  );
}

export default ExportPreviewPlaceholder;