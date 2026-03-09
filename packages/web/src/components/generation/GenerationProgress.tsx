import { useState, useEffect, useCallback } from 'react';
import { CheckCircle2, Circle, Loader2, XCircle, FileText, Clock } from 'lucide-react';
import { api, type GenerationProgress as ProgressData, type GenerationComplete, type Template } from '@char-gen/shared';

function hasName(value: unknown): value is { name: string } {
  return typeof value === 'object' && value !== null && 'name' in value && typeof (value as { name: unknown }).name === 'string';
}

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
  status: 'pending' | 'generating' | 'complete' | 'error';
  content?: string;
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
  const [stage, setStage] = useState<ProgressData['stage']>('initializing');
  const [status, setStatus] = useState<ProgressData['status']>('started');
  const [currentAsset, setCurrentAsset] = useState<string | null>(null);
  const [assets, setAssets] = useState<AssetProgress[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [streamController, setStreamController] = useState<ReturnType<typeof api.generate> | null>(null);

  // Update elapsed time every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (status === 'in_progress') {
        setElapsed(Math.floor((Date.now() - startTime) / 1000));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime, status]);

  // Initialize assets from template
  useEffect(() => {
    const selectedTemplate = templates.find(t => t.name === template);
    if (selectedTemplate) {
      setAssets(
        selectedTemplate.assets.map(a => ({
          name: a.name,
          status: 'pending' as const,
        }))
      );
    } else {
      // Default assets if no template
      setAssets([
        { name: 'character_sheet', status: 'pending' },
        { name: 'intro_page', status: 'pending' },
        { name: 'character_traits', status: 'pending' },
        { name: 'character_appearance', status: 'pending' },
        { name: 'character_background', status: 'pending' },
        { name: 'character_dialogue', status: 'pending' },
      ]);
    }
  }, [template, templates]);

  // Start generation
  useEffect(() => {
    let ignoreAbortError = false;
    const stream = api.generate({ seed, mode, template, stream: true });
    setStreamController(stream);

    stream.subscribe((event) => {
      if (event.event === 'status') {
        const data = event.data as ProgressData;
        setStage(data.stage);
        setStatus(data.status);
        if (data.asset) {
          setCurrentAsset(data.asset);
          setAssets(prev =>
            prev.map(a =>
              a.name === data.asset
                ? { ...a, status: 'generating' }
                : a
            )
          );
        }
      } else if (event.event === 'chunk' && 'content' in event.data) {
        const data = event.data as { content: string };
        setStreamingContent(prev => prev + data.content);
      } else if (event.event === 'asset_complete') {
        if (hasName(event.data)) {
          const data = event.data;
          setAssets(prev =>
            prev.map(a =>
              a.name === data.name
                ? { ...a, status: 'complete' }
                : a
            )
          );
        }
        setStreamingContent('');
      } else if (event.event === 'asset') {
        if (hasName(event.data)) {
          const data = event.data;
          setCurrentAsset(data.name);
          setAssets(prev =>
            prev.map(a =>
              a.name === data.name
                ? { ...a, status: 'generating' }
                : a
            )
          );
        }
      } else if (event.event === 'complete') {
        const data = event.data as GenerationComplete;
        setStatus('complete');
        onComplete(data);
      } else if (event.event === 'error') {
        const data = event.data as { error: string };
        setError(data.error);
        setStatus('error');
        onError(data.error);
      }
    });

    stream.onError_((err) => {
      if (ignoreAbortError || /abort/i.test(err)) {
        return;
      }
      setError(err);
      setStatus('error');
      onError(err);
    });

    stream.onComplete_((data) => {
      setStatus('complete');
      onComplete(data);
    });

    stream.start();

    return () => {
      ignoreAbortError = true;
      stream.abort();
    };
  }, [seed, mode, template, onComplete, onError]);

  const handleCancel = useCallback(() => {
    if (streamController) {
      streamController.abort();
      setStatus('error');
      setError('Cancelled by user');
      onCancel();
    }
  }, [streamController, onCancel]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const completedCount = assets.filter(a => a.status === 'complete').length;
  const progress = assets.length > 0 ? (completedCount / assets.length) * 100 : 0;

  const getStageLabel = (s: ProgressData['stage']) => {
    switch (s) {
      case 'initializing': return 'Initializing...';
      case 'orchestrator': return 'Starting generation...';
      case 'parsing': return 'Parsing response...';
      case 'saving': return 'Saving draft...';
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
          <h3 className="text-lg font-semibold">{getStageLabel(stage)}</h3>
          <p className="text-sm text-muted-foreground">
            {currentAsset ? `Generating: ${currentAsset}` : 'Processing...'}
          </p>
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

      {/* Streaming Content Preview */}
      {streamingContent && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>Live Preview</span>
          </div>
          <div className="max-h-48 overflow-auto rounded-md border border-border bg-muted/50 p-3">
            <pre className="whitespace-pre-wrap text-xs">{streamingContent}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
