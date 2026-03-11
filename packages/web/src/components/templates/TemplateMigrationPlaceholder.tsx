export interface TemplateMigrationPlaceholderProps {
  templateName?: string;
  draftId?: string;
}

export function TemplateMigrationPlaceholder({
  templateName,
  draftId,
}: TemplateMigrationPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Template Migration Placeholder</h3>
      <p className="mt-2">Planned integration point for migration, starter kits, onboarding, and marketplace import flows.</p>
      <p className="mt-2">Template: {templateName ?? 'unset'} · Draft: {draftId ?? 'unset'}</p>
    </section>
  );
}

export default TemplateMigrationPlaceholder;