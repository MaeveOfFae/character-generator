import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CheckCircle, FolderSearch, Loader2, ShieldAlert, ShieldCheck } from 'lucide-react';
import type { ValidationResponse } from '@char-gen/shared';
import { api } from '@/lib/api';
import { useAssistantScreenContext } from '../common/AssistantContext';

export default function Validation() {
  const [path, setPath] = useState('');
  const [selectedDraftId, setSelectedDraftId] = useState('');
  const [result, setResult] = useState<ValidationResponse | null>(null);

  const { data: draftsData, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  const validatePathMutation = useMutation({
    mutationFn: () => api.validatePath({ path }),
    onSuccess: (data) => setResult(data),
  });

  const validateDraftMutation = useMutation({
    mutationFn: (draftId: string) => api.validateDraft(draftId),
    onSuccess: (data) => setResult(data),
  });

  const findings = useMemo(() => {
    if (!result?.output) {
      return [] as string[];
    }
    return result.output.split('\n').map((line) => line.trim()).filter(Boolean);
  }, [result]);

  const isPending = validatePathMutation.isPending || validateDraftMutation.isPending;
  const mutationError = validatePathMutation.error || validateDraftMutation.error;

  useAssistantScreenContext({
    validation_path: path,
    selected_draft_id: selectedDraftId,
    has_result: Boolean(result),
    validation_success: result?.success ?? null,
    validation_output_preview: result?.output.slice(0, 500) ?? '',
    is_validating: isPending,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Validation</h1>
        <p className="text-muted-foreground">
          Run browser-side validation against a saved draft or an IndexedDB-backed draft path.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <FolderSearch className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Validate Directory</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Use a saved draft path like drafts/&lt;review_id&gt; or paste a review ID directly.
          </p>
          <input
            type="text"
            value={path}
            onChange={(event) => setPath(event.target.value)}
            placeholder="drafts/20260307_203638_unnamed_character"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <button
            onClick={() => validatePathMutation.mutate()}
            disabled={isPending || !path.trim()}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {validatePathMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
            Validate Path
          </button>
        </section>

        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Validate Saved Draft</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Pick an existing draft by review ID and run the browser validator against its current saved assets.
          </p>
          <select
            value={selectedDraftId}
            onChange={(event) => setSelectedDraftId(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select a draft...</option>
            {draftsData?.drafts.map((draft) => (
              <option key={draft.review_id} value={draft.review_id}>
                {draft.character_name || draft.seed}
              </option>
            ))}
          </select>
          <button
            onClick={() => validateDraftMutation.mutate(selectedDraftId)}
            disabled={isPending || !selectedDraftId}
            className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            {validateDraftMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
            Validate Draft
          </button>
        </section>
      </div>

      {mutationError && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
          {mutationError instanceof Error ? mutationError.message : 'Validation failed'}
        </div>
      )}

      {result && (
        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Validation Results</h2>
              <p className="text-sm text-muted-foreground">{result.path}</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${result.success ? 'bg-green-500/15 text-green-600 dark:text-green-400' : 'bg-destructive/15 text-destructive'}`}>
              {result.success ? 'Passed' : 'Failed'}
            </span>
          </div>

          <div className="rounded-lg border border-border bg-muted/30 p-4">
            {findings.length === 0 ? (
              <p className="text-sm text-muted-foreground">No validator output.</p>
            ) : (
              <div className="space-y-2 text-sm">
                {findings.map((line) => (
                  <div key={line} className={line.startsWith('OK') ? 'text-green-700 dark:text-green-400' : line.startsWith('VALIDATION FAILED') ? 'font-semibold text-destructive' : line.startsWith('- ') ? 'text-yellow-700 dark:text-yellow-400' : 'text-muted-foreground'}>
                    {line}
                  </div>
                ))}
              </div>
            )}
          </div>

          {result.errors && (
            <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
              <h3 className="mb-2 text-sm font-semibold text-destructive">Stderr</h3>
              <pre className="whitespace-pre-wrap text-xs text-destructive">{result.errors}</pre>
            </div>
          )}
        </section>
      )}
    </div>
  );
}