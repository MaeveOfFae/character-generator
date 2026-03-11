import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, ClipboardList, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

export interface ReviewChecklistPlaceholderProps {
  draftId?: string;
}

export function ReviewChecklistPlaceholder({ draftId }: ReviewChecklistPlaceholderProps) {
  const draftQuery = useQuery({
    queryKey: ['draft', draftId, 'checklist'],
    queryFn: () => api.getDraft(draftId || ''),
    enabled: Boolean(draftId),
  });

  const validationQuery = useQuery({
    queryKey: ['draft', draftId, 'validation-checklist'],
    queryFn: () => api.validateDraft(draftId || ''),
    enabled: Boolean(draftId),
  });

  const checklist = useMemo(() => {
    const draft = draftQuery.data;
    const validation = validationQuery.data;
    if (!draft) {
      return [] as Array<{ label: string; passed: boolean }>;
    }

    return [
      { label: 'Character name inferred or set', passed: Boolean(draft.metadata.character_name) },
      { label: 'Template recorded', passed: Boolean(draft.metadata.template_name) },
      { label: 'At least three assets saved', passed: Object.keys(draft.assets).length >= 3 },
      { label: 'Validation passes without placeholder failures', passed: validation?.success ?? false },
    ];
  }, [draftQuery.data, validationQuery.data]);

  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-foreground">Review Checklist</h3>
          <p className="mt-2">Quick readiness pass built from draft metadata and the browser validator.</p>
          <p className="mt-2">Draft: {draftId ?? 'unset'}</p>
        </div>
        <ClipboardList className="h-5 w-5 text-primary" />
      </div>

      {(draftQuery.isLoading || validationQuery.isLoading) && (
        <div className="mt-4 flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading review checklist...
        </div>
      )}

      {!draftId ? (
        <div className="mt-4 rounded-md border border-border p-3">
          Select a draft to load review checks.
        </div>
      ) : null}

      {checklist.length > 0 && (
        <div className="mt-4 space-y-2">
          {checklist.map((item) => (
            <div key={item.label} className="flex items-center gap-2 rounded-md border border-border p-3">
              <CheckCircle2 className={`h-4 w-4 shrink-0 ${item.passed ? 'text-green-500' : 'text-muted-foreground'}`} />
              <span className={item.passed ? 'text-foreground' : 'text-muted-foreground'}>{item.label}</span>
            </div>
          ))}

          {validationQuery.data && !validationQuery.data.success && (
            <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-amber-700 dark:text-amber-300">
              {validationQuery.data.output}
            </div>
          )}

          {/* TODO: Promote this into persistent reviewer notes and asset-level scoring once the review flow stores structured annotations instead of transient checklist output. */}
        </div>
      )}
    </section>
  );
}

export default ReviewChecklistPlaceholder;