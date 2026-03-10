import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Sparkles, FolderOpen, GitCompare, Baby, ArrowRight, Dice, GitBranch, ShieldCheck, Zap, FileText, Layers } from 'lucide-react';
import { api } from '@char-gen/shared';
import { useAssistantScreenContext } from './common/AssistantContext';

const QUICK_ACTIONS = [
  { to: '/generate', label: 'Generate', description: 'Create a new character', icon: Sparkles, color: 'from-purple-500 to-pink-500' },
  { to: '/seed-generator', label: 'Seeds', description: 'Brainstorm concepts', icon: Dice, color: 'from-blue-500 to-cyan-500' },
  { to: '/drafts', label: 'Drafts', description: 'Browse saved drafts', icon: FolderOpen, color: 'from-amber-500 to-orange-500' },
  { to: '/similarity', label: 'Compare', description: 'Analyze similarities', icon: GitCompare, color: 'from-emerald-500 to-teal-500' },
  { to: '/offspring', label: 'Offspring', description: 'Combine characters', icon: Baby, color: 'from-rose-500 to-pink-500' },
  { to: '/lineage', label: 'Lineage', description: 'Explore family trees', icon: GitBranch, color: 'from-violet-500 to-purple-500' },
] as const;

const MORE_ACTIONS = [
  { to: '/validation', label: 'Validation', description: 'Check drafts and exports', icon: ShieldCheck },
  { to: '/templates', label: 'Templates', description: 'Manage templates', icon: FileText },
  { to: '/batch', label: 'Batch', description: 'Bulk generation', icon: Layers },
] as const;

interface StatCardProps {
  icon: React.ReactNode;
  value: string | number;
  label: string;
  gradient?: string;
}

function StatCard({ icon, value, label, gradient }: StatCardProps) {
  return (
    <div className={`relative overflow-hidden rounded-2xl border border-border/50 ${gradient || 'bg-gradient-to-br from-slate-800 to-slate-900'}`}>
      <div className="absolute -right-8 -top-8 h-32 w-32 bg-white/5 rounded-full blur-3xl" />
      <div className="relative p-6">
        <div className="flex items-center justify-between mb-2">
          <div className="p-3 rounded-xl bg-white/10 backdrop-blur-sm">
            {icon}
          </div>
          <div className="text-xs text-white/60 font-mono">
            {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </div>
        </div>
        <div className="text-4xl font-bold text-white mb-1">{value}</div>
        <div className="text-sm text-white/70 font-medium">{label}</div>
      </div>
    </div>
  );
}

interface ActionCardProps {
  to: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  gradient?: string;
}

function ActionCard({ to, label, description, icon: Icon, gradient }: ActionCardProps) {
  return (
    <Link
      to={to}
      className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 hover:from-slate-700/50 hover:to-slate-800/50 backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-primary/20"
    >
      <div className={`absolute -right-12 -bottom-12 h-48 w-48 ${gradient || 'bg-gradient-to-br from-primary/20 to-accent/20'} rounded-full blur-3xl group-hover:scale-110 transition-transform duration-500`} />
      <div className="relative p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className={`p-3 rounded-xl ${gradient || 'bg-gradient-to-br from-primary to-accent'} shadow-lg shadow-black/20`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-xl font-bold text-foreground">{label}</h2>
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="absolute top-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
          <ArrowRight className="h-5 w-5 text-primary" />
        </div>
      </div>
    </Link>
  );
}

interface RecentDraftCardProps {
  id: string;
  to: string;
  name: string;
  meta: string;
}

function RecentDraftCard({ id, to, name, meta }: RecentDraftCardProps) {
  return (
    <Link
      key={id}
      to={to}
      className="group flex items-center justify-between p-4 rounded-xl border border-border/50 bg-card/50 hover:bg-accent/50 hover:border-primary/30 transition-all duration-200"
    >
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-foreground truncate mb-1">{name}</div>
        <div className="text-sm text-muted-foreground truncate">{meta}</div>
      </div>
      <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors opacity-0 group-hover:opacity-100">
        <ArrowRight className="h-4 w-4 text-primary" />
      </div>
    </Link>
  );
}

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
    <div className="mx-auto max-w-7xl space-y-12 pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl border border-border/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 h-64 w-64 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 h-96 w-96 bg-accent/10 rounded-full blur-3xl" />
        </div>

        <div className="relative text-center py-16 px-8">
          <div className="mb-4">
            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl bg-gradient-to-r from-primary to-accent shadow-2xl shadow-primary/20">
              <Sparkles className="h-8 w-8 text-white animate-pulse" />
              <span className="text-4xl font-bold text-white">Character Generator</span>
            </div>
          </div>

          <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Generate template-aware character drafts with shared blueprints, validation, and export.
            <span className="block mt-2 text-primary">Start from one seed and build a consistent set of assets.</span>
          </p>

          <div className="mt-8 flex items-center justify-center gap-2">
            <Link
              to="/generate"
              className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
            >
              <Zap className="h-5 w-5" />
              Start Generating
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <div className="h-8 w-1 rounded-full bg-gradient-to-r from-primary to-accent" />
          <h2 className="text-2xl font-bold text-foreground">Quick Stats</h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard
            icon={<FolderOpen className="h-6 w-6 text-white" />}
            value={statsData?.stats?.total_drafts ?? '--'}
            label="Characters"
            gradient="bg-gradient-to-br from-violet-600 to-indigo-600"
          />
          <StatCard
            icon={<FileText className="h-6 w-6 text-white" />}
            value={templatesData?.length ?? '--'}
            label="Templates"
            gradient="bg-gradient-to-br from-cyan-600 to-blue-600"
          />
          <StatCard
            icon={<Zap className="h-6 w-6 text-white" />}
            value={statsData?.stats?.favorites ?? '--'}
            label="Favorites"
            gradient="bg-gradient-to-br from-amber-600 to-orange-600"
          />
        </div>
      </section>

      {/* Quick Actions Grid */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <div className="h-8 w-1 rounded-full bg-gradient-to-r from-primary to-accent" />
          <h2 className="text-2xl font-bold text-foreground">Quick Actions</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {QUICK_ACTIONS.map((action) => (
            <ActionCard key={action.to} {...action} />
          ))}
        </div>
      </section>

      {/* More Actions */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <div className="h-8 w-1 rounded-full bg-gradient-to-r from-primary to-accent" />
          <h2 className="text-2xl font-bold text-foreground">More Actions</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {MORE_ACTIONS.map((action) => (
            <ActionCard key={action.to} {...action} />
          ))}
        </div>
      </section>

      {/* Recent Drafts */}
      {statsData?.drafts && statsData.drafts.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="h-8 w-1 rounded-full bg-gradient-to-r from-primary to-accent" />
              <h2 className="text-2xl font-bold text-foreground">Recent Drafts</h2>
            </div>
            <Link
              to="/drafts"
              className="text-sm font-medium text-primary hover:text-primary/80 hover:underline"
            >
              View all →
            </Link>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {statsData.drafts.slice(0, 6).map((draft) => (
              <RecentDraftCard
                key={draft.review_id}
                to={`/drafts/${encodeURIComponent(draft.review_id)}`}
                name={draft.character_name || draft.seed}
                meta={`${draft.template_name || 'V2/V3 Card'} • ${draft.mode || 'SFW'}`}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
