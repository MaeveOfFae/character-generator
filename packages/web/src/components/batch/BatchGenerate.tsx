import { useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Play, Pause, Upload, X, CheckCircle, XCircle, Loader2, List } from 'lucide-react';
import type { ContentMode } from '@char-gen/shared';
import { api } from '@/lib/api';
import { useAssistantScreenContext } from '../common/AssistantContext';

interface BatchJob {
  seed: string;
  status: 'pending' | 'generating' | 'complete' | 'error';
  draftPath?: string;
  error?: string;
}

export default function BatchGenerate() {
  const [seeds, setSeeds] = useState<string[]>([]);
  const [mode, setMode] = useState<ContentMode>('SFW');
  const [template, setTemplate] = useState<string>('');
  const [parallel, setParallel] = useState(true);
  const [maxConcurrent, setMaxConcurrent] = useState(3);
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentSeed, setCurrentSeed] = useState<string>('');
  const [inputText, setInputText] = useState('');
  const abortRef = useRef<(() => void) | null>(null);

  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
  });

  const handleAddSeeds = () => {
    const newSeeds = inputText
      .split('\n')
      .map(s => s.trim())
      .filter(s => s.length > 0 && !seeds.includes(s));
    if (newSeeds.length > 0) {
      setSeeds(prev => [...prev, ...newSeeds]);
      setInputText('');
    }
  };

  const handleRemoveSeed = (seed: string) => {
    setSeeds(prev => prev.filter(s => s !== seed));
  };

  const handleClearAll = () => {
    setSeeds([]);
    setJobs([]);
  };

  const handleRunBatch = async () => {
    if (seeds.length === 0 || isRunning) return;

    setIsRunning(true);
    setJobs(seeds.map(seed => ({ seed, status: 'pending' as const })));

    try {
      const stream = api.generateBatch(seeds, {
        mode,
        template: template || undefined,
        parallel,
        max_concurrent: maxConcurrent,
      });

      abortRef.current = () => stream.abort();

      stream.subscribe((event) => {
        if (event.event === 'batch_start') {
          const data = event.data as unknown as { index: number; seed: string };
          setCurrentSeed(data.seed);
          setJobs(prev => prev.map((job, i) =>
            i === data.index ? { ...job, status: 'generating' } : job
          ));
        }
        if (event.event === 'batch_complete') {
          const data = event.data as unknown as { index: number; seed: string; draft_path: string };
          setJobs(prev => prev.map((job, i) =>
            i === data.index ? { ...job, status: 'complete', draftPath: data.draft_path } : job
          ));
        }
        if (event.event === 'batch_error') {
          const data = event.data as unknown as { index: number; seed: string; error: string };
          setJobs(prev => prev.map((job, i) =>
            i === data.index ? { ...job, status: 'error', error: data.error } : job
          ));
        }
      });

      stream.onError_((error) => {
        console.error('Batch error:', error);
        setIsRunning(false);
        setCurrentSeed('');
      });

      stream.onComplete_(() => {
        setIsRunning(false);
        setCurrentSeed('');
      });

      await stream.start();
    } catch (err) {
      console.error(err);
      setIsRunning(false);
      setCurrentSeed('');
    }
  };

  const handleStop = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsRunning(false);
      setCurrentSeed('');
    }
  };

  const modes: ContentMode[] = ['SFW', 'NSFW', 'Platform-Safe', 'Auto'];

  const completedCount = jobs.filter(j => j.status === 'complete').length;
  const errorCount = jobs.filter(j => j.status === 'error').length;
  const progress = jobs.length > 0 ? ((completedCount + errorCount) / jobs.length) * 100 : 0;

  useAssistantScreenContext({
    seed_count: seeds.length,
    current_seed: currentSeed,
    mode,
    template: template || 'default',
    parallel,
    max_concurrent: maxConcurrent,
    is_running: isRunning,
    progress_percent: Number(progress.toFixed(0)),
    completed_jobs: completedCount,
    error_jobs: errorCount,
  });

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold">Batch Generation</h1>
        <p className="text-muted-foreground">
          Generate multiple characters from a list of seeds
        </p>
      </div>

      {/* Seed Input */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <List className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Seeds</h2>
          <span className="text-sm text-muted-foreground">({seeds.length} added)</span>
        </div>

        <div className="space-y-2">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter seeds, one per line...&#10;Example:&#10;Space pirate captain with a secret&#10;Medieval healer with forbidden knowledge&#10;Cyberpunk hacker on the run"
            className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            disabled={isRunning}
          />
          <div className="flex gap-2">
            <button
              onClick={handleAddSeeds}
              disabled={!inputText.trim() || isRunning}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              Add Seeds
            </button>
            <button
              onClick={handleClearAll}
              disabled={seeds.length === 0 || isRunning}
              className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm hover:bg-accent disabled:opacity-50"
            >
              <X className="h-4 w-4" />
              Clear All
            </button>
          </div>
        </div>

        {/* Seed List */}
        {seeds.length > 0 && (
          <div className="max-h-48 overflow-y-auto rounded-md border border-border">
            <div className="divide-y divide-border">
              {seeds.map((seed, index) => (
                <div key={index} className="flex items-center justify-between px-3 py-2 text-sm">
                  <span className="truncate flex-1">{seed}</span>
                  <button
                    onClick={() => handleRemoveSeed(seed)}
                    disabled={isRunning}
                    className="ml-2 text-muted-foreground hover:text-destructive disabled:opacity-50"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Options */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Options</h2>

        <div className="grid gap-4 sm:grid-cols-2">
          {/* Mode */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Content Mode</label>
            <div className="flex flex-wrap gap-2">
              {modes.map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  disabled={isRunning}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    mode === m
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80'
                  } disabled:opacity-50`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Template */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Template</label>
            <select
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              disabled={isRunning}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Default</option>
              {templates?.map((t) => (
                <option key={t.name} value={t.name}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Parallel Settings */}
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={parallel}
              onChange={(e) => setParallel(e.target.checked)}
              disabled={isRunning}
              className="rounded border-input"
            />
            <span className="text-sm">Run in parallel</span>
          </label>

          {parallel && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Max concurrent:</label>
              <input
                type="number"
                min="1"
                max="10"
                value={maxConcurrent}
                onChange={(e) => setMaxConcurrent(parseInt(e.target.value) || 3)}
                disabled={isRunning}
                className="w-16 rounded-md border border-input bg-background px-2 py-1 text-sm"
              />
            </div>
          )}
        </div>
      </div>

      {/* Progress */}
      {jobs.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Progress</h2>
            <span className="text-sm text-muted-foreground">
              {completedCount} / {jobs.length} complete
              {errorCount > 0 && ` (${errorCount} failed)`}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Current Seed */}
          {currentSeed && (
            <div className="flex items-center gap-2 text-sm">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span>Generating: {currentSeed}</span>
            </div>
          )}

          {/* Job List */}
          <div className="max-h-64 overflow-y-auto rounded-md border border-border">
            <div className="divide-y divide-border">
              {jobs.map((job, index) => (
                <div key={index} className="flex items-center justify-between px-3 py-2 text-sm">
                  <span className="truncate flex-1">{job.seed}</span>
                  <div className="flex items-center gap-2">
                    {job.status === 'pending' && (
                      <span className="text-muted-foreground">Pending</span>
                    )}
                    {job.status === 'generating' && (
                      <span className="flex items-center gap-1 text-primary">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Generating
                      </span>
                    )}
                    {job.status === 'complete' && (
                      <a
                        href={`/drafts/${encodeURIComponent(job.draftPath || '')}`}
                        className="flex items-center gap-1 text-green-500 hover:underline"
                      >
                        <CheckCircle className="h-4 w-4" />
                        View
                      </a>
                    )}
                    {job.status === 'error' && (
                      <span className="flex items-center gap-1 text-destructive">
                        <XCircle className="h-4 w-4" />
                        {job.error || 'Error'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        {isRunning ? (
          <button
            onClick={handleStop}
            className="inline-flex items-center gap-2 rounded-md bg-destructive px-6 py-3 text-sm font-medium text-destructive-foreground hover:bg-destructive/90"
          >
            <Pause className="h-5 w-5" />
            Stop
          </button>
        ) : (
          <button
            onClick={handleRunBatch}
            disabled={seeds.length === 0}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <Play className="h-5 w-5" />
            Start Generation ({seeds.length} seeds)
          </button>
        )}
      </div>
    </div>
  );
}
