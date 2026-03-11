import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, FileWarning, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

export interface BlueprintLintPlaceholderProps {
  blueprintPath?: string;
}

interface BlueprintLintIssue {
  severity: 'error' | 'warning';
  message: string;
}

function lintBlueprintContent(content: string): BlueprintLintIssue[] {
  const issues: BlueprintLintIssue[] = [];
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);

  if (!frontmatterMatch) {
    issues.push({ severity: 'warning', message: 'Missing YAML frontmatter block. Browser tools will fall back to heading-derived metadata.' });
  } else {
    const frontmatter = frontmatterMatch[1];
    for (const field of ['name', 'description', 'version']) {
      if (!new RegExp(`^${field}:`, 'm').test(frontmatter)) {
        issues.push({ severity: 'warning', message: `Frontmatter is missing ${field}.` });
      }
    }
  }

  const checks: Array<[RegExp, string, BlueprintLintIssue['severity']]> = [
    [/\{PLACEHOLDER\}|\{TITLE\}/g, 'Contains unresolved placeholder tokens.', 'error'],
    [/\(\([^)]+\.\.\.[^)]+\)\)|\(\(\.\.\)\)/g, 'Contains unresolved weighted prompt slots.', 'error'],
    [/\[(Name|Age|Content):?[^\]]*\]/g, 'Contains unresolved bracket placeholders.', 'warning'],
    [/```[\s\S]*?```/g, 'ok', 'warning'],
  ];

  const hasCodeBlock = /```[\s\S]*?```/g.test(content);
  if (!hasCodeBlock) {
    issues.push({ severity: 'warning', message: 'No fenced example or output block detected.' });
  }

  for (const [pattern, message, severity] of checks.slice(0, 3)) {
    if (pattern.test(content)) {
      issues.push({ severity, message });
    }
  }

  if (content.length < 200) {
    issues.push({ severity: 'warning', message: 'Blueprint content is unusually short.' });
  }

  return issues;
}

export function BlueprintLintPlaceholder({
  blueprintPath,
}: BlueprintLintPlaceholderProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['blueprint', blueprintPath, 'lint'],
    queryFn: () => api.getBlueprint(blueprintPath || ''),
    enabled: Boolean(blueprintPath),
  });

  const issues = useMemo(() => {
    if (!data?.content) {
      return [];
    }
    return lintBlueprintContent(data.content);
  }, [data?.content]);

  const errorCount = issues.filter((issue) => issue.severity === 'error').length;
  const warningCount = issues.filter((issue) => issue.severity === 'warning').length;

  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-foreground">Blueprint Lint</h3>
          <p className="mt-2">Checks frontmatter and obvious unresolved placeholder issues for the selected blueprint.</p>
          <p className="mt-2">Blueprint: {blueprintPath ?? 'unset'}</p>
        </div>
        {issues.length === 0 && data ? (
          <CheckCircle2 className="h-5 w-5 text-green-500" />
        ) : (
          <FileWarning className="h-5 w-5 text-amber-500" />
        )}
      </div>

      {isLoading && (
        <div className="mt-4 flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Running lint checks...
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-destructive">
          Failed to load blueprint: {error.message}
        </div>
      )}

      {!isLoading && !error && data && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-muted px-2.5 py-1 text-muted-foreground">
              {errorCount} errors
            </span>
            <span className="rounded-full bg-muted px-2.5 py-1 text-muted-foreground">
              {warningCount} warnings
            </span>
          </div>

          {issues.length === 0 ? (
            <div className="rounded-md border border-green-500/40 bg-green-500/10 p-3 text-green-700 dark:text-green-300">
              No obvious lint issues found.
            </div>
          ) : (
            <div className="space-y-2">
              {issues.map((issue) => (
                <div
                  key={`${issue.severity}-${issue.message}`}
                  className={`flex items-start gap-2 rounded-md border p-3 ${issue.severity === 'error' ? 'border-destructive/40 bg-destructive/10 text-destructive' : 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300'}`}
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{issue.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* TODO: Expand blueprint linting to validate dependency graphs and template-specific output contracts once browser tooling exposes richer schema metadata. */}
        </div>
      )}
    </section>
  );
}

export default BlueprintLintPlaceholder;