export interface TemplateComparisonPlaceholderProps {
  leftTemplate?: string;
  rightTemplate?: string;
}

export function TemplateComparisonPlaceholder({
  leftTemplate,
  rightTemplate,
}: TemplateComparisonPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Template Comparison Placeholder</h3>
      <p className="mt-2">Planned integration point for asset-set comparison, dependency diffs, and cloning workflows.</p>
      <p className="mt-2">Left: {leftTemplate ?? 'unset'} · Right: {rightTemplate ?? 'unset'}</p>
    </section>
  );
}

export default TemplateComparisonPlaceholder;