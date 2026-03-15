import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Copy,
  Download,
  Loader2,
  Palette,
  Pencil,
  Save,
  Trash2,
  Upload,
  Wand2,
} from 'lucide-react';
import type { ThemeColors, ThemePreset } from '@char-gen/shared';
import { api } from '@/lib/api';
import { EDITABLE_THEME_SECTIONS, resolveThemeColors } from '../../theme/theme';
import { saveDownload } from '../../utils/download';

interface ThemeDuplicateDraft {
  sourceName: string;
  newName: string;
  displayName: string;
  description: string;
  author: string;
  tags: string;
  basedOn: string;
}

interface ThemeRenameDraft {
  sourceName: string;
  newName: string;
  displayName: string;
}

interface ThemeMetadataDraft {
  sourceName: string;
  displayName: string;
  description: string;
  author: string;
  tags: string;
  basedOn: string;
}

interface ImportedThemePayload {
  name: string;
  displayName: string;
  description: string;
  author: string;
  tags: string[];
  basedOn: string;
  colors: ThemeColors;
}

interface ThemeImportDraft {
  file: File;
  imported: ImportedThemePayload;
  targetName: string;
  conflictTheme: ThemePresetRecord;
}

interface ThemeImportOptions {
  conflict_strategy?: 'reject' | 'rename' | 'overwrite';
  target_name?: string;
}

type ThemeSortMode = 'name-asc' | 'name-desc' | 'author-asc' | 'source';
type ThemeViewMode = 'comfortable' | 'compact';

type ThemePresetRecord = ThemePreset & {
  author: string;
  tags: string[];
  based_on: string;
};

type ThemeApi = typeof api & {
  exportTheme: (name: string) => Promise<{ blob: Blob; filename: string | null; contentType: string | null }>;
  importTheme: (file: File, options?: ThemeImportOptions) => Promise<ThemePreset>;
  createTheme: (request: {
    name: string;
    display_name: string;
    description?: string;
    author?: string;
    tags?: string[];
    based_on?: string;
    colors: ThemeColors;
  }) => Promise<ThemePreset>;
  updateTheme: (name: string, request: {
    display_name?: string;
    description?: string;
    author?: string;
    tags?: string[];
    based_on?: string;
    colors?: ThemeColors;
  }) => Promise<ThemePreset>;
  duplicateTheme: (name: string, request: {
    new_name: string;
    display_name?: string;
    description?: string;
    author?: string;
    tags?: string[];
    based_on?: string;
  }) => Promise<ThemePreset>;
  renameTheme: (name: string, request: { new_name: string; display_name?: string }) => Promise<ThemePreset>;
  deleteTheme: (name: string) => Promise<{ status: string; name: string }>;
};

const themeApi = api as ThemeApi;

async function readImportedThemePayload(file: File): Promise<ImportedThemePayload> {
  const raw = JSON.parse(await file.text()) as Record<string, unknown>;
  const payload = (raw.theme && typeof raw.theme === 'object' ? raw.theme : raw) as Record<string, unknown>;
  const name = typeof payload.name === 'string' ? payload.name.trim() : '';
  const displayNameValue = payload.display_name ?? payload.displayName;
  const displayName = typeof displayNameValue === 'string' ? displayNameValue.trim() : '';
  const description = typeof payload.description === 'string' ? payload.description : '';
  const author = typeof payload.author === 'string' ? payload.author : '';
  const tags = Array.isArray(payload.tags) ? payload.tags.map((tag) => String(tag).trim()).filter(Boolean) : [];
  const basedOnValue = payload.based_on ?? payload.basedOn;
  const basedOn = typeof basedOnValue === 'string' ? basedOnValue : '';
  const colors = payload.colors;

  if (!name || !displayName || !colors || typeof colors !== 'object') {
    throw new Error('Theme file is missing a valid name, display name, or colors payload.');
  }

  return { name, displayName, description, author, tags, basedOn, colors: colors as ThemeColors };
}

function parseTagInput(value: string): string[] {
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function sanitizeThemeName(name: string): string {
  return name.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '');
}

function buildUniqueThemeName(baseName: string, themes: ThemePreset[]): string {
  const sanitizedBase = sanitizeThemeName(baseName);
  const existing = new Set(themes.map((theme) => sanitizeThemeName(theme.name)));

  if (!existing.has(sanitizedBase)) {
    return sanitizedBase;
  }

  let index = 2;
  while (existing.has(`${sanitizedBase}_${index}`)) {
    index += 1;
  }

  return `${sanitizedBase}_${index}`;
}

const palettePreviewKeys: Array<keyof ThemeColors> = [
  'background',
  'surface',
  'accent',
  'highlight',
  'button',
  'tok_brackets',
];

function isHexColor(value: string): boolean {
  return /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(value.trim());
}

function renderColorValue(value: string) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="h-4 w-4 rounded-full border border-black/10"
        style={{ backgroundColor: isHexColor(value) ? value : 'transparent' }}
      />
      <span className="font-mono text-xs">{value}</span>
    </div>
  );
}

export default function Themes() {
  const queryClient = useQueryClient();
  const importInputId = 'theme-import-input';
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState<'all' | 'builtin' | 'custom'>('all');
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [sortMode, setSortMode] = useState<ThemeSortMode>('name-asc');
  const [viewMode, setViewMode] = useState<ThemeViewMode>('comfortable');
  const [newThemeName, setNewThemeName] = useState('');
  const [newThemeDisplayName, setNewThemeDisplayName] = useState('');
  const [newThemeDescription, setNewThemeDescription] = useState('');
  const [newThemeAuthor, setNewThemeAuthor] = useState('');
  const [newThemeTags, setNewThemeTags] = useState('');
  const [newThemeBasedOn, setNewThemeBasedOn] = useState('');
  const [duplicateDraft, setDuplicateDraft] = useState<ThemeDuplicateDraft | null>(null);
  const [renameDraft, setRenameDraft] = useState<ThemeRenameDraft | null>(null);
  const [metadataDraft, setMetadataDraft] = useState<ThemeMetadataDraft | null>(null);
  const [importDraft, setImportDraft] = useState<ThemeImportDraft | null>(null);

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  });

  const { data: themes = [], isLoading: themesLoading } = useQuery<ThemePresetRecord[]>({
    queryKey: ['themes'],
    queryFn: () => api.getThemes() as Promise<ThemePresetRecord[]>,
  });

  const activeTheme = useMemo(
    () => themes.find((theme) => theme.name === config?.theme_name) ?? themes[0],
    [themes, config?.theme_name]
  );

  const resolvedCurrentTheme = useMemo(
    () => resolveThemeColors(activeTheme, config?.theme),
    [activeTheme, config?.theme]
  );

  const importDiffSections = useMemo(() => {
    if (!importDraft) {
      return [];
    }

    return EDITABLE_THEME_SECTIONS.map((section) => {
      const changes = section.fields
        .map((field) => {
          const existingValue = importDraft.conflictTheme.colors[field.colorKey];
          const importedValue = importDraft.imported.colors[field.colorKey];

          if (existingValue === importedValue) {
            return null;
          }

          return {
            label: field.label,
            existingValue,
            importedValue,
          };
        })
        .filter((value): value is { label: string; existingValue: string; importedValue: string } => Boolean(value));

      return {
        title: section.title,
        changes,
      };
    }).filter((section) => section.changes.length > 0);
  }, [importDraft]);

  const importDiffCount = useMemo(
    () => importDiffSections.reduce((count, section) => count + section.changes.length, 0),
    [importDiffSections]
  );

  const invalidateThemeData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['themes'] }),
      queryClient.invalidateQueries({ queryKey: ['config'] }),
    ]);
  };

  const createMutation = useMutation({
    mutationFn: () => {
      if (!resolvedCurrentTheme) {
        throw new Error('No resolved theme available to save.');
      }

      return themeApi.createTheme({
        name: newThemeName,
        display_name: newThemeDisplayName,
        description: newThemeDescription,
        author: newThemeAuthor,
        tags: parseTagInput(newThemeTags),
        based_on: newThemeBasedOn,
        colors: resolvedCurrentTheme,
      });
    },
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Created reusable theme preset ${theme.display_name}.`);
      setError(null);
      setNewThemeName('');
      setNewThemeDisplayName('');
      setNewThemeDescription('');
      setNewThemeAuthor('');
      setNewThemeTags('');
      setNewThemeBasedOn('');
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to create theme');
      setNotice(null);
    },
  });

  const activateMutation = useMutation({
    mutationFn: (themeName: string) => api.updateConfig({ theme_name: themeName, theme: {} }),
    onSuccess: async () => {
      await invalidateThemeData();
      setNotice('Theme activated.');
      setError(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to activate theme');
      setNotice(null);
    },
  });

  const updateCurrentCustomMutation = useMutation({
    mutationFn: (themeName: string) => {
      if (!resolvedCurrentTheme) {
        throw new Error('No resolved theme available to save.');
      }
      return themeApi.updateTheme(themeName, { colors: resolvedCurrentTheme });
    },
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Updated ${theme.display_name} from the current active palette.`);
      setError(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to update theme');
      setNotice(null);
    },
  });

  const updateMetadataMutation = useMutation({
    mutationFn: (draft: ThemeMetadataDraft) => themeApi.updateTheme(draft.sourceName, {
      display_name: draft.displayName,
      description: draft.description,
      author: draft.author,
      tags: parseTagInput(draft.tags),
      based_on: draft.basedOn,
    }),
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Updated metadata for ${theme.display_name}.`);
      setError(null);
      setMetadataDraft(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to update theme metadata');
      setNotice(null);
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (draft: ThemeDuplicateDraft) => themeApi.duplicateTheme(draft.sourceName, {
      new_name: draft.newName,
      display_name: draft.displayName,
      description: draft.description,
      author: draft.author,
      tags: parseTagInput(draft.tags),
      based_on: draft.basedOn,
    }),
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Created duplicate preset ${theme.display_name}.`);
      setError(null);
      setDuplicateDraft(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to duplicate theme');
      setNotice(null);
    },
  });

  const renameMutation = useMutation({
    mutationFn: (draft: ThemeRenameDraft) => themeApi.renameTheme(draft.sourceName, {
      new_name: draft.newName,
      display_name: draft.displayName,
    }),
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Renamed theme to ${theme.display_name}.`);
      setError(null);
      setRenameDraft(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to rename theme');
      setNotice(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (themeName: string) => themeApi.deleteTheme(themeName),
    onSuccess: async (_, themeName) => {
      await invalidateThemeData();
      setNotice(`Deleted ${themeName}.`);
      setError(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to delete theme');
      setNotice(null);
    },
  });

  const exportMutation = useMutation({
    mutationFn: async (theme: ThemePreset) => {
      const download = await themeApi.exportTheme(theme.name);
      await saveDownload(download, `${theme.name}.theme.json`);
      return theme;
    },
    onSuccess: (theme) => {
      setNotice(`Exported ${theme.display_name}.`);
      setError(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to export theme');
      setNotice(null);
    },
  });

  const importMutation = useMutation({
    mutationFn: ({ file, options }: { file: File; options?: ThemeImportOptions }) => themeApi.importTheme(file, options),
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Imported theme preset ${theme.display_name}.`);
      setError(null);
      setImportDraft(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to import theme');
      setNotice(null);
    },
  });

  const builtInThemes = themes.filter((theme) => theme.is_builtin);
  const customThemes = themes.filter((theme) => !theme.is_builtin);

  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    themes.forEach((theme) => {
      theme.tags.forEach((tag) => tags.add(tag));
    });
    return Array.from(tags).sort((left, right) => left.localeCompare(right));
  }, [themes]);

  const availableAuthors = useMemo(() => {
    const authors = new Set<string>();
    themes.forEach((theme) => {
      if (theme.author.trim()) {
        authors.add(theme.author.trim());
      }
    });
    return Array.from(authors).sort((left, right) => left.localeCompare(right));
  }, [themes]);

  const filteredThemes = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    return themes.filter((theme) => {
      const matchesSource = sourceFilter === 'all'
        || (sourceFilter === 'builtin' && theme.is_builtin)
        || (sourceFilter === 'custom' && !theme.is_builtin);
      if (!matchesSource) {
        return false;
      }

      const matchesAuthor = selectedAuthor === 'all' || theme.author === selectedAuthor;
      if (!matchesAuthor) {
        return false;
      }

      const matchesTag = selectedTag === 'all' || theme.tags.includes(selectedTag);
      if (!matchesTag) {
        return false;
      }

      if (!normalizedQuery) {
        return true;
      }

      const haystack = [
        theme.name,
        theme.display_name,
        theme.description,
        theme.author,
        theme.based_on,
        ...theme.tags,
      ]
        .join(' ')
        .toLowerCase();

      return haystack.includes(normalizedQuery);
    });
  }, [themes, searchQuery, sourceFilter, selectedAuthor, selectedTag]);

  const sortedThemes = useMemo(() => {
    const themesToSort = [...filteredThemes];

    themesToSort.sort((left, right) => {
      if (sortMode === 'name-desc') {
        return right.display_name.localeCompare(left.display_name);
      }

      if (sortMode === 'author-asc') {
        const authorCompare = (left.author || 'zzzz').localeCompare(right.author || 'zzzz');
        if (authorCompare !== 0) {
          return authorCompare;
        }
        return left.display_name.localeCompare(right.display_name);
      }

      if (sortMode === 'source') {
        const sourceCompare = Number(left.is_builtin) - Number(right.is_builtin);
        if (sourceCompare !== 0) {
          return sourceCompare;
        }
        return left.display_name.localeCompare(right.display_name);
      }

      return left.display_name.localeCompare(right.display_name);
    });

    return themesToSort;
  }, [filteredThemes, sortMode]);

  const isBusy = createMutation.isPending || activateMutation.isPending || updateCurrentCustomMutation.isPending || updateMetadataMutation.isPending || duplicateMutation.isPending || renameMutation.isPending || deleteMutation.isPending || exportMutation.isPending || importMutation.isPending;

  const handleImportChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const imported = await readImportedThemePayload(file);
      const existingTheme = themes.find((theme) => sanitizeThemeName(theme.name) === sanitizeThemeName(imported.name));

      if (!existingTheme) {
        importMutation.mutate({ file });
      } else {
        setImportDraft({
          file,
          imported,
          conflictTheme: existingTheme,
          targetName: buildUniqueThemeName(imported.name, themes),
        });
        setError(null);
        setNotice(`Theme ${imported.displayName} conflicts with existing preset ${existingTheme.display_name}. Choose how to import it.`);
      }
    } catch (importError) {
      setError(importError instanceof Error ? importError.message : 'Failed to read theme file');
      setNotice(null);
      setImportDraft(null);
    }

    event.target.value = '';
  };

  if (configLoading || themesLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center gap-3 text-sm text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading theme manager...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="mb-2">
            <Link to="/settings" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4" />
              Back to settings
            </Link>
          </div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <Palette className="h-7 w-7 text-primary" />
            Theme Manager
          </h1>
          <p className="text-muted-foreground">
            Save the current palette as a reusable preset and manage custom themes for the web app and review surfaces.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label
            htmlFor={importInputId}
            className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent"
          >
            <Upload className="h-4 w-4" />
            Import preset
          </label>
          <input
            id={importInputId}
            type="file"
            accept="application/json"
            onChange={handleImportChange}
            className="hidden"
          />
          {activeTheme && (
            <div className="rounded-lg border border-border bg-card px-4 py-3 text-sm">
              <div className="font-medium">Active preset</div>
              <div className="text-muted-foreground">{activeTheme.display_name}</div>
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <section className="rounded-lg border border-border bg-card p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Save Current Theme as Preset</h2>
              <p className="text-sm text-muted-foreground">
                Creates a named custom preset from the current active theme plus any live overrides saved in settings.
              </p>
            </div>
            {activeTheme && !activeTheme.is_builtin && (
              <button
                type="button"
                onClick={() => updateCurrentCustomMutation.mutate(activeTheme.name)}
                disabled={isBusy || !resolvedCurrentTheme}
                className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
              >
                {updateCurrentCustomMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Update active custom theme
              </button>
            )}
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm">
              <span className="font-medium">Theme name</span>
              <input
                type="text"
                value={newThemeName}
                onChange={(event) => setNewThemeName(event.target.value)}
                placeholder="e.g. ember_night"
                className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            <label className="space-y-2 text-sm">
              <span className="font-medium">Display name</span>
              <input
                type="text"
                value={newThemeDisplayName}
                onChange={(event) => setNewThemeDisplayName(event.target.value)}
                placeholder="Ember Night"
                className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          </div>
          <label className="mt-4 block space-y-2 text-sm">
            <span className="font-medium">Description</span>
            <textarea
              value={newThemeDescription}
              onChange={(event) => setNewThemeDescription(event.target.value)}
              rows={3}
              placeholder="Warm preview theme tuned for long review sessions."
              className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm">
              <span className="font-medium">Author</span>
              <input
                type="text"
                value={newThemeAuthor}
                onChange={(event) => setNewThemeAuthor(event.target.value)}
                placeholder="e.g. Nyx"
                className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            <label className="space-y-2 text-sm">
              <span className="font-medium">Based on</span>
              <input
                type="text"
                value={newThemeBasedOn}
                onChange={(event) => setNewThemeBasedOn(event.target.value)}
                placeholder="e.g. dark"
                className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          </div>
          <label className="mt-4 block space-y-2 text-sm">
            <span className="font-medium">Tags</span>
            <input
              type="text"
              value={newThemeTags}
              onChange={(event) => setNewThemeTags(event.target.value)}
              placeholder="warm, editorial, night"
              className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>

          {resolvedCurrentTheme && (
            <div className="mt-4 rounded-lg border border-border bg-background/60 p-4">
              <div className="text-sm font-medium">Current palette preview</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  resolvedCurrentTheme.background,
                  resolvedCurrentTheme.surface,
                  resolvedCurrentTheme.accent,
                  resolvedCurrentTheme.button,
                  resolvedCurrentTheme.tok_brackets,
                  resolvedCurrentTheme.highlight,
                ].map((color) => (
                  <span key={color} className="h-8 w-8 rounded-full border border-black/10" style={{ backgroundColor: color }} />
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => createMutation.mutate()}
              disabled={isBusy || !newThemeName.trim() || !newThemeDisplayName.trim() || !resolvedCurrentTheme}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
              Save custom preset
            </button>
          </div>
        </section>

        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="text-lg font-semibold">Preset Summary</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-lg border border-border bg-background/60 p-4">
              <div className="text-2xl font-bold text-primary">{builtInThemes.length}</div>
              <div className="text-sm text-muted-foreground">Built-in themes</div>
            </div>
            <div className="rounded-lg border border-border bg-background/60 p-4">
              <div className="text-2xl font-bold text-primary">{customThemes.length}</div>
              <div className="text-sm text-muted-foreground">Custom themes</div>
            </div>
          </div>
        </section>
      </div>

      {(notice || error) && (
        <div className={`rounded-md border px-3 py-2 text-sm ${error ? 'border-destructive/40 bg-destructive/10 text-destructive' : 'border-primary/30 bg-primary/10 text-foreground'}`}>
          {error || notice}
        </div>
      )}

      {importDraft && (
        <section className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="flex items-center gap-2 text-lg font-semibold">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Import conflict detected
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {importDraft.imported.displayName} wants to use the preset name {sanitizeThemeName(importDraft.imported.name)}, which already exists as {importDraft.conflictTheme.display_name}.
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                {importDiffCount === 0 ? 'The palettes are identical.' : `${importDiffCount} palette values differ across the imported and existing presets.`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setImportDraft(null)}
              className="rounded-md border border-input px-3 py-2 text-sm hover:bg-accent"
            >
              Dismiss
            </button>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <div className="rounded-lg border border-border bg-background/60 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">Existing preset</div>
                  <div className="text-xs text-muted-foreground">{importDraft.conflictTheme.display_name}</div>
                </div>
                <div className="text-right text-xs text-muted-foreground">{importDraft.conflictTheme.name}</div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {palettePreviewKeys.map((key) => (
                  <span key={`existing-${key}`} className="h-8 w-8 rounded-full border border-black/10" style={{ backgroundColor: importDraft.conflictTheme.colors[key] }} />
                ))}
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                {importDraft.conflictTheme.description || 'No description'}
              </div>
              {(importDraft.conflictTheme.author || importDraft.conflictTheme.based_on || importDraft.conflictTheme.tags.length > 0) && (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  {importDraft.conflictTheme.author && <div>Author: {importDraft.conflictTheme.author}</div>}
                  {importDraft.conflictTheme.based_on && <div>Based on: {importDraft.conflictTheme.based_on}</div>}
                  {importDraft.conflictTheme.tags.length > 0 && <div>Tags: {importDraft.conflictTheme.tags.join(', ')}</div>}
                </div>
              )}
            </div>

            <div className="rounded-lg border border-border bg-background/60 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">Imported preset</div>
                  <div className="text-xs text-muted-foreground">{importDraft.imported.displayName}</div>
                </div>
                <div className="text-right text-xs text-muted-foreground">{sanitizeThemeName(importDraft.imported.name)}</div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {palettePreviewKeys.map((key) => (
                  <span key={`imported-${key}`} className="h-8 w-8 rounded-full border border-black/10" style={{ backgroundColor: importDraft.imported.colors[key] }} />
                ))}
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                {importDraft.imported.description || 'No description'}
              </div>
              {(importDraft.imported.author || importDraft.imported.basedOn || importDraft.imported.tags.length > 0) && (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  {importDraft.imported.author && <div>Author: {importDraft.imported.author}</div>}
                  {importDraft.imported.basedOn && <div>Based on: {importDraft.imported.basedOn}</div>}
                  {importDraft.imported.tags.length > 0 && <div>Tags: {importDraft.imported.tags.join(', ')}</div>}
                </div>
              )}
            </div>
          </div>

          {importDiffSections.length > 0 && (
            <div className="mt-4 rounded-lg border border-border bg-background/60 p-4">
              <div className="text-sm font-medium">Palette diff</div>
              <div className="mt-3 space-y-4">
                {importDiffSections.map((section) => (
                  <div key={section.title}>
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{section.title}</div>
                    <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)]">
                      <div className="text-xs font-medium text-muted-foreground">Field</div>
                      <div className="text-xs font-medium text-muted-foreground">Existing</div>
                      <div className="text-xs font-medium text-muted-foreground">Imported</div>
                      {section.changes.map((change) => (
                        <>
                          <div key={`${section.title}-${change.label}-label`} className="rounded-md border border-border px-3 py-2 text-sm">
                            {change.label}
                          </div>
                          <div key={`${section.title}-${change.label}-existing`} className="rounded-md border border-border px-3 py-2">
                            {renderColorValue(change.existingValue)}
                          </div>
                          <div key={`${section.title}-${change.label}-imported`} className="rounded-md border border-border px-3 py-2">
                            {renderColorValue(change.importedValue)}
                          </div>
                        </>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 grid gap-4 lg:grid-cols-[auto_1fr]">
            {!importDraft.conflictTheme.is_builtin && (
              <button
                type="button"
                onClick={() => importMutation.mutate({
                  file: importDraft.file,
                  options: {
                    conflict_strategy: 'overwrite',
                    target_name: importDraft.conflictTheme.name,
                  },
                })}
                disabled={importMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md border border-input px-4 py-2 text-sm hover:bg-accent disabled:opacity-50"
              >
                {importMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Overwrite existing custom preset
              </button>
            )}

            <div className="rounded-lg border border-border bg-background/60 p-4">
              <div className="text-sm font-medium">Import as new preset</div>
              <p className="mt-1 text-sm text-muted-foreground">
                Built-in presets cannot be overwritten. Rename the imported preset and keep both versions.
              </p>
              <div className="mt-3 flex flex-wrap gap-3">
                <input
                  type="text"
                  value={importDraft.targetName}
                  onChange={(event) => setImportDraft({ ...importDraft, targetName: event.target.value })}
                  placeholder="new preset name"
                  className="min-w-[220px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
                <button
                  type="button"
                  onClick={() => importMutation.mutate({
                    file: importDraft.file,
                    options: {
                      conflict_strategy: 'rename',
                      target_name: importDraft.targetName,
                    },
                  })}
                  disabled={importMutation.isPending || !importDraft.targetName.trim()}
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {importMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  Import renamed preset
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Available Themes</h2>
          <p className="text-sm text-muted-foreground">
            Built-in themes are read-only. Custom themes can be renamed, duplicated, activated, updated, and deleted.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
            <label className="space-y-2 text-sm">
              <span className="font-medium">Search presets</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search by name, author, tag, lineage, or description"
                className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            <div className="space-y-2 text-sm">
              <div className="font-medium">Filter by source</div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSourceFilter('all')}
                  className={`rounded-full border px-3 py-1.5 text-xs ${sourceFilter === 'all' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                >
                  All presets
                </button>
                <button
                  type="button"
                  onClick={() => setSourceFilter('builtin')}
                  className={`rounded-full border px-3 py-1.5 text-xs ${sourceFilter === 'builtin' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                >
                  Built-in
                </button>
                <button
                  type="button"
                  onClick={() => setSourceFilter('custom')}
                  className={`rounded-full border px-3 py-1.5 text-xs ${sourceFilter === 'custom' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                >
                  Custom
                </button>
              </div>
            </div>
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px]">
            <div className="space-y-2 text-sm">
              <div className="font-medium">Filter by author</div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedAuthor('all')}
                  className={`rounded-full border px-3 py-1.5 text-xs ${selectedAuthor === 'all' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                >
                  All authors
                </button>
                {availableAuthors.map((author) => (
                  <button
                    key={author}
                    type="button"
                    onClick={() => setSelectedAuthor(author)}
                    className={`rounded-full border px-3 py-1.5 text-xs ${selectedAuthor === author ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                  >
                    {author}
                  </button>
                ))}
                {availableAuthors.length === 0 && (
                  <div className="text-xs text-muted-foreground">No authors yet</div>
                )}
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <div className="font-medium">Filter by tag</div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedTag('all')}
                  className={`rounded-full border px-3 py-1.5 text-xs ${selectedTag === 'all' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                >
                  All tags
                </button>
                {availableTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => setSelectedTag(tag)}
                    className={`rounded-full border px-3 py-1.5 text-xs ${selectedTag === tag ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                  >
                    {tag}
                  </button>
                ))}
                {availableTags.length === 0 && (
                  <div className="text-xs text-muted-foreground">No tags yet</div>
                )}
              </div>
            </div>
            <div className="space-y-4">
              <label className="space-y-2 text-sm">
                <span className="font-medium">Sort presets</span>
                <select
                  value={sortMode}
                  onChange={(event) => setSortMode(event.target.value as ThemeSortMode)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="name-asc">Name A-Z</option>
                  <option value="name-desc">Name Z-A</option>
                  <option value="author-asc">Author</option>
                  <option value="source">Source</option>
                </select>
              </label>
              <div className="space-y-2 text-sm">
                <div className="font-medium">View mode</div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setViewMode('comfortable')}
                    className={`rounded-md border px-3 py-2 text-xs ${viewMode === 'comfortable' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                  >
                    Comfortable
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('compact')}
                    className={`rounded-md border px-3 py-2 text-xs ${viewMode === 'compact' ? 'border-primary bg-primary text-primary-foreground' : 'border-input hover:bg-accent'}`}
                  >
                    Compact
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-3 text-xs text-muted-foreground">
            Showing {sortedThemes.length} of {themes.length} presets.
          </div>
        </div>

        {sortedThemes.length === 0 && (
          <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center text-sm text-muted-foreground">
            No themes match the current search and tag filters.
          </div>
        )}

        <div className={`grid gap-4 ${viewMode === 'compact' ? 'lg:grid-cols-2 xl:grid-cols-3' : 'lg:grid-cols-2'}`}>
          {sortedThemes.map((theme) => {
            const isActive = config?.theme_name === theme.name;
            const isCustom = !theme.is_builtin;
            const isDuplicating = duplicateDraft?.sourceName === theme.name;
            const isRenaming = renameDraft?.sourceName === theme.name;
            const isEditingMetadata = metadataDraft?.sourceName === theme.name;
            const isCompact = viewMode === 'compact';
            const actionButtonClass = isCompact
              ? 'inline-flex items-center gap-1.5 rounded-md border border-input px-2 py-1.5 text-xs hover:bg-accent disabled:opacity-50'
              : 'inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent disabled:opacity-50';

            return (
              <div key={theme.name} className={`rounded-lg border bg-card ${isCompact ? 'p-3' : 'p-4'} ${isActive ? 'border-primary' : 'border-border'}`}>
                <div className={`flex ${isCompact ? 'flex-col gap-3' : 'items-start justify-between gap-4'}`}>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{theme.display_name}</h3>
                      {isActive && <CheckCircle className="h-4 w-4 text-primary" />}
                    </div>
                    <div className="text-xs text-muted-foreground">{theme.name}</div>
                    {isCompact ? (
                      <>
                        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                          <span className="rounded-full border border-border px-2 py-0.5">{theme.is_builtin ? 'Built-in' : 'Custom'}</span>
                          {theme.author && <span>By {theme.author}</span>}
                        </div>
                        {theme.tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {theme.tags.slice(0, 3).map((tag) => (
                              <span key={`${theme.name}-${tag}`} className="rounded-full border border-border px-2 py-0.5 text-[11px] text-muted-foreground">
                                {tag}
                              </span>
                            ))}
                            {theme.tags.length > 3 && (
                              <span className="text-[11px] text-muted-foreground">+{theme.tags.length - 3} more</span>
                            )}
                          </div>
                        )}
                      </>
                    ) : (
                      <>
                        <p className="mt-2 text-sm text-muted-foreground">{theme.description || 'No description'}</p>
                        {(theme.author || theme.based_on || theme.tags.length > 0) && (
                          <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                            {theme.author && <div>Author: {theme.author}</div>}
                            {theme.based_on && <div>Based on: {theme.based_on}</div>}
                            {theme.tags.length > 0 && <div>Tags: {theme.tags.join(', ')}</div>}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {[theme.colors.background, theme.colors.surface, theme.colors.accent, theme.colors.button].map((color) => (
                      <span key={`${theme.name}-${color}`} className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} rounded-full border border-black/10`} style={{ backgroundColor: color }} />
                    ))}
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => activateMutation.mutate(theme.name)}
                    disabled={isBusy}
                    className={actionButtonClass}
                  >
                    <Palette className="h-4 w-4" />
                    Activate
                  </button>
                  <button
                    type="button"
                    onClick={() => exportMutation.mutate(theme)}
                    disabled={isBusy}
                    className={actionButtonClass}
                  >
                    <Download className="h-4 w-4" />
                    Export
                  </button>
                  <button
                    type="button"
                    onClick={() => setDuplicateDraft({
                      sourceName: theme.name,
                      newName: `${theme.name}_copy`,
                      displayName: `${theme.display_name} Copy`,
                      description: theme.description,
                      author: theme.author,
                      tags: theme.tags.join(', '),
                      basedOn: theme.based_on,
                    })}
                    disabled={isBusy}
                    className={actionButtonClass}
                  >
                    <Copy className="h-4 w-4" />
                    Duplicate
                  </button>
                  {isCustom && (
                    <>
                      <button
                        type="button"
                        onClick={() => setMetadataDraft({
                          sourceName: theme.name,
                          displayName: theme.display_name,
                          description: theme.description,
                          author: theme.author,
                          tags: theme.tags.join(', '),
                          basedOn: theme.based_on,
                        })}
                        disabled={isBusy}
                        className={actionButtonClass}
                      >
                        <Pencil className="h-4 w-4" />
                        Edit details
                      </button>
                      <button
                        type="button"
                        onClick={() => setRenameDraft({
                          sourceName: theme.name,
                          newName: theme.name,
                          displayName: theme.display_name,
                        })}
                        disabled={isBusy}
                        className={actionButtonClass}
                      >
                        <Pencil className="h-4 w-4" />
                        Rename
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (window.confirm(`Delete theme ${theme.display_name}?`)) {
                            deleteMutation.mutate(theme.name);
                          }
                        }}
                        disabled={isBusy}
                        className={`${isCompact ? 'inline-flex items-center gap-1.5 rounded-md border border-destructive/40 px-2 py-1.5 text-xs text-destructive hover:bg-destructive/10 disabled:opacity-50' : 'inline-flex items-center gap-2 rounded-md border border-destructive/40 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 disabled:opacity-50'}`}
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete
                      </button>
                    </>
                  )}
                </div>

                {isEditingMetadata && metadataDraft && (
                  <div className="mt-4 space-y-3 rounded-lg border border-border bg-background/60 p-3">
                    <div className="text-sm font-medium">Edit Theme Details</div>
                    <div className="grid gap-3 md:grid-cols-2">
                      <input
                        type="text"
                        value={metadataDraft.displayName}
                        onChange={(event) => setMetadataDraft({ ...metadataDraft, displayName: event.target.value })}
                        placeholder="display name"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        value={metadataDraft.author}
                        onChange={(event) => setMetadataDraft({ ...metadataDraft, author: event.target.value })}
                        placeholder="author"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                    <textarea
                      value={metadataDraft.description}
                      onChange={(event) => setMetadataDraft({ ...metadataDraft, description: event.target.value })}
                      rows={2}
                      placeholder="description"
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                    <div className="grid gap-3 md:grid-cols-2">
                      <input
                        type="text"
                        value={metadataDraft.basedOn}
                        onChange={(event) => setMetadataDraft({ ...metadataDraft, basedOn: event.target.value })}
                        placeholder="based on"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        value={metadataDraft.tags}
                        onChange={(event) => setMetadataDraft({ ...metadataDraft, tags: event.target.value })}
                        placeholder="warm, editorial, night"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setMetadataDraft(null)}
                        className="rounded-md border border-input px-3 py-2 text-sm hover:bg-accent"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => updateMetadataMutation.mutate(metadataDraft)}
                        disabled={updateMetadataMutation.isPending || !metadataDraft.displayName.trim()}
                        className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                      >
                        {updateMetadataMutation.isPending ? 'Saving...' : 'Save details'}
                      </button>
                    </div>
                  </div>
                )}

                {isDuplicating && duplicateDraft && (
                  <div className="mt-4 space-y-3 rounded-lg border border-border bg-background/60 p-3">
                    <div className="text-sm font-medium">Duplicate Theme</div>
                    <div className="grid gap-3 md:grid-cols-2">
                      <input
                        type="text"
                        value={duplicateDraft.newName}
                        onChange={(event) => setDuplicateDraft({ ...duplicateDraft, newName: event.target.value })}
                        placeholder="theme name"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        value={duplicateDraft.displayName}
                        onChange={(event) => setDuplicateDraft({ ...duplicateDraft, displayName: event.target.value })}
                        placeholder="display name"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                    <textarea
                      value={duplicateDraft.description}
                      onChange={(event) => setDuplicateDraft({ ...duplicateDraft, description: event.target.value })}
                      rows={2}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                    <div className="grid gap-3 md:grid-cols-2">
                      <input
                        type="text"
                        value={duplicateDraft.author}
                        onChange={(event) => setDuplicateDraft({ ...duplicateDraft, author: event.target.value })}
                        placeholder="author"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        value={duplicateDraft.basedOn}
                        onChange={(event) => setDuplicateDraft({ ...duplicateDraft, basedOn: event.target.value })}
                        placeholder="based on"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                    <input
                      type="text"
                      value={duplicateDraft.tags}
                      onChange={(event) => setDuplicateDraft({ ...duplicateDraft, tags: event.target.value })}
                      placeholder="warm, editorial, night"
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                    <div className="flex justify-end gap-2">
                      <button type="button" onClick={() => setDuplicateDraft(null)} className="rounded-md border border-input px-3 py-2 text-sm hover:bg-accent">
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => duplicateMutation.mutate(duplicateDraft)}
                        disabled={duplicateMutation.isPending || !duplicateDraft.newName.trim() || !duplicateDraft.displayName.trim()}
                        className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                      >
                        {duplicateMutation.isPending ? 'Duplicating...' : 'Create copy'}
                      </button>
                    </div>
                  </div>
                )}

                {isRenaming && renameDraft && (
                  <div className="mt-4 space-y-3 rounded-lg border border-border bg-background/60 p-3">
                    <div className="text-sm font-medium">Rename Theme</div>
                    <div className="grid gap-3 md:grid-cols-2">
                      <input
                        type="text"
                        value={renameDraft.newName}
                        onChange={(event) => setRenameDraft({ ...renameDraft, newName: event.target.value })}
                        placeholder="theme name"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        value={renameDraft.displayName}
                        onChange={(event) => setRenameDraft({ ...renameDraft, displayName: event.target.value })}
                        placeholder="display name"
                        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <button type="button" onClick={() => setRenameDraft(null)} className="rounded-md border border-input px-3 py-2 text-sm hover:bg-accent">
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => renameMutation.mutate(renameDraft)}
                        disabled={renameMutation.isPending || !renameDraft.newName.trim() || !renameDraft.displayName.trim()}
                        className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                      >
                        {renameMutation.isPending ? 'Renaming...' : 'Rename'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
