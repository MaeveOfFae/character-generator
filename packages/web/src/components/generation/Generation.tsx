import { useCallback, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, Zap, BookOpen, XCircle, Loader2 } from 'lucide-react';
import type { ContentMode, GenerationComplete, Template } from '@char-gen/shared';
import { api } from '@/lib/api';
import { useAssistantScreenContext } from '../common/AssistantContext';
import GenerationProgress from './GenerationProgress';
import ApprovalWorkflowPlaceholder from './ApprovalWorkflowPlaceholder';
import CheckpointSessionPlaceholder from './CheckpointSessionPlaceholder';

export default function Generation() {
  const location = useLocation();
  const navigate = useNavigate();
  const [seed, setSeed] = useState('');
  const [mode, setMode] = useState<ContentMode>('NSFW');
  const [template, setTemplate] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
  });

  useEffect(() => {
    if (!template && templates.length > 0) {
      setTemplate(templates[0].name);
    }
  }, [template, templates]);

  const selectedTemplate = templates.find((availableTemplate: Template) => availableTemplate.name === template);

  useAssistantScreenContext({
    seed_preview: seed.slice(0, 200),
    mode,
    template_name: template || null,
    is_generating: isGenerating,
    generation_error: generationError,
    available_templates: templates.length,
  });

  useEffect(() => {
    const nextSeed = (location.state as { seed?: string } | null)?.seed;
    if (nextSeed) {
      setSeed(nextSeed);
    }
  }, [location.state]);

  const handleGenerate = () => {
    if (!seed.trim()) return;
    setGenerationError(null);
    setIsGenerating(true);
  };

  const handleComplete = useCallback((data: GenerationComplete) => {
    setIsGenerating(false);
    if (data.draft_id) {
      navigate(`/drafts/${encodeURIComponent(data.draft_id)}`);
      return;
    }
    navigate('/drafts');
  }, [navigate]);

  const handleError = useCallback((error: string) => {
    setGenerationError(error);
    setIsGenerating(false);
  }, []);

  const handleCancel = useCallback(() => {
    setIsGenerating(false);
  }, []);

  const MODE_OPTIONS: { value: ContentMode; label: string; color: string }[] = [
    { value: 'SFW', label: 'Safe For Work', color: 'from-emerald-500 to-green-500' },
    { value: 'NSFW', label: 'Not Safe For Work', color: 'from-violet-500 to-purple-500' },
    { value: 'Platform-Safe', label: 'Platform Safe', color: 'from-amber-500 to-orange-500' },
    { value: 'Auto', label: 'Auto Detect', color: 'from-slate-500 to-gray-500' },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-12">
      {/* Header */}
      <div className="text-center space-y-3 mb-8">
        <div className="inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-gradient-to-r from-primary to-accent shadow-lg shadow-primary/20">
          <Sparkles className="h-6 w-6 text-white animate-pulse" />
          <span className="text-xl font-bold text-white">Generate Character</span>
        </div>
        <p className="text-muted-foreground max-w-xl mx-auto">
          Enter a seed concept and optionally choose content mode and template to generate a character.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Seed Input Section */}
        <section className="space-y-4">
          <div className="rounded-2xl border border-border/50 bg-card/50 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500">
                <Zap className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Seed</h2>
                <p className="text-sm text-muted-foreground">
                  The core concept for your character
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Enter a seed</label>
              <textarea
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                placeholder="e.g., a lonely space pirate searching for redemption"
                className="mt-1.5 min-h-32 w-full rounded-xl border border-border bg-background/50 px-4 py-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
              />
              <div className="flex items-center gap-2">
                <Link
                  to="/seed-generator"
                  className="text-sm text-primary hover:text-primary/80 hover:underline"
                >
                  Open Seed Generator →
                </Link>
              </div>
            </div>

            {generationError && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-3 py-2.5 text-sm text-destructive">
                <XCircle className="h-4 w-4 inline-flex" />
                <span className="ml-2">{generationError}</span>
              </div>
            )}
          </div>
        </section>

        {/* Options Section */}
        <section className="space-y-4">
          <div className="rounded-2xl border border-border/50 bg-card/50 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500">
                <BookOpen className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Options</h2>
                <p className="text-sm text-muted-foreground">
                  Configure generation parameters
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {/* Content Mode */}
              <div>
                <label className="text-sm font-medium mb-3 block">Content Mode</label>
                <div className="grid grid-cols-2 gap-2">
                  {MODE_OPTIONS.map((option) => {
                    const isSelected = mode === option.value;
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setMode(option.value)}
                        disabled={isGenerating}
                        className={`relative overflow-hidden rounded-xl p-3 text-left transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
                          isSelected
                            ? `bg-gradient-to-br ${option.color} text-white shadow-lg`
                            : 'bg-background/50 border border-border/50 hover:border-border'
                        }`}
                      >
                        {isSelected && (
                          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 -z-10" />
                        )}
                        <div className="relative">
                          <div className="font-semibold">{option.label}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Template Selection */}
              <div>
                <label className="text-sm font-medium mb-3 block">Template</label>
                <select
                  value={template}
                  onChange={(e) => setTemplate(e.target.value)}
                  disabled={templatesLoading || templates.length === 0 || isGenerating}
                  className="w-full rounded-xl border border-border bg-background/50 px-4 py-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {templates.length === 0 ? (
                    <option value="">No templates available</option>
                  ) : (
                    templates.map((availableTemplate: Template) => (
                      <option key={availableTemplate.name} value={availableTemplate.name}>
                        {availableTemplate.name}
                      </option>
                    ))
                  )}
                </select>
                {templatesLoading && (
                  <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading templates...
                  </div>
                )}
              </div>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !seed.trim() || templates.length === 0}
              className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-3.5 text-sm font-semibold text-primary-foreground hover:from-primary/90 hover:to-accent/90 transition-all duration-200 shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="h-5 w-5" />
              {isGenerating ? 'Generating...' : 'Generate Character'}
            </button>
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-dashed border-border/60 bg-card/40 p-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Planned Workflow Upgrades</h2>
            <p className="text-sm text-muted-foreground">
              These hooks mark where approval and checkpoint tooling will attach to the generation flow.
            </p>
          </div>
          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
            Planned
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <ApprovalWorkflowPlaceholder
            templateName={selectedTemplate?.name || template || undefined}
            assetCount={selectedTemplate?.assets.length}
          />
          <CheckpointSessionPlaceholder
            reviewId={undefined}
            resumeFromAsset={selectedTemplate?.assets[0]?.name}
          />
        </div>
      </section>

      {/* Progress Overlay */}
      {isGenerating && (
        <GenerationProgress
          seed={seed}
          mode={mode}
          template={template}
          templates={templates}
          onComplete={handleComplete}
          onError={handleError}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
}
