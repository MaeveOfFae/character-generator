export interface AutomationPlaceholderProps {
  workflowName?: string;
}

export function AutomationPlaceholder({ workflowName }: AutomationPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Automation Placeholder</h3>
      <p className="mt-2">Planned integration point for queued workflows, scheduled runs, and assistant automations.</p>
      <p className="mt-2">Workflow: {workflowName ?? 'unset'}</p>
    </section>
  );
}

export default AutomationPlaceholder;