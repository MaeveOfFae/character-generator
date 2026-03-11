import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, Loader2, Play, RotateCcw } from 'lucide-react';
import type { ContentMode } from '@char-gen/shared';
import { api } from '@/lib/api';

export interface BlueprintSandboxPlaceholderProps {
  blueprintPath?: string;
  seed?: string;
}

type PreviewResult = {
  asset_name: string;
  content: string;
  system_prompt: string;
  user_prompt: string;
};

const MODES: ContentMode[] = ['Auto', 'SFW', 'NSFW', 'Platform-Safe'];

function deriveAssetName(blueprintPath?: string): string {
  if (!blueprintPath) {
    return 'preview_asset';
  }

  const fileName = blueprintPath.split('/').pop() || blueprintPath;
  return fileName.replace(/\.md$/i, '') || 'preview_asset';
}

export function BlueprintSandboxPlaceholder({
  blueprintPath,
  seed,
}: BlueprintSandboxPlaceholderProps) {
  const [seedInput, setSeedInput] = useState(seed ?? 'preview seed');
  const [mode, setMode] = useState<ContentMode>('Auto');
  const [assetName, setAssetName] = useState(() => deriveAssetName(blueprintPath));
  const [streamedContent, setStreamedContent] = useState('');
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const streamRef = useRef<{ abort: () => void } | null>(null);

  const { data: blueprint, isLoading } = useQuery({
    queryKey: ['blueprint', blueprintPath],
    queryFn: () => api.getBlueprint(blueprintPath || ''),
    enabled: Boolean(blueprintPath),
  });

  const resolvedAssetName = useMemo(() => deriveAssetName(blueprintPath), [blueprintPath]);

  useEffect(() => {
    setAssetName(resolvedAssetName);
    setPreview(null);
    setStreamedContent('');
    setError(null);
  }, [resolvedAssetName]);

  useEffect(() => {
    setSeedInput(seed ?? 'preview seed');
  }, [seed]);

  useEffect(() => () => {
    streamRef.current?.abort();
  }, []);

  const handleReset = () => {
    streamRef.current?.abort();
    setMode('Auto');
    setAssetName(resolvedAssetName);
    setSeedInput(seed ?? 'preview seed');
    setStreamedContent('');
    setPreview(null);
    setError(null);
    setIsRunning(false);
  };

  const handleRun = async () => {
    if (!blueprint || !seedInput.trim() || !assetName.trim()) {
      return;
    }

    streamRef.current?.abort();
    setIsRunning(true);
    setError(null);
    setPreview(null);
    setStreamedContent('');

    try {
      const stream = api.previewBlueprint({
        seed: seedInput.trim(),
        mode,
        template: undefined,
        asset_name: assetName.trim(),
        prior_assets: {},
        blueprint_content: blueprint.content,
      });

      streamRef.current = stream;

      let fullContent = '';
      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          fullContent += data.content;
          setStreamedContent(fullContent);
        }

        if (event.event === 'complete') {
          const data = event.data as PreviewResult;
          setPreview({
            asset_name: data.asset_name,
            content: data.content,
            system_prompt: data.system_prompt,
            user_prompt: data.user_prompt,
          });
          setStreamedContent(data.content);
          setIsRunning(false);
        }
      });

      stream.onError_((message) => {
        setError(message);
        setIsRunning(false);
      });

      await stream.start();
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : 'Blueprint preview failed');
      setIsRunning(false);
    }
  };

  return (
    <section className="rounded-lg border border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-foreground">
            <FlaskConical className="h-4 w-4 text-primary" />
            Blueprint Sandbox
          </h3>
          <p className="mt-2">
            Run a browser-only preview against the selected blueprint without saving a draft.
          </p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
          Live
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Blueprint</span>
          <div className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground">
            {blueprintPath ?? 'Select a blueprint from the catalog'}
          </div>
        </label>

        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Asset Name</span>
          <input
            type="text"
            value={assetName}
            onChange={(event) => setAssetName(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="system_prompt"
            disabled={!blueprintPath || isRunning}
          />
        </label>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Seed</span>
          <textarea
            value={seedInput}
            onChange={(event) => setSeedInput(event.target.value)}
            className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Describe the preview seed"
            disabled={!blueprintPath || isRunning}
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Mode</span>
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value as ContentMode)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            disabled={!blueprintPath || isRunning}
          >
            {MODES.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          onClick={() => void handleRun()}
          disabled={!blueprintPath || !blueprint || !seedInput.trim() || !assetName.trim() || isRunning}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {isRunning ? 'Running Preview' : 'Run Preview'}
        </button>
        <button
          onClick={handleReset}
          disabled={isRunning && !streamedContent}
          className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium text-foreground hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RotateCcw className="h-4 w-4" />
          Reset
        </button>
        {isLoading ? <span className="text-xs">Loading blueprint…</span> : null}
      </div>

      {error ? (
        <div className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <div className="mt-4 space-y-3">
        <div className="rounded-md border border-border bg-background/70 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Preview Output</span>
            <span className="text-xs text-muted-foreground">No draft save</span>
          </div>
          <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs text-foreground">
            {streamedContent || 'Run a preview to inspect the generated asset output.'}
          </pre>
        </div>

        <details className="rounded-md border border-border bg-background/70 p-3">
          <summary className="cursor-pointer text-xs font-medium uppercase tracking-wide text-muted-foreground">
            System Prompt
          </summary>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-words text-xs text-foreground">
            {preview?.system_prompt || 'The composed system prompt will appear here after a preview run.'}
          </pre>
        </details>

        <details className="rounded-md border border-border bg-background/70 p-3">
          <summary className="cursor-pointer text-xs font-medium uppercase tracking-wide text-muted-foreground">
            User Prompt
          </summary>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-words text-xs text-foreground">
            {preview?.user_prompt || 'The composed user prompt will appear here after a preview run.'}
          </pre>
        </details>
      </div>

      <p className="mt-3 text-xs text-muted-foreground">
        TODO: add prior-asset context sets so downstream blueprint previews can be exercised against higher-tier outputs.
      </p>
    </section>
  );
}

export default BlueprintSandboxPlaceholder;