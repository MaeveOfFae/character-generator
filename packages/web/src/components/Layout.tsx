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
  Dices,
  ShieldCheck,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/utils/cn';
import { AssistantContextProvider } from './common/AssistantContext';
import GlobalAssistant from './common/GlobalAssistant';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/generate', label: 'Generate', icon: Sparkles },
  { path: '/seed-generator', label: 'Seed Generator', icon: Dices },
  { path: '/validation', label: 'Validation', icon: ShieldCheck },
  { path: '/batch', label: 'Batch', icon: Layers },
  { path: '/drafts', label: 'Drafts', icon: FolderOpen },
  { path: '/templates', label: 'Templates', icon: FileText },
  { path: '/blueprints', label: 'Blueprints', icon: BookOpen },
  { path: '/similarity', label: 'Compare', icon: GitCompare },
  { path: '/offspring', label: 'Offspring', icon: Baby },
  { path: '/lineage', label: 'Lineage', icon: GitBranch },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <AssistantContextProvider>
      <div className="flex h-screen overflow-hidden">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-card border-r border-border transition-transform duration-200 ease-in-out lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-border">
            <Link to="/" className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <span className="font-semibold text-lg">CharGen</span>
            </Link>
            <button
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-border p-4">
            <p className="text-xs text-muted-foreground">
              Character Generator v2.0
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {/* Mobile header */}
        <header className="flex h-16 items-center gap-4 border-b border-border px-4 lg:hidden">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>
          <span className="font-semibold">Character Generator</span>
        </header>

        {/* Page content */}
        <div className="p-6">{children}</div>
      </main>
        <GlobalAssistant />
      </div>
    </AssistantContextProvider>
  );
}
