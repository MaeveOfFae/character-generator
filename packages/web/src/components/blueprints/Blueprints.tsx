import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { BookOpen, FileJson, Lightbulb, Package, Search, ArrowRight } from 'lucide-react';
import type { Blueprint } from '@char-gen/shared';
import { api } from '@/lib/api';
import { useAssistantScreenContext } from '../common/AssistantContext';
import BlueprintLintPlaceholder from './BlueprintLintPlaceholder';
import BlueprintSandboxPlaceholder from './BlueprintSandboxPlaceholder';

type Section = {
  title: string;
  blueprints: Blueprint[];
  icon: React.ReactNode;
};

export default function Blueprints() {
  const [query, setQuery] = useState('');
  const { data, isLoading, error } = useQuery({
    queryKey: ['blueprints'],
    queryFn: () => api.getBlueprints(),
  });

  const sections = useMemo<Section[]>(() => {
    if (!data) {
      return [];
    }

    return [
      { title: 'Core Blueprints', blueprints: data.core, icon: <BookOpen className="h-5 w-5 text-primary" /> },
      { title: 'System Blueprints', blueprints: data.system, icon: <FileJson className="h-5 w-5 text-primary" /> },
      {
        title: 'Template Blueprints',
        blueprints: Object.values(data.templates).flat(),
        icon: <Package className="h-5 w-5 text-primary" />,
      },
      { title: 'Example Blueprints', blueprints: data.examples, icon: <Lightbulb className="h-5 w-5 text-primary" /> },
    ];
  }, [data]);

  const normalizedQuery = query.trim().toLowerCase();
  const filteredSections = sections
    .map((section) => ({
      ...section,
      blueprints: section.blueprints.filter((blueprint) => {
        if (!normalizedQuery) {
          return true;
        }
        return (
          blueprint.name.toLowerCase().includes(normalizedQuery) ||
          blueprint.description.toLowerCase().includes(normalizedQuery) ||
          blueprint.path.toLowerCase().includes(normalizedQuery)
        );
      }),
    }))
    .filter((section) => section.blueprints.length > 0);

  const highlightedBlueprint = filteredSections[0]?.blueprints[0] ?? sections[0]?.blueprints[0];

  useAssistantScreenContext({
    search_query: query,
    visible_sections: filteredSections.map((section) => section.title),
    total_visible_blueprints: filteredSections.reduce((count, section) => count + section.blueprints.length, 0),
    total_blueprints: sections.reduce((count, section) => count + section.blueprints.length, 0),
  });

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center text-muted-foreground">Loading blueprints...</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
        Error loading blueprints: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Blueprints</h1>
          <p className="text-muted-foreground">
            Browse and edit blueprint files used by templates and generation flows.
          </p>
        </div>
      </div>

      <div className="relative max-w-xl">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search blueprints by name, description, or path"
          className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      <section className="rounded-lg border border-dashed border-border bg-card/50 p-5">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Blueprint Tools</h2>
            <p className="text-sm text-muted-foreground">
              Linting and sandbox preview are available now for fast browser-only blueprint checks.
            </p>
          </div>
          <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">
            Live
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <BlueprintLintPlaceholder blueprintPath={highlightedBlueprint?.path} />
          <BlueprintSandboxPlaceholder
            blueprintPath={highlightedBlueprint?.path}
            seed={normalizedQuery || 'preview seed'}
          />
        </div>
      </section>

      {filteredSections.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
          No blueprints match the current search.
        </div>
      ) : (
        <div className="space-y-6">
          {filteredSections.map((section) => (
            <section key={section.title} className="space-y-3">
              <div className="flex items-center gap-2">
                {section.icon}
                <h2 className="text-lg font-semibold">{section.title}</h2>
                <span className="text-sm text-muted-foreground">{section.blueprints.length}</span>
              </div>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {section.blueprints.map((blueprint) => (
                  <Link
                    key={blueprint.path}
                    to={`/blueprints/edit/${encodeURIComponent(blueprint.path)}`}
                    className="group rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary hover:bg-accent/30"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium">{blueprint.name}</h3>
                        <p className="mt-1 text-sm text-muted-foreground">{blueprint.description || 'No description'}</p>
                      </div>
                      <ArrowRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1" />
                    </div>
                    <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{blueprint.path}</span>
                      <span>v{blueprint.version}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}