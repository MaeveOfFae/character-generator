import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { CheckCircle2, Circle, Loader2, XCircle, FileText, Clock, RotateCcw, Save } from 'lucide-react';
import type { GenerationComplete, Template } from '@char-gen/shared';
import { GenerationService } from '../../lib/services/generation.js';
import { configManager } from '../../lib/config/manager.js';
import {
  clearActiveGenerationSession,
  loadActiveGenerationSession,
  matchesActiveGenerationSession,
  saveActiveGenerationSession,
  type ActiveGenerationSession,
} from '../../lib/services/generation-session.js';
import { inferCharacterDisplayNameForTemplate } from '../../lib/templates/browser.js';

interface GenerationProgressProps {
  seed: string;
  mode: 'SFW' | 'NSFW' | 'Platform-Safe' | 'Auto';
  template?: string;
  templates: Template[];
  onComplete: (data: GenerationComplete) => void;
  onError: (error: string) => void;
  onCancel: () => void;
}

interface AssetProgress {
  name: string;
  status: 'pending' | 'generating' | 'reviewing' | 'complete' | 'error';
  content?: string;
}

type ResumeAction =
  | { type: 'idle' }
  | { type: 'new' }
  | { type: 'review' }
  | { type: 'generate'; assetIndex: number; approvedAssets: Record<string, string> }
  | { type: 'save'; approvedAssets: Record<string, string> };

function sortTemplateAssets(template?: Template): string[] {
  if (!template) {
    return [];
  }

  const assets = template.assets;
  const inDegree = new Map<string, number>();
  const edges = new Map<string, string[]>();

  for (const asset of assets) {
    inDegree.set(asset.name, asset.depends_on.length);
    edges.set(asset.name, []);
  }

  for (const asset of assets) {
    for (const dependency of asset.depends_on) {
      const dependents = edges.get(dependency);
      if (dependents) {
        dependents.push(asset.name);
      }
    }
  }

  const queue = assets.filter((asset) => asset.depends_on.length === 0).map((asset) => asset.name);
  const ordered: string[] = [];

  while (queue.length > 0) {
    const current = queue.shift()!;
    ordered.push(current);
    for (const dependent of edges.get(current) || []) {
      const nextDegree = (inDegree.get(dependent) || 0) - 1;
      inDegree.set(dependent, nextDegree);
      if (nextDegree === 0) {
        queue.push(dependent);
      }
    }
  }

  return ordered.length === assets.length ? ordered : assets.map((asset) => asset.name);
}

export default function GenerationProgress({
  seed,
  mode,
  template,
  templates,
  onComplete,
  onError,
  onCancel,
}: GenerationProgressProps) {
  const [status, setStatus] = useState<'initializing' | 'generating' | 'reviewing' | 'saving' | 'complete' | 'error'>('initializing');
  const [currentAsset, setCurrentAsset] = useState<string | null>(null);
  const [assets, setAssets] = useState<AssetProgress[]>([]);
  const [assetDrafts, setAssetDrafts] = useState<Record<string, string>>({});
  const [editorContent, setEditorContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [characterName, setCharacterName] = useState<string | null>(null);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [resumeAction, setResumeAction] = useState<ResumeAction>({ type: 'idle' });
  const abortControllerRef = useRef<AbortController | null>(null);
  const restoredSessionRef = useRef<ActiveGenerationSession | null>(loadActiveGenerationSession());

  const selectedTemplate = useMemo(
    () => templates.find((candidate) => candidate.name === template),
    [template, templates]
  );
  const assetOrder = useMemo(() => sortTemplateAssets(selectedTemplate), [selectedTemplate]);

  const updateAssetStatus = useCallback((assetName: string, nextStatus: AssetProgress['status'], content?: string) => {
    setAssets((previous) => previous.map((asset) => (
      asset.name === assetName
        ? { ...asset, status: nextStatus, content: content ?? asset.content }
        : asset
    )));
  }, []);

  const getApprovedAssets = useCallback((upToIndex: number, currentOverride?: { name: string; content: string }) => {
    const approved: Record<string, string> = {};
    for (let index = 0; index < upToIndex; index += 1) {
      const assetName = assetOrder[index];
      const content = assetDrafts[assetName];
      if (content) {
        approved[assetName] = content;
      }
    }
    if (currentOverride) {
      approved[currentOverride.name] = currentOverride.content;
    }
    return approved;
  }, [assetDrafts, assetOrder]);

  const generateAsset = useCallback(async (assetIndex: number, approvedAssets: Record<string, string>) => {
    const assetName = assetOrder[assetIndex];
    if (!assetName) {
      return;
    }

    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setStatus('generating');
    setCurrentAsset(assetName);
    setEditorContent('');
    updateAssetStatus(assetName, 'generating');

    try {
      // Use client-side GenerationService for single asset generation
      let fullContent = '';

      for await (const progress of GenerationService.generateAsset({
        seed,
        mode: mode as 'SFW' | 'NSFW' | 'Platform-Safe',
        template,
        asset_name: assetName,
        prior_assets: approvedAssets,
      })) {
        if (controller.signal.aborted) {
          return;
        }

        if (progress.type === 'chunk' && progress.content) {
          fullContent += progress.content;
          setEditorContent(fullContent);
          setStatus('generating');
        } else if (progress.type === 'asset' && progress.content) {
          fullContent = progress.content;
          setEditorContent(fullContent);
          updateAssetStatus(assetName, 'reviewing', fullContent);
          setStatus('reviewing');
          return;
        } else if (progress.type === 'error') {
          throw new Error(progress.error || 'Asset generation failed');
        }
      }

      if (!fullContent) {
        throw new Error('No content generated');
      }

      updateAssetStatus(assetName, 'reviewing', fullContent);
      setStatus('reviewing');
    } catch (generationError) {
      if (controller.signal.aborted) {
        return;
      }
      const message = generationError instanceof Error ? generationError.message : 'Asset generation failed';
      setError(message);
      updateAssetStatus(assetName, 'error');
      setStatus('error');
      onError(message);
    }
  }, [assetOrder, mode, onError, seed, template, updateAssetStatus]);

  const saveApprovedDraft = useCallback(async (approvedAssets: Record<string, string>) => {
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    setStatus('saving');

    try {
      const { DraftStorage } = await import('../../lib/storage/draft-db.js');
      const reviewId = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      const nextCharacterName = inferCharacterDisplayNameForTemplate(approvedAssets, template);

      const draft = {
        path: reviewId,
        metadata: {
          review_id: reviewId,
          seed,
          mode: mode as 'SFW' | 'NSFW' | 'Platform-Safe',
          model: configManager.getConfig().model,
          created: new Date().toISOString(),
          modified: new Date().toISOString(),
          favorite: false,
          template_name: template,
          character_name: nextCharacterName,
        },
        assets: approvedAssets,
      };

      await DraftStorage.saveDraft(draft);

      clearActiveGenerationSession();
      setCharacterName(nextCharacterName);
      setStatus('complete');
      onComplete({
        draft_path: reviewId,
        draft_id: reviewId,
        character_name: nextCharacterName,
        duration_ms: Date.now() - startTime,
      });
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : 'Failed to save draft';
      setError(message);
      setStatus('error');
      clearActiveGenerationSession();
      onError(message);
    }
  }, [mode, onComplete, onError, seed, startTime, template]);

  // Update elapsed time every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (status === 'generating' || status === 'reviewing' || status === 'saving') {
        setElapsed(Math.floor((Date.now() - startTime) / 1000));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime, status]);

  // Initialize assets from template
  useEffect(() => {
    if (assetOrder.length === 0) {
      setAssets([]);
      setResumeAction({ type: 'idle' });
      return;
    }

    const storedSession = restoredSessionRef.current;
    const canResume = storedSession
      && matchesActiveGenerationSession(storedSession, { seed, mode, template })
      && Object.keys(storedSession.assetDrafts).every((assetName) => assetOrder.includes(assetName));

    if (!canResume) {
      setAssets(assetOrder.map((name) => ({ name, status: 'pending' })));
      setAssetDrafts({});
      setCurrentAsset(null);
      setEditorContent('');
      setError(null);
      setCharacterName(null);
      setResumeAction({ type: 'new' });
      return;
    }

    const approvedAssets = storedSession.assetDrafts;
    const restoredCurrentAsset = storedSession.currentAsset && assetOrder.includes(storedSession.currentAsset)
      ? storedSession.currentAsset
      : null;
    const restoredAssets = assetOrder.map((name) => {
      if (approvedAssets[name]) {
        return { name, status: 'complete' as const, content: approvedAssets[name] };
      }
      if (restoredCurrentAsset === name && storedSession.currentStatus === 'reviewing') {
        return { name, status: 'reviewing' as const, content: storedSession.currentAssetContent };
      }
      return { name, status: 'pending' as const };
    });

    setAssets(restoredAssets);
    setAssetDrafts(approvedAssets);
    setCurrentAsset(restoredCurrentAsset);
    setEditorContent(storedSession.currentStatus === 'reviewing' ? storedSession.currentAssetContent : '');
    setError(null);
    setCharacterName(inferCharacterDisplayNameForTemplate(approvedAssets, template));

    if (storedSession.currentStatus === 'reviewing' && restoredCurrentAsset) {
      setStatus('reviewing');
      setResumeAction({ type: 'review' });
      return;
    }

    if (Object.keys(approvedAssets).length >= assetOrder.length) {
      setStatus('saving');
      setResumeAction({ type: 'save', approvedAssets });
      return;
    }

    const nextAssetName = restoredCurrentAsset || assetOrder[Object.keys(approvedAssets).length];
    const nextAssetIndex = assetOrder.indexOf(nextAssetName);

    setStatus('initializing');
    setResumeAction({
      type: 'generate',
      assetIndex: nextAssetIndex >= 0 ? nextAssetIndex : 0,
      approvedAssets,
    });
  }, [assetOrder, mode, seed, template]);

  // Start generation
  useEffect(() => {
    if (resumeAction.type === 'idle' || assetOrder.length === 0) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      if (resumeAction.type === 'new') {
        void generateAsset(0, {});
        return;
      }

      if (resumeAction.type === 'generate') {
        void generateAsset(resumeAction.assetIndex, resumeAction.approvedAssets);
        return;
      }

      if (resumeAction.type === 'save') {
        void saveApprovedDraft(resumeAction.approvedAssets);
      }
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
      abortControllerRef.current?.abort();
    };
  }, [assetOrder.length, generateAsset, resumeAction, saveApprovedDraft]);

  useEffect(() => {
    if (status === 'complete' || status === 'error') {
      return;
    }

    const currentStatus = status === 'reviewing' || status === 'saving' ? status : 'generating';
    saveActiveGenerationSession({
      version: 1,
      seed,
      mode,
      template,
      assetDrafts,
      currentAsset,
      currentAssetContent: currentStatus === 'reviewing' ? editorContent : '',
      currentStatus,
      startedAt: startTime,
      updatedAt: Date.now(),
    });
  }, [assetDrafts, currentAsset, editorContent, mode, seed, startTime, status, template]);

  const handleCancel = useCallback(() => {
    abortControllerRef.current?.abort();
    clearActiveGenerationSession();
    onCancel();
  }, [onCancel]);

  const handleContinue = useCallback(async () => {
    if (!currentAsset) {
      return;
    }

    const assetIndex = assetOrder.indexOf(currentAsset);
    const approved = getApprovedAssets(assetIndex, { name: currentAsset, content: editorContent });
    setAssetDrafts(approved);
    updateAssetStatus(currentAsset, 'complete', editorContent);

    const nextIndex = assetIndex + 1;
    if (nextIndex < assetOrder.length) {
      await generateAsset(nextIndex, approved);
      return;
    }

    await saveApprovedDraft(approved);
  }, [assetOrder, currentAsset, editorContent, generateAsset, getApprovedAssets, saveApprovedDraft, updateAssetStatus]);

  const handleRegenerate = useCallback(async () => {
    if (!currentAsset) {
      return;
    }
    const assetIndex = assetOrder.indexOf(currentAsset);
    const approved = getApprovedAssets(assetIndex);
    await generateAsset(assetIndex, approved);
  }, [assetOrder, currentAsset, generateAsset, getApprovedAssets]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const completedCount = assets.filter(a => a.status === 'complete').length;
  const progress = assets.length > 0 ? (completedCount / assets.length) * 100 : 0;

  const getStageLabel = (s: typeof status) => {
    switch (s) {
      case 'initializing': return 'Preparing generation...';
      case 'generating': return 'Generating current asset...';
      case 'reviewing': return 'Review and edit this asset';
      case 'saving': return 'Saving reviewed draft...';
      case 'complete': return 'Complete!';
      case 'error': return 'Error';
      default: return s;
    }
  };

  const getAssetIcon = (status: AssetProgress['status']) => {
    switch (status) {
      case 'complete':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'generating':
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case 'reviewing':
        return <FileText className="h-4 w-4 text-amber-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return <Circle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  if (status === 'error') {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-6">
        <div className="flex items-center gap-2 text-destructive">
          <XCircle className="h-5 w-5" />
          <h3 className="font-semibold">Generation Failed</h3>
        </div>
        <p className="mt-2 text-sm text-destructive/80">{error}</p>
        <button
          onClick={onCancel}
          className="mt-4 rounded-md bg-destructive px-4 py-2 text-sm text-destructive-foreground hover:bg-destructive/90"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{getStageLabel(status)}</h3>
          <p className="text-sm text-muted-foreground">
            {currentAsset ? `Current asset: ${currentAsset}` : 'Processing...'}
          </p>
          {characterName && (
            <p className="text-sm text-muted-foreground">Character: {characterName}</p>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            {formatTime(elapsed)}
          </div>
          <button
            onClick={handleCancel}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm hover:bg-accent"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Progress</span>
          <span>{completedCount} / {assets.length} assets</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Asset List */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {assets.map(asset => (
          <div
            key={asset.name}
            className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${
              asset.status === 'generating'
                ? 'border-primary bg-primary/10'
                : asset.status === 'reviewing'
                ? 'border-amber-500/50 bg-amber-500/10'
                : asset.status === 'complete'
                ? 'border-green-500/50 bg-green-500/10'
                : 'border-border'
            }`}
          >
            {getAssetIcon(asset.status)}
            <span className="truncate">{asset.name}</span>
          </div>
        ))}
      </div>

      {/* Current Asset Editor */}
      {currentAsset && (status === 'reviewing' || status === 'generating' || status === 'saving') && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>{currentAsset.replace(/_/g, ' ')}</span>
          </div>
          <textarea
            value={editorContent}
            onChange={(event) => setEditorContent(event.target.value)}
            disabled={status !== 'reviewing'}
            className="min-h-[280px] w-full rounded-md border border-input bg-background p-3 text-sm font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-70"
          />
          <p className="text-xs text-muted-foreground">
            Downstream assets will use this reviewed text as source context.
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => void handleRegenerate()}
              disabled={status !== 'reviewing'}
              className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4" />
              Regenerate Asset
            </button>
            <button
              onClick={() => void handleContinue()}
              disabled={status !== 'reviewing' || !editorContent.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {completedCount + 1 >= assets.length ? 'Save Draft' : 'Approve and Continue'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
