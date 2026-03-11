export interface BlueprintSandboxPlaceholderProps {
  blueprintPath?: string;
  seed?: string;
}

export function BlueprintSandboxPlaceholder({
  blueprintPath,
  seed,
}: BlueprintSandboxPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Blueprint Sandbox Placeholder</h3>
      <p className="mt-2">Planned integration point for preview runs and prompt experimentation without saving drafts.</p>
      <p className="mt-2">Blueprint: {blueprintPath ?? 'unset'} · Seed: {seed ?? 'unset'}</p>
    </section>
  );
}

export default BlueprintSandboxPlaceholder;