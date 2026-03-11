export interface BlueprintLintPlaceholderProps {
  blueprintPath?: string;
}

export function BlueprintLintPlaceholder({
  blueprintPath,
}: BlueprintLintPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Blueprint Lint Placeholder</h3>
      <p className="mt-2">Planned integration point for placeholder, dependency, and output-shape linting.</p>
      <p className="mt-2">Blueprint: {blueprintPath ?? 'unset'}</p>
    </section>
  );
}

export default BlueprintLintPlaceholder;