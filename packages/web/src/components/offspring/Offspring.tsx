import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Baby, Loader2, Users, CheckCircle } from 'lucide-react';
import { api, type ContentMode } from '@char-gen/shared';
import { useAssistantScreenContext } from '../common/AssistantContext';

export default function Offspring() {
  const [parent1, setParent1] = useState<string>('');
  const [parent2, setParent2] = useState<string>('');
  const [mode, setMode] = useState<ContentMode>('SFW');
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState('');
  const [result, setResult] = useState<{ draftId: string; characterName: string } | null>(null);

  // Fetch drafts for parent selection
  const { data: draftsData, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  const getParentName = (draftId: string) => {
    const draft = draftsData?.drafts.find((d) => d.review_id === draftId);
    return draft?.character_name || draftId;
  };

  useAssistantScreenContext({
    parent1_id: parent1 || null,
    parent2_id: parent2 || null,
    parent1_name: parent1 ? getParentName(parent1) : null,
    parent2_name: parent2 ? getParentName(parent2) : null,
    mode,
    is_generating: isGenerating,
    has_result: Boolean(result),
    result_character: result?.characterName ?? null,
    output_length: output.length,
    available_drafts: draftsData?.drafts.length ?? 0,
  });

  const handleGenerate = async () => {
    if (!parent1 || !parent2) return;

    setIsGenerating(true);
    setOutput('');
    setResult(null);

    try {
      const stream = api.generateOffspring({
        parent1_id: parent1,
        parent2_id: parent2,
        mode,
      });

      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          setOutput((prev) => prev + data.content);
        }
        if (event.event === 'complete' && 'draft_id' in event.data) {
          const data = event.data as { draft_id?: string; character_name?: string };
          setResult({
            draftId: data.draft_id || '',
            characterName: data.character_name || 'Unknown',
          });
        }
      });

      stream.onError_((error) => {
        console.error('Offspring generation error:', error);
        setIsGenerating(false);
      });

      stream.onComplete_(() => {
        setIsGenerating(false);
      });

      await stream.start();
    } catch (err) {
      console.error(err);
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const modes: ContentMode[] = ['SFW', 'NSFW', 'Platform-Safe', 'Auto'];

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold">Offspring Generator</h1>
        <p className="text-muted-foreground">
          Create a child character from two parent characters
        </p>
      </div>

      {/* Parent Selection */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Parent 1 */}
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Parent 1</h2>
          </div>
          <select
            value={parent1}
            onChange={(e) => setParent1(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select parent 1...</option>
            {draftsData?.drafts
              .filter((d) => d.review_id !== parent2)
              .map((draft) => (
                <option key={draft.review_id} value={draft.review_id}>
                  {draft.character_name || draft.review_id}
                </option>
              ))}
          </select>
          {parent1 && (
            <p className="mt-2 text-sm text-muted-foreground">
              Selected: {getParentName(parent1)}
            </p>
          )}
        </div>

        {/* Parent 2 */}
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-5 w-5 text-secondary" />
            <h2 className="text-lg font-semibold">Parent 2</h2>
          </div>
          <select
            value={parent2}
            onChange={(e) => setParent2(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select parent 2...</option>
            {draftsData?.drafts
              .filter((d) => d.review_id !== parent1)
              .map((draft) => (
                <option key={draft.review_id} value={draft.review_id}>
                  {draft.character_name || draft.review_id}
                </option>
              ))}
          </select>
          {parent2 && (
            <p className="mt-2 text-sm text-muted-foreground">
              Selected: {getParentName(parent2)}
            </p>
          )}
        </div>
      </div>

      {/* Options */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Options</h2>

        <div className="space-y-2">
          <label className="text-sm font-medium">Content Mode</label>
          <div className="flex flex-wrap gap-2">
            {modes.map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === m
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={!parent1 || !parent2 || isGenerating}
          className="w-full flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Generating Offspring...
            </>
          ) : (
            <>
              <Baby className="h-5 w-5" />
              Generate Offspring
            </>
          )}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="rounded-lg border border-green-500/50 bg-green-500/10 p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h2 className="text-lg font-semibold text-green-500">Offspring Created!</h2>
          </div>
          <p className="text-sm mb-2">
            <strong>Character:</strong> {result.characterName}
          </p>
          <p className="text-sm text-muted-foreground">
            <strong>Parents:</strong> {getParentName(parent1)} + {getParentName(parent2)}
          </p>
          <Link
            to={`/drafts/${encodeURIComponent(result.draftId)}`}
            className="mt-4 inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            View Character
          </Link>
        </div>
      )}

      {/* Output Preview */}
      {output && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Generation Output</h2>
          <div className="rounded-lg border border-border bg-card p-4 max-h-96 overflow-auto">
            <pre className="whitespace-pre-wrap text-sm">{output}</pre>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!parent1 && !parent2 && !isGenerating && (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <Baby className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">Select Two Parents</h3>
          <p className="text-muted-foreground">
            Choose two characters to combine their traits into a new character
          </p>
        </div>
      )}
    </div>
  );
}
