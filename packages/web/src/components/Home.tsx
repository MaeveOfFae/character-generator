import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Sparkles, FolderOpen, GitCompare, Baby, ArrowRight, Dices, GitBranch, ShieldCheck } from 'lucide-react';
import { api } from '@char-gen/shared';
import { useAssistantScreenContext } from './common/AssistantContext';

export default function Home() {
  const { data: statsData } = useQuery({
    queryKey: ['drafts', 'stats'],
    queryFn: () => api.getDrafts({ limit: 1 }),
  });

  const { data: templatesData } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
  });

  useAssistantScreenContext({
    draft_count: statsData?.stats?.total_drafts ?? 0,
    favorite_count: statsData?.stats?.favorites ?? 0,
    template_count: templatesData?.length ?? 0,
    recent_drafts: (statsData?.drafts ?? []).slice(0, 5).map((draft) => draft.character_name || draft.seed),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Hero */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold tracking-tight">
          Character Generator
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Generate template-aware character drafts with shared blueprints, validation, and export.
          Start from one seed and build a consistent set of assets for review, editing, and publishing.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Link
          to="/generate"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <Sparkles className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Generate</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Create a new character
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>

        <Link
          to="/seed-generator"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <Dices className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Seeds</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Brainstorm concepts
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>

        <Link
          to="/drafts"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <FolderOpen className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Drafts</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Browse saved drafts
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>

        <Link
          to="/similarity"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <GitCompare className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Compare</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Analyze similarities
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>

        <Link
          to="/offspring"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <Baby className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Offspring</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Combine characters
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>

        <Link
          to="/lineage"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <GitBranch className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Lineage</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Explore family trees
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>

        <Link
          to="/validation"
          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary hover:bg-accent"
        >
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-primary" />
            <h2 className="text-xl font-semibold">Validation</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Check drafts and exports
          </p>
          <ArrowRight className="ml-auto h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
        </Link>
      </div>

      {/* Stats */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary">
              {statsData?.stats?.total_drafts ?? '--'}
            </div>
            <div className="text-sm text-muted-foreground">Characters</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-primary">
              {templatesData?.length ?? '--'}
            </div>
            <div className="text-sm text-muted-foreground">Templates</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-primary">
              {statsData?.stats?.favorites ?? '--'}
            </div>
            <div className="text-sm text-muted-foreground">Favorites</div>
          </div>
        </div>
      </div>

      {/* Recent Drafts */}
      {statsData?.drafts && statsData.drafts.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Recent Drafts</h3>
            <Link to="/drafts" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-2">
            {statsData.drafts.slice(0, 5).map((draft) => (
              <Link
                key={draft.review_id}
                to={`/drafts/${encodeURIComponent(draft.review_id)}`}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors"
              >
                <div>
                  <div className="font-medium">{draft.character_name || draft.seed}</div>
                  <div className="text-sm text-muted-foreground">
                    {draft.template_name || 'V2/V3 Card'} • {draft.mode || 'SFW'}
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
