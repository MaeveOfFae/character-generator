import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Save,
  TestTube,
  Loader2,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  RefreshCw,
  Palette,
  Upload,
  Download,
  RotateCcw,
} from 'lucide-react';
import { api, type Config, type ModelInfo, type ThemeOverride, type ThemePreset } from '@char-gen/shared';
import { useThemePreview } from '../common/ThemeProvider';
import {
  EDITABLE_THEME_FIELDS,
  resolveThemeColors,
} from '../../theme/theme';

const ALL_PROVIDERS = ['openai', 'google', 'openrouter', 'deepseek', 'zai', 'moonshot'] as const;
type Provider = typeof ALL_PROVIDERS[number];

type ThemeImportPayload = {
  version?: number;
  theme_name?: string;
  theme?: ThemeOverride;
  name?: string;
  colors?: ThemePreset['colors'];
};

function buildThemeOverrideFromColors(colors: ThemePreset['colors']): ThemeOverride {
  return {
    app: {
      background: colors.background,
      text: colors.text,
      accent: colors.accent,
      button: colors.button,
      button_text: colors.button_text,
      border: colors.border,
      highlight: colors.highlight,
      window: colors.window,
      muted_text: colors.muted_text,
      surface: colors.surface,
      success_text: colors.success_text,
      error_text: colors.error_text,
      warning_text: colors.warning_text,
      success_bg: colors.success_bg,
      danger_bg: colors.danger_bg,
      accent_bg: colors.accent_bg,
      accent_title: colors.accent_title,
    },
  };
}

export default function Settings() {
  const queryClient = useQueryClient();
  const importInputRef = useRef<HTMLInputElement | null>(null);
  const { themes, isLoading: themesLoading, previewTheme, clearPreview } = useThemePreview();

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [testResult, setTestResult] = useState<{ provider: string; success: boolean; message: string } | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<Provider>('openrouter');
  const [localConfig, setLocalConfig] = useState<Partial<Config>>({});
  const [themeNotice, setThemeNotice] = useState<string | null>(null);
  const [themeError, setThemeError] = useState<string | null>(null);

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  });

  const {
    data: modelsData,
    isLoading: modelsLoading,
    refetch: refreshModels,
    isRefetching: modelsRefreshing,
  } = useQuery({
    queryKey: ['models', selectedProvider],
    queryFn: () => api.getModels(selectedProvider),
    enabled: !!selectedProvider,
  });

  useEffect(() => {
    if (!config) {
      return;
    }

    setLocalConfig(config);

    const model = config.model || '';
    for (const provider of ALL_PROVIDERS) {
      if (model.startsWith(provider + '/') || model.includes(provider)) {
        setSelectedProvider(provider);
        break;
      }
    }
  }, [config]);

  const updateMutation = useMutation({
    mutationFn: (updates: Partial<Config>) => api.updateConfig(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setThemeNotice('Settings saved. Theme and generation config are now persisted.');
      setThemeError(null);
    },
  });

  const testMutation = useMutation({
    mutationFn: (provider: string) => api.testConnection({ provider }),
    onSuccess: (result, provider) => {
      setTestResult({
        provider,
        success: result.success,
        message: result.success
          ? `Connected! Latency: ${result.latency_ms?.toFixed(0)}ms`
          : result.error || 'Connection failed',
      });
    },
  });

  const selectedThemeName = localConfig.theme_name ?? config?.theme_name ?? 'dark';
  const selectedTheme = useMemo(
    () => themes.find((theme) => theme.name === selectedThemeName) ?? themes[0],
    [themes, selectedThemeName]
  );

  const resolvedTheme = useMemo(
    () => resolveThemeColors(selectedTheme, localConfig.theme),
    [selectedTheme, localConfig.theme]
  );

  useEffect(() => {
    previewTheme(selectedThemeName, localConfig.theme);

    return () => {
      clearPreview();
    };
  }, [previewTheme, clearPreview, selectedThemeName, localConfig.theme]);

  const handleSave = () => {
    updateMutation.mutate(localConfig);
  };

  const handleTest = (provider: string) => {
    setTestResult(null);
    testMutation.mutate(provider);
  };

  const toggleShowKey = (provider: string) => {
    setShowKeys((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleModelSelect = (modelId: string) => {
    setLocalConfig((previous) => ({ ...previous, model: modelId }));
  };

  const handleRefreshModels = () => {
    refreshModels();
  };

  const updateTheme = (themeName: string, nextTheme: ThemeOverride) => {
    setLocalConfig((previous) => ({
      ...previous,
      theme_name: themeName,
      theme: nextTheme,
    }));
  };

  const handleThemePresetSelect = (themeName: string) => {
    updateTheme(themeName, {});
    setThemeNotice(`Loaded ${themeName} preset. Save settings to persist it.`);
    setThemeError(null);
  };

  const handleThemeFieldChange = (key: keyof NonNullable<ThemeOverride['app']>, value: string) => {
    const nextTheme: ThemeOverride = {
      ...localConfig.theme,
      app: {
        ...(localConfig.theme?.app ?? {}),
        [key]: value || undefined,
      },
      tokenizer: localConfig.theme?.tokenizer,
    };

    updateTheme(selectedThemeName, nextTheme);
    setThemeNotice('Preview updated. Save settings when you want to keep these overrides.');
    setThemeError(null);
  };

  const handleResetThemeOverrides = () => {
    updateTheme(selectedThemeName, {});
    setThemeNotice('Custom overrides cleared. Preset colors restored.');
    setThemeError(null);
  };

  const handleExportTheme = () => {
    const payload = {
      version: 1,
      exported_at: new Date().toISOString(),
      theme_name: selectedThemeName,
      theme: localConfig.theme ?? {},
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedThemeName.replace(/[^a-z0-9_-]/gi, '_')}_theme.json`;
    link.click();
    URL.revokeObjectURL(url);

    setThemeNotice('Theme JSON exported.');
    setThemeError(null);
  };

  const handleImportThemeClick = () => {
    importInputRef.current?.click();
  };

  const handleImportTheme = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const raw = await file.text();
      const parsed = JSON.parse(raw) as ThemeImportPayload;

      if (parsed.theme || parsed.theme_name) {
        updateTheme(parsed.theme_name ?? selectedThemeName, parsed.theme ?? {});
      } else if (parsed.colors) {
        updateTheme(parsed.name ?? selectedThemeName, buildThemeOverrideFromColors(parsed.colors));
      } else {
        throw new Error('Theme file did not contain a supported theme payload.');
      }

      setThemeNotice(`Imported theme from ${file.name}. Save settings to persist it.`);
      setThemeError(null);
    } catch (error) {
      setThemeError(error instanceof Error ? error.message : 'Theme import failed');
      setThemeNotice(null);
    } finally {
      event.target.value = '';
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const models = modelsData?.models || [];
  const currentModel = localConfig.model || config?.model || '';

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Configure providers, generation defaults, and the active application theme.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <h2 className="text-lg font-semibold">API Keys</h2>
          <p className="text-sm text-muted-foreground">
            Configure your LLM provider API keys. Keys are stored locally in .bpui.toml.
          </p>
        </div>
        <div className="space-y-4 p-4">
          {ALL_PROVIDERS.map((provider) => (
            <div key={provider} className="space-y-2">
              <label className="text-sm font-medium capitalize">{provider}</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showKeys[provider] ? 'text' : 'password'}
                    value={localConfig.api_keys?.[provider] || config?.api_keys?.[provider] || ''}
                    onChange={(e) =>
                      setLocalConfig((previous) => ({
                        ...previous,
                        api_keys: {
                          ...(previous.api_keys || config?.api_keys || {}),
                          [provider]: e.target.value,
                        },
                      }))
                    }
                    placeholder={`Enter your ${provider} API key`}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey(provider)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showKeys[provider] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <button
                  onClick={() => handleTest(provider)}
                  disabled={testMutation.isPending}
                  className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
                >
                  {testMutation.isPending && testMutation.variables === provider ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <TestTube className="h-4 w-4" />
                  )}
                  Test
                </button>
              </div>
              {testResult?.provider === provider && (
                <div className={`flex items-center gap-2 text-sm ${testResult.success ? 'text-green-500' : 'text-destructive'}`}>
                  {testResult.success ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                  {testResult.message}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <h2 className="text-lg font-semibold">Model Selection</h2>
          <p className="text-sm text-muted-foreground">
            Choose your preferred model and engine. Models are fetched dynamically from providers.
          </p>
        </div>
        <div className="space-y-4 p-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value as Provider)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {ALL_PROVIDERS.map((provider) => (
                <option key={provider} value={provider}>
                  {provider.charAt(0).toUpperCase() + provider.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Engine</label>
              <select
                value={localConfig.engine || config?.engine || 'auto'}
                onChange={(e) => setLocalConfig((previous) => ({ ...previous, engine: e.target.value as Config['engine'] }))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="auto">Auto (detect from model)</option>
                <option value="openai">OpenAI</option>
                <option value="google">Google</option>
                <option value="openai_compatible">OpenAI Compatible</option>
              </select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Model</label>
                <button
                  onClick={handleRefreshModels}
                  disabled={modelsRefreshing || modelsLoading}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                >
                  <RefreshCw className={`h-3 w-3 ${modelsRefreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
              {modelsLoading ? (
                <div className="flex items-center justify-center py-2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <select
                  value={currentModel}
                  onChange={(e) => handleModelSelect(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">Select a model...</option>
                  {models.map((model: ModelInfo) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                      {model.context_length ? ` (${Math.round(model.context_length / 1000)}k ctx)` : ''}
                    </option>
                  ))}
                </select>
              )}
              {modelsData?.error && <p className="text-xs text-yellow-600">{modelsData.error}</p>}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Or enter custom model ID</label>
            <input
              type="text"
              value={currentModel}
              onChange={(e) => handleModelSelect(e.target.value)}
              placeholder="e.g., openrouter/openai/gpt-4o-mini"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <p className="text-xs text-muted-foreground">
              Use format: provider/model-name (e.g., openrouter/anthropic/claude-3.5-sonnet)
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <div className="flex items-center gap-2">
            <Palette className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Theme Studio</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Load a preset, tweak key colors, and import or export the current theme as JSON.
          </p>
        </div>
        <div className="space-y-6 p-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {themesLoading ? (
              <div className="col-span-full flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading theme presets...
              </div>
            ) : (
              themes.map((theme) => {
                const isSelected = theme.name === selectedThemeName;
                return (
                  <button
                    key={theme.name}
                    type="button"
                    onClick={() => handleThemePresetSelect(theme.name)}
                    className={`rounded-lg border p-4 text-left transition-colors ${
                      isSelected ? 'border-primary bg-primary/10' : 'border-border hover:bg-accent'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">{theme.display_name}</div>
                        <div className="text-xs text-muted-foreground">{theme.name}</div>
                      </div>
                      {isSelected && <CheckCircle className="h-4 w-4 text-primary" />}
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{theme.description || 'No description'}</p>
                    <div className="mt-4 flex gap-2">
                      {[theme.colors.background, theme.colors.surface, theme.colors.accent, theme.colors.highlight].map((color) => (
                        <span
                          key={`${theme.name}-${color}`}
                          className="h-6 w-6 rounded-full border border-black/10"
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
            <div className="space-y-4 rounded-lg border border-border bg-background/60 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Custom Overrides</h3>
                  <p className="text-sm text-muted-foreground">
                    Overrides apply on top of the selected preset and preview live.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleResetThemeOverrides}
                  className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset overrides
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {EDITABLE_THEME_FIELDS.map((field) => (
                  <label key={field.key} className="space-y-2 text-sm">
                    <span className="font-medium">{field.label}</span>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={localConfig.theme?.app?.[field.key] || resolvedTheme?.[field.key === 'text' ? 'text' : field.key === 'muted_text' ? 'muted_text' : field.key === 'surface' ? 'surface' : field.key] || '#000000'}
                        onChange={(e) => handleThemeFieldChange(field.key, e.target.value)}
                        className="h-10 w-12 rounded border border-input bg-background p-1"
                      />
                      <input
                        type="text"
                        value={localConfig.theme?.app?.[field.key] || ''}
                        onChange={(e) => handleThemeFieldChange(field.key, e.target.value)}
                        placeholder={resolvedTheme?.[field.key === 'text' ? 'text' : field.key === 'muted_text' ? 'muted_text' : field.key === 'surface' ? 'surface' : field.key] || '#000000'}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      />
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-4 rounded-lg border border-border bg-background/60 p-4">
              <div>
                <h3 className="font-semibold">Theme Preview</h3>
                <p className="text-sm text-muted-foreground">
                  Current preset: <span className="font-medium text-foreground">{selectedTheme?.display_name || selectedThemeName}</span>
                </p>
              </div>

              {resolvedTheme && (
                <div
                  className="rounded-xl border p-4"
                  style={{
                    background: `linear-gradient(180deg, ${resolvedTheme.window} 0%, ${resolvedTheme.background} 100%)`,
                    borderColor: resolvedTheme.border,
                    color: resolvedTheme.text,
                  }}
                >
                  <div className="mb-4 flex items-center justify-between rounded-lg px-3 py-2"
                    style={{ backgroundColor: resolvedTheme.surface }}>
                    <span className="font-semibold">Character Generator</span>
                    <span
                      className="rounded-full px-2 py-1 text-xs font-medium"
                      style={{ backgroundColor: resolvedTheme.accent, color: resolvedTheme.button_text }}
                    >
                      Theme Live
                    </span>
                  </div>
                  <div className="space-y-3">
                    <div className="rounded-lg p-3" style={{ backgroundColor: resolvedTheme.surface }}>
                      <div className="text-sm font-medium">Review panel</div>
                      <div className="text-xs" style={{ color: resolvedTheme.muted_text }}>
                        Accent surfaces, borders, and button contrast update as you edit.
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="rounded-md px-3 py-2 text-sm font-medium"
                        style={{ backgroundColor: resolvedTheme.button, color: resolvedTheme.button_text }}
                      >
                        Primary action
                      </button>
                      <button
                        type="button"
                        className="rounded-md border px-3 py-2 text-sm font-medium"
                        style={{ borderColor: resolvedTheme.border, color: resolvedTheme.text }}
                      >
                        Secondary
                      </button>
                    </div>
                    <div className="flex gap-2 text-xs font-medium">
                      <span style={{ color: resolvedTheme.success_text }}>Success</span>
                      <span style={{ color: resolvedTheme.warning_text }}>Warning</span>
                      <span style={{ color: resolvedTheme.error_text }}>Error</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Theme Import / Export</h4>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleExportTheme}
                    className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent"
                  >
                    <Download className="h-4 w-4" />
                    Export JSON
                  </button>
                  <button
                    type="button"
                    onClick={handleImportThemeClick}
                    className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm hover:bg-accent"
                  >
                    <Upload className="h-4 w-4" />
                    Import JSON
                  </button>
                </div>
                <input
                  ref={importInputRef}
                  type="file"
                  accept="application/json"
                  onChange={handleImportTheme}
                  className="hidden"
                />
              </div>
            </div>
          </div>

          {(themeNotice || themeError) && (
            <div className={`rounded-md border px-3 py-2 text-sm ${themeError ? 'border-destructive/40 bg-destructive/10 text-destructive' : 'border-primary/30 bg-primary/10 text-foreground'}`}>
              {themeError || themeNotice}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <h2 className="text-lg font-semibold">Generation Settings</h2>
          <p className="text-sm text-muted-foreground">Fine-tune generation parameters.</p>
        </div>
        <div className="space-y-4 p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Temperature: {localConfig.temperature ?? config?.temperature ?? 0.7}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={localConfig.temperature ?? config?.temperature ?? 0.7}
                onChange={(e) => setLocalConfig((previous) => ({ ...previous, temperature: parseFloat(e.target.value) }))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Focused</span>
                <span>Creative</span>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Tokens</label>
              <input
                type="number"
                value={localConfig.max_tokens ?? config?.max_tokens ?? 4096}
                onChange={(e) => setLocalConfig((previous) => ({ ...previous, max_tokens: parseInt(e.target.value, 10) || 0 }))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Concurrent (Batch)</label>
              <input
                type="number"
                min="1"
                max="10"
                value={localConfig.batch?.max_concurrent ?? config?.batch?.max_concurrent ?? 3}
                onChange={(e) =>
                  setLocalConfig((previous) => ({
                    ...previous,
                    batch: {
                      ...(previous.batch || config?.batch || { max_concurrent: 3, rate_limit_delay: 1 }),
                      max_concurrent: parseInt(e.target.value, 10) || 1,
                    },
                  }))
                }
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Rate Limit Delay (seconds)</label>
              <input
                type="number"
                min="0"
                max="60"
                step="0.5"
                value={localConfig.batch?.rate_limit_delay ?? config?.batch?.rate_limit_delay ?? 1}
                onChange={(e) =>
                  setLocalConfig((previous) => ({
                    ...previous,
                    batch: {
                      ...(previous.batch || config?.batch || { max_concurrent: 3, rate_limit_delay: 1 }),
                      rate_limit_delay: parseFloat(e.target.value) || 0,
                    },
                  }))
                }
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {updateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Save Settings
        </button>
      </div>
    </div>
  );
}