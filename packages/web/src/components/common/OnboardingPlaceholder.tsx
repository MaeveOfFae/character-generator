export interface OnboardingPlaceholderProps {
  templateName?: string;
}

export function OnboardingPlaceholder({ templateName }: OnboardingPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Onboarding Placeholder</h3>
      <p className="mt-2">Planned integration point for guided empty states, first-run flows, and template-aware help.</p>
      <p className="mt-2">Template: {templateName ?? 'unset'}</p>
    </section>
  );
}

export default OnboardingPlaceholder;