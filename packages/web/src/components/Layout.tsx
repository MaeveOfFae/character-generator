import { ReactNode } from 'react';
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
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '../utils/cn';
import { AssistantContextProvider } from './common/AssistantContext';
import GlobalAssistant from './common/GlobalAssistant';

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

  return (
    <AssistantContextProvider>
      <div className="flex h-screen overflow-hidden bg-background">
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
            'fixed inset-y-0 left-0 z-50 w-72 bg-card/80 backdrop-blur-md border-r border-border transition-transform duration-300 ease-out lg:static lg:translate-x-0',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex h-full flex-col">
            {/* Logo */}
            <div className="flex h-16 items-center justify-between px-4 border-b border-border/50">
              <Link to="/" className="flex items-center gap-2" onClick={() => setSidebarOpen(false)}>
                <div className="p-2 rounded-lg bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-lg">CharGen</span>
                  <span className="text-xs text-muted-foreground">v2.0</span>
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
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          {/* Mobile header */}
          <header className="flex h-16 items-center gap-3 border-b border-border/50 bg-card/50 backdrop-blur-md px-4 lg:hidden sticky top-0 z-30">
            <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-accent transition-colors">
              <Menu className="h-6 w-6" />
            </button>
            <span className="font-semibold text-lg">Eidolon Simulacra</span>
          </header>

          {/* Page content */}
          <div className="p-6 lg:p-8 max-w-6xl mx-auto">{children}</div>
        </main>
        <GlobalAssistant />
      </div>
    </AssistantContextProvider>
  );
}
