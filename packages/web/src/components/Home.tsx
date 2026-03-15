import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Sparkles, FolderOpen, GitCompare, Baby, ArrowRight, Dice1, GitBranch, ShieldCheck, Zap, FileText, Layers, PlayCircle, RotateCcw, Target } from 'lucide-react';
import type { DraftMetadata } from '@char-gen/shared';
import { api } from '@/lib/api';
import { getGuidedTour, gettingStartedSteps, guidedTours } from '@/lib/help';
import { roadmapGroups } from '@/lib/roadmap';
import { releaseNotes } from '@/lib/whats-new';
import { useGuidedTour } from './common/GuidedTourContext';
import { useAssistantScreenContext } from './common/useAssistantContext';
import AutomationPlaceholder from './common/AutomationPlaceholder';
import OnboardingPlaceholder from './common/OnboardingPlaceholder';

const QUICK_ACTIONS = [
  { to: '/generate', label: 'Generate', description: 'Create a new simulacrum', icon: Sparkles, color: 'from-purple-500 to-pink-500' },
  { to: '/seed-generator', label: 'Seeds', description: 'Brainstorm concepts', icon: Dice1, color: 'from-blue-500 to-cyan-500' },
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

function formatReleaseDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function Home() {
  const { activeStepIndex, activeTourId, goToCurrentStep, helpState, isTourCompleted, restartTour, startTour } = useGuidedTour();
  const { data: statsData } = useQuery({
    queryKey: ['drafts', 'stats'],
    queryFn: () => api.getDrafts({ limit: 1 }),
  });

  const { data: templatesData } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.listTemplates(),
  });

  useAssistantScreenContext({
    draft_count: statsData?.stats?.total_drafts ?? 0,
    favorite_count: statsData?.stats?.favorites ?? 0,
    template_count: templatesData?.length ?? 0,
    recent_drafts: (statsData?.drafts ?? []).slice(0, 5).map((draft: DraftMetadata) => draft.character_name || draft.seed),
  });

  const upcomingUpdates = roadmapGroups
    .filter((group) => group.status !== 'implemented')
    .slice(0, 4)
    .map((group) => ({
      id: group.id,
      title: group.title,
      summary: group.items[0],
      ownerFile: group.ownerFiles[0],
    }));

  const nextIncompleteTour = guidedTours.find((tour) => !isTourCompleted(tour.id)) ?? null;
  const activeTour = activeTourId ? getGuidedTour(activeTourId) : null;
  const activeTourStep = activeTour?.steps[activeStepIndex] ?? null;

  return (
    <div className="space-y-12 pb-12">
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
              <span className="text-4xl font-bold text-white">Eidolon Simulacra</span>
            </div>
          </div>

          <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Generate template-aware simulacra with blueprint templates, validation, and export.
            <span className="block mt-2 text-primary">Start from one seed and compile a consistent set of assets.</span>
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

      {/* Browser-Only Mode Notice */}
      <section className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-amber-400" />
          <div>
            <h2 className="text-sm font-semibold text-foreground">Browser-Only Mode</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              This workspace runs fully client-side. Drafts, templates, theme presets, and blueprint edits stay in the browser instead of syncing through a local API server.
            </p>
          </div>
        </div>
      </section>

      {/* 2-Column Layout */}
      <div className="grid gap-8 xl:grid-cols-[minmax(0,2fr)_minmax(340px,1fr)]">
        {/* Left Column - Main Content */}
        <div className="space-y-12">
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

            <div className="mt-6 rounded-2xl border border-primary/20 bg-primary/5 p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">New here?</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    The app now includes a Help Center and a guided starter path. Follow the checklist below if you want the safest path to a first usable draft.
                  </p>
                </div>
                <Link
                  to="/help"
                  className="inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/70 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
                >
                  Open Help Center
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {gettingStartedSteps.slice(0, 3).map((step, index) => (
                  <div key={step.id} className="rounded-xl border border-border/50 bg-background/40 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Step {index + 1}</p>
                    <h4 className="mt-2 font-medium text-foreground">{step.title}</h4>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{step.description}</p>
                  </div>
                ))}
              </div>
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
                {statsData.drafts.slice(0, 6).map((draft: DraftMetadata) => (
                  <RecentDraftCard
                    id={draft.review_id}
                    to={`/drafts/${encodeURIComponent(draft.review_id)}`}
                    name={draft.character_name || draft.seed}
                    meta={`${draft.template_name || 'V2/V3 Card'} • ${draft.mode || 'SFW'}`}
                  />
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Right Column - Sidebar */}
        <aside className="space-y-8">
          {/* What's New */}
          <section>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-6 w-1 rounded-full bg-gradient-to-r from-primary to-accent" />
                <h2 className="text-xl font-bold text-foreground">What's New</h2>
              </div>
              <span className="rounded-full border border-border/60 bg-card/70 px-2.5 py-1 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                v{__APP_VERSION__}
              </span>
            </div>

            <div className="space-y-4">
              {releaseNotes.slice(0, 2).map((entry) => (
                <article
                  key={entry.version}
                  className="relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-slate-900/95 via-slate-900/90 to-slate-800/90 p-5"
                >
                  <div className="absolute -right-10 -top-10 h-36 w-36 rounded-full bg-primary/10 blur-3xl" />
                  <div className="relative space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
                        {entry.badge}
                      </span>
                      <span className="rounded-full border border-border/60 px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        v{entry.version}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-foreground">{entry.headline}</h3>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">{entry.summary}</p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {entry.links.slice(0, 2).map((link) => (
                        <Link
                          key={`${entry.version}-${link.to}`}
                          to={link.to}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-border/60 bg-card/70 px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
                        >
                          {link.label}
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                      ))}
                    </div>
                  </div>
                </article>
              ))}
            </div>

            <Link
              to="/whats-new"
              className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 hover:underline"
            >
              Full release history →
            </Link>
          </section>

          {/* Upcoming Updates */}
          <section className="rounded-2xl border border-border/50 bg-card/60 p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-foreground">Upcoming Updates</h3>
              <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                Planned
              </span>
            </div>

            <div className="space-y-3">
              {upcomingUpdates.map((update) => (
                <div
                  key={update.id}
                  className="rounded-xl border border-border/50 bg-background/30 p-3"
                >
                  <h4 className="font-medium text-foreground text-sm">{update.title}</h4>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{update.summary}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Guided Workflows */}
          <section className="rounded-2xl border border-dashed border-border/60 bg-card/40 p-5">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-foreground">Guided Workflows</h3>
                <p className="text-sm text-muted-foreground">
                  First-run guidance and automations.
                </p>
              </div>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                Live
              </span>
            </div>

            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-primary mb-2">
                <Target className="h-4 w-4" />
                Resume Help
              </div>
              <h4 className="font-semibold text-foreground">
                {activeTour && activeTourStep
                  ? `Continue ${activeTour.title}`
                  : nextIncompleteTour
                    ? `Next: ${nextIncompleteTour.title}`
                    : 'All tours complete'}
              </h4>
              <p className="mt-1 text-sm leading-5 text-muted-foreground">
                {activeTour && activeTourStep
                  ? `Step ${activeStepIndex + 1} of ${activeTour.steps.length}`
                  : nextIncompleteTour
                    ? nextIncompleteTour.summary
                    : 'You\'re caught up!'}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                {activeTour ? (
                  <button
                    type="button"
                    onClick={goToCurrentStep}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    <PlayCircle className="h-3.5 w-3.5" />
                    Resume
                  </button>
                ) : nextIncompleteTour ? (
                  <button
                    type="button"
                    onClick={() => startTour(nextIncompleteTour.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    <PlayCircle className="h-3.5 w-3.5" />
                    Start
                  </button>
                ) : null}

                {nextIncompleteTour && (
                  <button
                    type="button"
                    onClick={() => restartTour(nextIncompleteTour.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border/60 bg-background/50 px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    Restart
                  </button>
                )}
              </div>
            </div>

            <div className="mt-4 grid gap-3">
              <OnboardingPlaceholder templateName={templatesData?.[0]?.name} />
              <AutomationPlaceholder workflowName="draft validation queue" />
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
