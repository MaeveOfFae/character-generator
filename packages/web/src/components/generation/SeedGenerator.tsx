import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Sparkles, Shuffle, Loader2, ArrowRight, Copy, Check } from 'lucide-react';
import { api } from '@char-gen/shared';
import { useAssistantScreenContext } from '../common/AssistantContext';

const defaultGenreLines = ['Noir detective', 'Cyberpunk mercenary', 'Fantasy sorceress'].join('\n');

export default function SeedGenerator() {
  const navigate = useNavigate();
  const [genreLines, setGenreLines] = useState(defaultGenreLines);
  const [copiedSeed, setCopiedSeed] = useState<string | null>(null);

  const seedMutation = useMutation({
    mutationFn: (request: { genre_lines: string; surprise_mode?: boolean }) => api.generateSeeds(request),
  });

  const seeds = seedMutation.data?.seeds ?? [];

  useAssistantScreenContext({
    genre_input_preview: genreLines.slice(0, 400),
    generated_seeds_count: seeds.length,
    seeds_preview: seeds.slice(0, 5),
    is_generating: seedMutation.isPending,
    surprise_mode: Boolean(seedMutation.variables?.surprise_mode),
  });

  const handleGenerate = () => {
    seedMutation.mutate({ genre_lines: genreLines, surprise_mode: false });
  };

  const handleSurprise = () => {
    seedMutation.mutate({ genre_lines: '', surprise_mode: true });
  };

  const handleUseSeed = (seed: string) => {
    navigate('/generate', { state: { seed } });
  };

  const handleCopySeed = async (seed: string) => {
    try {
      await navigator.clipboard.writeText(seed);
      setCopiedSeed(seed);
      window.setTimeout(() => setCopiedSeed(null), 1500);
    } catch (error) {
      console.error('Failed to copy seed', error);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Seed Generator</h1>
        <p className="text-muted-foreground">
          Generate evocative character seeds from genre lines or let the model surprise you.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div>
            <label className="text-sm font-medium">Genre or Theme Lines</label>
            <p className="mt-1 text-xs text-muted-foreground">
              One line per genre, tone, or hook. The model will expand these into usable character concepts.
            </p>
          </div>

          <textarea
            value={genreLines}
            onChange={(event) => setGenreLines(event.target.value)}
            placeholder="fantasy\ncyberpunk noir\nVictorian horror"
            className="min-h-48 w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />

          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleGenerate}
              disabled={seedMutation.isPending || !genreLines.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {seedMutation.isPending && !seedMutation.variables?.surprise_mode ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Generate Seeds
            </button>

            <button
              onClick={handleSurprise}
              disabled={seedMutation.isPending}
              className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {seedMutation.isPending && seedMutation.variables?.surprise_mode ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Shuffle className="h-4 w-4" />
              )}
              Surprise Me
            </button>
          </div>

          {seedMutation.error && (
            <div className="rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              {seedMutation.error instanceof Error ? seedMutation.error.message : 'Seed generation failed'}
            </div>
          )}
        </section>

        <section className="rounded-lg border border-border bg-card p-6">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Generated Seeds</h2>
              <p className="text-sm text-muted-foreground">
                Click any result to send it directly into the character generator.
              </p>
            </div>
            <span className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">
              {seeds.length} seeds
            </span>
          </div>

          {seeds.length === 0 ? (
            <div className="flex min-h-64 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
              Generate a set of seeds to start exploring concepts.
            </div>
          ) : (
            <div className="space-y-3">
              {seeds.map((seed) => (
                <div key={seed} className="rounded-lg border border-border p-4">
                  <p className="text-sm leading-6">{seed}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      onClick={() => handleUseSeed(seed)}
                      className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                    >
                      Use In Generate
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleCopySeed(seed)}
                      className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-xs font-medium hover:bg-accent"
                    >
                      {copiedSeed === seed ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                      {copiedSeed === seed ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}