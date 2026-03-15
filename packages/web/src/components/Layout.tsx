import { ReactNode, useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Sparkles,
  FolderOpen,
  FileText,
  GitCompare,
  Baby,
  GitBranch,
  Settings,
  Menu,
  X,
  Layers,
  BookOpen,
  Dice1,
  ShieldCheck,
  Palette,
  Scale,
  Info,
  CircleHelp,
} from 'lucide-react';
import { helpTopics, resolvePageHelp } from '../lib/help';
import { cn } from '../utils/cn';
import { AssistantContextProvider } from './common/AssistantContext';
import ContextualHelpPanel from './common/ContextualHelpPanel';
import GlobalAssistant from './common/GlobalAssistant';
import GuidedTourOverlay from './common/GuidedTourOverlay';
import { GuidedTourProvider } from './common/GuidedTourContext';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/generate', label: 'Generate', icon: Sparkles },
  { path: '/seed-generator', label: 'Seed Generator', icon: Dice1 },
  { path: '/validation', label: 'Validation', icon: ShieldCheck },
  { path: '/batch', label: 'Batch', icon: Layers },
  { path: '/drafts', label: 'Drafts', icon: FolderOpen },
  { path: '/templates', label: 'Templates', icon: FileText },
  { path: '/blueprints', label: 'Blueprints', icon: BookOpen },
  { path: '/similarity', label: 'Compare', icon: GitCompare },
  { path: '/offspring', label: 'Offspring', icon: Baby },
  { path: '/lineage', label: 'Lineage', icon: GitBranch },
  { path: '/themes', label: 'Theme Studio', icon: Palette },
  { path: '/settings', label: 'Settings', icon: Settings },
];

const footerLinks = [
  { path: '/about', label: 'About', icon: Info },
  { path: '/help', label: 'Help', icon: BookOpen },
  { path: '/whats-new', label: 'What\'s New', icon: Info },
  { path: '/terms', label: 'Terms', icon: Scale },
  { path: '/privacy', label: 'Privacy', icon: ShieldCheck },
  { path: '/license', label: 'License', icon: FileText },
  { path: '/security', label: 'Security', icon: ShieldCheck },
  { path: '/code-of-conduct', label: 'Conduct', icon: BookOpen },
];

interface NavItemProps {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  isActive: boolean;
  onClick: () => void;
}

function NavItem({ path, label, icon: Icon, isActive, onClick }: NavItemProps) {
  return (
    <Link
      to={path}
      onClick={onClick}
      className={cn(
        'group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200',
        isActive
          ? 'bg-gradient-to-r from-primary to-accent text-primary-foreground shadow-lg shadow-primary/20'
          : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
      )}
    >
      <Icon className={cn('h-5 w-5 transition-transform duration-200', isActive ? 'scale-110' : 'group-hover:scale-110')} />
      <span>{label}</span>
      {isActive && (
        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/20 to-accent/20 -z-10" />
      )}
    </Link>
  );
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const pageHelp = useMemo(() => resolvePageHelp(location.pathname), [location.pathname]);
  const relatedTopics = useMemo(
    () => helpTopics.filter((topic) => pageHelp?.relatedTopicIds.includes(topic.id)),
    [pageHelp]
  );

  useEffect(() => {
    setHelpOpen(false);
  }, [location.pathname]);

  return (
    <AssistantContextProvider>
      <GuidedTourProvider>
      <div className="flex min-h-dvh bg-background lg:h-screen">
        {/* Mobile sidebar backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={cn(
            'fixed inset-y-0 left-0 z-50 w-[min(20rem,calc(100vw-1rem))] max-w-[calc(100vw-1rem)] bg-card/80 backdrop-blur-md border-r border-border transition-transform duration-300 ease-out lg:static lg:w-72 lg:max-w-none lg:translate-x-0',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex h-dvh flex-col lg:h-full">
            {/* Logo */}
            <div className="flex h-16 items-center justify-between px-4 border-b border-border/50">
              <Link to="/" className="flex items-center gap-2" onClick={() => setSidebarOpen(false)}>
                <div className="p-2 rounded-lg bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-lg">Eidolon</span>
                  <span className="text-xs text-muted-foreground">Simulacra v{__APP_VERSION__}</span>
                </div>
              </Link>
              <button
                className="lg:hidden p-2 rounded-lg hover:bg-accent transition-colors"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto p-4 space-y-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <NavItem
                    key={item.path}
                    path={item.path}
                    label={item.label}
                    icon={item.icon}
                    isActive={isActive}
                    onClick={() => setSidebarOpen(false)}
                  />
                );
              })}
            </nav>

            <div className="border-t border-border/50 px-4 py-4">
              <div className="mb-3">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                  Support
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Back Eidolon Simulacra on Ko-fi.
                </p>
              </div>
              <div className="rounded-xl border border-border/60 bg-background/80 p-3 shadow-sm">
                <a
                  href="https://ko-fi.com/maeveoffae"
                  target="_blank"
                  rel="noreferrer"
                  className="flex w-full items-center justify-center rounded-lg bg-[#72a4f2] px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
                >
                  Support me on Ko-fi
                </a>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-border/50 p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Web • No backend required
                </p>
                <Link
                  to="/settings"
                  className="text-xs text-muted-foreground hover:text-primary transition-colors"
                >
                  Settings
                </Link>
              </div>
              <div className="mt-3 flex flex-wrap gap-x-3 gap-y-2 text-xs text-muted-foreground">
                {footerLinks.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className="hover:text-primary transition-colors"
                    onClick={() => setSidebarOpen(false)}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="min-w-0 flex-1 overflow-auto">
          {/* Mobile header */}
          <header className="flex h-16 items-center gap-3 border-b border-border/50 bg-card/50 backdrop-blur-md px-4 lg:hidden sticky top-0 z-30">
            <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-accent transition-colors">
              <Menu className="h-6 w-6" />
            </button>
            <span className="min-w-0 truncate font-semibold text-base sm:text-lg">Eidolon Simulacra</span>
            {pageHelp && (
              <button
                type="button"
                onClick={() => setHelpOpen(true)}
                className="ml-auto inline-flex items-center gap-2 rounded-lg border border-border/60 bg-background/50 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
              >
                <CircleHelp className="h-4 w-4" />
                Help
              </button>
            )}
          </header>

          {/* Page content */}
          <div className="p-6 lg:p-8">
            {pageHelp && (
              <section className="mb-6 hidden rounded-2xl border border-border/60 bg-card/60 p-4 backdrop-blur-sm lg:block">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Contextual Help</p>
                    <h2 className="mt-1 text-lg font-semibold text-foreground">{pageHelp.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{pageHelp.summary}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setHelpOpen(true)}
                    className="inline-flex items-center gap-2 rounded-lg border border-border/60 bg-background/50 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
                  >
                    <CircleHelp className="h-4 w-4" />
                    Open page help
                  </button>
                </div>
              </section>
            )}

            {children}
          </div>
        </main>
        {pageHelp && (
          <ContextualHelpPanel
            entry={pageHelp}
            topics={relatedTopics}
            isOpen={helpOpen}
            onClose={() => setHelpOpen(false)}
          />
        )}
        <GuidedTourOverlay />
        <GlobalAssistant />
      </div>
      </GuidedTourProvider>
    </AssistantContextProvider>
  );
}
