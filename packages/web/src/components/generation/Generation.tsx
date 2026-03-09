import { useCallback, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { api, type ContentMode, type GenerationComplete, type Template } from '@char-gen/shared';
import { useAssistantScreenContext } from '../common/AssistantContext';
import GenerationProgress from './GenerationProgress';

export default function Generation() {
  const location = useLocation();
  const navigate = useNavigate();
  const [seed, setSeed] = useState('');
  const [mode, setMode] = useState<ContentMode>('SFW');
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

  useAssistantScreenContext({
    seed_preview: seed.slice(0, 200),
    mode,
    template_name: template || null,
    is_generating: isGenerating,
    available_templates: templates.length,
    generation_error: generationError,
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

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Generate Character</h1>
        <p className="text-muted-foreground">
          Enter a seed concept to generate a complete character profile
        </p>
        <Link to="/seed-generator" className="mt-2 inline-block text-sm text-primary hover:underline">
          Need inspiration? Open Seed Generator
        </Link>
      </div>

      {/* Input Section */}
      <div className="space-y-4 rounded-lg border border-border bg-card p-6">
        <div>
          <label className="text-sm font-medium">Seed Concept</label>
          <textarea
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="e.g., a lonely space pirate searching for redemption"
            className="mt-1.5 h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        <div>
          <label className="text-sm font-medium">Content Mode</label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as ContentMode)}
            className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="SFW">SFW (Safe For Work)</option>
            <option value="NSFW">NSFW</option>
            <option value="Platform-Safe">Platform Safe</option>
            <option value="Auto">Auto</option>
          </select>
        </div>

        <div>
          <label className="text-sm font-medium">Template</label>
          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            disabled={templatesLoading || templates.length === 0 || isGenerating}
            className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
        </div>

        {generationError && (
          <div className="rounded-md border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {generationError}
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={isGenerating || !seed.trim() || templates.length === 0}
          className="flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles className="h-4 w-4" />
          Generate
        </button>
      </div>

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
