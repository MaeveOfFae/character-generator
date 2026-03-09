import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  CheckCircle,
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
import { api, type ThemeColors, type ThemePreset } from '@char-gen/shared';
import { resolveThemeColors } from '../../theme/theme';
import { saveDownload } from '../../utils/download';

interface ThemeActionDraft {
  sourceName: string;
  newName: string;
  displayName: string;
  description: string;
}

type ThemeApi = typeof api & {
  exportTheme: (name: string) => Promise<{ blob: Blob; filename: string | null; contentType: string | null }>;
  importTheme: (file: File) => Promise<ThemePreset>;
  createTheme: (request: {
    name: string;
    display_name: string;
    description?: string;
    colors: ThemeColors;
  }) => Promise<ThemePreset>;
  updateTheme: (name: string, request: { colors?: ThemeColors }) => Promise<ThemePreset>;
  duplicateTheme: (name: string, request: {
    new_name: string;
    display_name?: string;
    description?: string;
  }) => Promise<ThemePreset>;
  renameTheme: (name: string, request: { new_name: string; display_name?: string }) => Promise<ThemePreset>;
  deleteTheme: (name: string) => Promise<{ status: string; name: string }>;
};

const themeApi = api as ThemeApi;

export default function Themes() {
  const queryClient = useQueryClient();
  const importInputId = 'theme-import-input';
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newThemeName, setNewThemeName] = useState('');
  const [newThemeDisplayName, setNewThemeDisplayName] = useState('');
  const [newThemeDescription, setNewThemeDescription] = useState('');
  const [duplicateDraft, setDuplicateDraft] = useState<ThemeActionDraft | null>(null);
  const [renameDraft, setRenameDraft] = useState<Omit<ThemeActionDraft, 'description'> | null>(null);

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  });

  const { data: themes = [], isLoading: themesLoading } = useQuery({
    queryKey: ['themes'],
    queryFn: () => api.getThemes(),
  });

  const activeTheme = useMemo(
    () => themes.find((theme) => theme.name === config?.theme_name) ?? themes[0],
    [themes, config?.theme_name]
  );

  const resolvedCurrentTheme = useMemo(
    () => resolveThemeColors(activeTheme, config?.theme),
    [activeTheme, config?.theme]
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

  const duplicateMutation = useMutation({
    mutationFn: (draft: ThemeActionDraft) => themeApi.duplicateTheme(draft.sourceName, {
      new_name: draft.newName,
      display_name: draft.displayName,
      description: draft.description,
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
    mutationFn: (draft: Omit<ThemeActionDraft, 'description'>) => themeApi.renameTheme(draft.sourceName, {
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
    mutationFn: (file: File) => themeApi.importTheme(file),
    onSuccess: async (theme) => {
      await invalidateThemeData();
      setNotice(`Imported theme preset ${theme.display_name}.`);
      setError(null);
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to import theme');
      setNotice(null);
    },
  });

  const builtInThemes = themes.filter((theme) => theme.is_builtin);
  const customThemes = themes.filter((theme) => !theme.is_builtin);

  const isBusy = createMutation.isPending || activateMutation.isPending || updateCurrentCustomMutation.isPending || duplicateMutation.isPending || renameMutation.isPending || deleteMutation.isPending || exportMutation.isPending || importMutation.isPending;

  const handleImportChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    importMutation.mutate(file);
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
    <div className="mx-auto max-w-6xl space-y-6">
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
            Save the current palette as a reusable preset and manage custom themes for web and TUI surfaces.
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

          {resolvedCurrentTheme && (
            <div className="mt-4 rounded-lg border border-border bg-background/60 p-4">
              <div className="text-sm font-medium">Current palette preview</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  resolvedCurrentTheme.background,
                  resolvedCurrentTheme.surface,
                  resolvedCurrentTheme.accent,
                  resolvedCurrentTheme.tui_primary,
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

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Available Themes</h2>
          <p className="text-sm text-muted-foreground">
            Built-in themes are read-only. Custom themes can be renamed, duplicated, activated, updated, and deleted.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {themes.map((theme) => {
            const isActive = config?.theme_name === theme.name;
            const isCustom = !theme.is_builtin;
            const isDuplicating = duplicateDraft?.sourceName === theme.name;
            const isRenaming = renameDraft?.sourceName === theme.name;

            return (
              <div key={theme.name} className={`rounded-lg border bg-card p-4 ${isActive ? 'border-primary' : 'border-border'}`}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{theme.display_name}</h3>
                      {isActive && <CheckCircle className="h-4 w-4 text-primary" />}
                    </div>
                    <div className="text-xs text-muted-foreground">{theme.name}</div>
                    <p className="mt-2 text-sm text-muted-foreground">{theme.description || 'No description'}</p>
                  </div>
                  <div className="flex gap-2">
                    {[theme.colors.background, theme.colors.surface, theme.colors.accent, theme.colors.tui_primary].map((color) => (
                      <span key={`${theme.name}-${color}`} className="h-6 w-6 rounded-full border border-black/10" style={{ backgroundColor: color }} />
                    ))}
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => activateMutation.mutate(theme.name)}
                    disabled={isBusy}
                    className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
                  >
                    <Palette className="h-4 w-4" />
                    Activate
                  </button>
                  <button
                    type="button"
                    onClick={() => exportMutation.mutate(theme)}
                    disabled={isBusy}
                    className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
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
                    })}
                    disabled={isBusy}
                    className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
                  >
                    <Copy className="h-4 w-4" />
                    Duplicate
                  </button>
                  {isCustom && (
                    <>
                      <button
                        type="button"
                        onClick={() => setRenameDraft({
                          sourceName: theme.name,
                          newName: theme.name,
                          displayName: theme.display_name,
                        })}
                        disabled={isBusy}
                        className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
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
                        className="inline-flex items-center gap-2 rounded-md border border-destructive/40 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 disabled:opacity-50"
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete
                      </button>
                    </>
                  )}
                </div>

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
