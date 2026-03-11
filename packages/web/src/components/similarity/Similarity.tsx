import { useEffect, useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { GitCompare, Loader2, Users, AlertCircle, CheckCircle } from 'lucide-react';
import type { SimilarityResult } from '@char-gen/shared';
import { api } from '@/lib/api';
import { useAssistantScreenContext } from '../common/AssistantContext';

export default function Similarity() {
  const [searchParams] = useSearchParams();
  const [character1, setCharacter1] = useState<string>('');
  const [character2, setCharacter2] = useState<string>('');
  const [includeLLM, setIncludeLLM] = useState(false);
  const [result, setResult] = useState<SimilarityResult | null>(null);

  // Fetch drafts for selection
  const { data: draftsData, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  useEffect(() => {
    const nextCharacter1 = searchParams.get('character1');
    const nextCharacter2 = searchParams.get('character2');

    if (nextCharacter1) {
      setCharacter1(nextCharacter1);
    }
    if (nextCharacter2) {
      setCharacter2(nextCharacter2);
    }
  }, [searchParams]);

  // Compare mutation
  const compareMutation = useMutation({
    mutationFn: () => api.analyzeSimilarity({
      draft1_id: character1,
      draft2_id: character2,
      include_llm_analysis: includeLLM,
    }),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  useAssistantScreenContext({
    character1_id: character1 || null,
    character2_id: character2 || null,
    include_llm: includeLLM,
    is_comparing: compareMutation.isPending,
    has_result: Boolean(result),
    overall_score: result?.overall_score ?? null,
    compatibility: result?.compatibility ?? null,
    commonality_count: result?.commonalities.length ?? 0,
    difference_count: result?.differences.length ?? 0,
  });

  const handleCompare = () => {
    if (!character1 || !character2) return;
    setResult(null);
    compareMutation.mutate();
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.75) return 'text-green-500';
    if (score >= 0.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getCompatibilityColor = (compat: string) => {
    switch (compat) {
      case 'high': return 'bg-green-500/20 text-green-400';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400';
      case 'low': return 'bg-orange-500/20 text-orange-400';
      case 'conflict': return 'bg-red-500/20 text-red-400';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Compare Characters</h1>
        <p className="text-muted-foreground">
          Analyze similarities and relationships between characters
        </p>
      </div>

      {/* Selection Section */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Character 1 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Character 1</label>
          <select
            value={character1}
            onChange={(e) => setCharacter1(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select a character...</option>
            {draftsData?.drafts.map((draft) => (
              <option key={draft.review_id} value={draft.review_id}>
                {draft.character_name || draft.seed}
              </option>
            ))}
          </select>
        </div>

        {/* Character 2 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Character 2</label>
          <select
            value={character2}
            onChange={(e) => setCharacter2(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select a character...</option>
            {draftsData?.drafts.map((draft) => (
              <option key={draft.review_id} value={draft.review_id}>
                {draft.character_name || draft.seed}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Options */}
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={includeLLM}
            onChange={(e) => setIncludeLLM(e.target.checked)}
            className="rounded border-input"
          />
          Include LLM-powered deep analysis
        </label>

        <button
          onClick={handleCompare}
          disabled={!character1 || !character2 || compareMutation.isPending}
          className="ml-auto flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {compareMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <GitCompare className="h-4 w-4" />
          )}
          Compare
        </button>
      </div>

      {/* Error */}
      {compareMutation.isError && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {compareMutation.error?.message || 'Failed to compare characters'}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Overview */}
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">
                {result.character1_name} vs {result.character2_name}
              </h2>
              <span className={`rounded-full px-3 py-1 text-sm font-medium ${getCompatibilityColor(result.compatibility)}`}>
                {result.compatibility} compatibility
              </span>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="text-center">
                <div className={`text-3xl font-bold ${getScoreColor(result.overall_score)}`}>
                  {(result.overall_score * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Similarity</div>
              </div>
              <div className="text-center">
                <div className={`text-3xl font-bold ${getScoreColor(1 - result.conflict_potential)}`}>
                  {(result.conflict_potential * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Conflict Potential</div>
              </div>
              <div className="text-center">
                <div className={`text-3xl font-bold ${getScoreColor(result.synergy_potential)}`}>
                  {(result.synergy_potential * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Synergy Potential</div>
              </div>
            </div>
          </div>

          {/* Commonalities & Differences */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Commonalities
              </h3>
              {result.commonalities.length > 0 ? (
                <ul className="space-y-2">
                  {result.commonalities.map((item, i) => (
                    <li key={i} className="text-sm text-muted-foreground">• {item}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No significant commonalities found</p>
              )}
            </div>

            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-500" />
                Differences
              </h3>
              {result.differences.length > 0 ? (
                <ul className="space-y-2">
                  {result.differences.map((item, i) => (
                    <li key={i} className="text-sm text-muted-foreground">• {item}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No significant differences found</p>
              )}
            </div>
          </div>

          {/* Relationship Suggestions */}
          {result.relationship_suggestions.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="font-semibold mb-4">Relationship Suggestions</h3>
              <ul className="space-y-2">
                {result.relationship_suggestions.map((item, i) => (
                  <li key={i} className="text-sm text-muted-foreground">• {item}</li>
                ))}
              </ul>
            </div>
          )}

          {result.llm_analysis && (
            <div className="grid gap-6 md:grid-cols-2">
              <div className="rounded-lg border border-border bg-card p-6">
                <h3 className="font-semibold mb-4">LLM Relationship Read</h3>
                <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                  {result.llm_analysis.relationship_potential}
                </p>
              </div>

              <div className="rounded-lg border border-border bg-card p-6 space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Story Hooks</h3>
                  <ul className="space-y-2">
                    {result.llm_analysis.story_hooks.map((item, i) => (
                      <li key={i} className="text-sm text-muted-foreground">• {item}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <h4 className="text-sm font-medium mb-2">Conflict Areas</h4>
                    <ul className="space-y-1">
                      {result.llm_analysis.conflict_areas.map((item, i) => (
                        <li key={i} className="text-sm text-muted-foreground">• {item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-2">Synergy Areas</h4>
                    <ul className="space-y-1">
                      {result.llm_analysis.synergy_areas.map((item, i) => (
                        <li key={i} className="text-sm text-muted-foreground">• {item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !compareMutation.isPending && (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <GitCompare className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">Select Two Characters</h3>
          <p className="text-muted-foreground">
            Choose two characters from your drafts to analyze their similarities and potential relationships
          </p>
        </div>
      )}
    </div>
  );
}
