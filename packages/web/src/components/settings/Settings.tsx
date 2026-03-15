import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Save,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  Download,
  Upload,
  RotateCcw,
  Shield,
  Zap,
  Palette,
  Lock,
  BookOpen,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Config, ModelInfo, ThemeOverride, ThemePreset } from '@char-gen/shared';
import { useThemePreview } from '../common/useThemePreview';
import {
  EDITABLE_THEME_SECTIONS,
  resolveThemeColors,
} from '../../theme/theme';
import { api } from '../../lib/api.js';
import { configManager, isInvalidApiKeyValue, normalizeApiKeyValue } from '../../lib/config/manager.js';
import { createEngine, MODEL_SUGGESTIONS } from '../../lib/llm/factory.js';
import { saveBlobDownload } from '../../utils/download';
import { GETTING_STARTED_TOUR_ID } from '@/lib/help';
import InlineHelpTip from '../common/InlineHelpTip';
import { useGuidedTour } from '../common/GuidedTourContext';

const ALL_PROVIDERS = ['openai', 'google', 'openrouter', 'anthropic', 'deepseek', 'zai', 'moonshot'] as const;
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
    tokenizer: {
      brackets: colors.tok_brackets,
      asterisk: colors.tok_asterisk,
      parentheses: colors.tok_parentheses,
      double_brackets: colors.tok_double_brackets,
      curly_braces: colors.tok_curly_braces,
      pipes: colors.tok_pipes,
      at_sign: colors.tok_at_sign,
    },
  } as ThemeOverride;
}

// Provider colors for badges
const PROVIDER_COLORS: Record<Provider, string> = {
  openai: 'from-emerald-500 to-green-500',
  google: 'from-blue-500 to-cyan-500',
  openrouter: 'from-violet-500 to-purple-500',
  anthropic: 'from-orange-500 to-red-500',
  deepseek: 'from-cyan-500 to-teal-500',
  zai: 'from-pink-500 to-rose-500',
  moonshot: 'from-orange-500 to-amber-500',
};

export default function Settings() {
  const importInputRef = useRef<HTMLInputElement | null>(null);
  const { themes, isLoading: themesLoading, previewTheme, clearPreview } = useThemePreview();

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [testResult, setTestResult] = useState<{ provider: string; success: boolean; message: string } | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<Provider>('openrouter');
  const [localConfig, setLocalConfig] = useState<Partial<Config>>({});
  const [themeNotice, setThemeNotice] = useState<string | null>(null);
  const [themeError, setThemeError] = useState<string | null>(null);
  const [persistKeys, setPersistKeys] = useState(false);
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsNotice, setModelsNotice] = useState<string | null>(null);
  const { isTourCompleted, restartTour, startTour } = useGuidedTour();

  // Load config from client-side manager
  useEffect(() => {
    const config = configManager.getConfig();
    const apiKeys = configManager.getApiKeys();
    setLocalConfig({ ...config, api_keys: apiKeys });
    setPersistKeys(configManager.isPersistingApiKeys());

    if (config.engine_mode === 'explicit' && config.engine && ALL_PROVIDERS.includes(config.engine as Provider)) {
      setSelectedProvider(config.engine as Provider);
      return;
    }

    const model = config.model || '';
    for (const provider of ALL_PROVIDERS) {
      if (model.startsWith(provider + '/') || model.includes(provider)) {
        setSelectedProvider(provider);
        return;
      }
    }
  }, []);

  const modelSuggestions = useMemo(() => {
    if (availableModels.length > 0) {
      return availableModels.map((model) => model.id);
    }

    return MODEL_SUGGESTIONS[selectedProvider] || [];
  }, [availableModels, selectedProvider]);

  const updateConfig = () => {
    const persistedConfig = { ...localConfig };
    delete persistedConfig.api_keys;
    configManager.updateConfig(persistedConfig);
    configManager.setPersistApiKeys(persistKeys);

    if (localConfig.api_keys) {
      configManager.setApiKeys(localConfig.api_keys);
    }

    setThemeNotice('Settings saved. Theme and generation config are now persisted.');
    setThemeError(null);
  };

  const selectedThemeName = localConfig.theme_name ?? 'dark';
  const selectedTheme = useMemo(
    () => themes.find((theme) => theme.name === selectedThemeName) ?? themes[0],
    [themes, selectedThemeName]
  );

  const resolvedTheme = useMemo(
    () => resolveThemeColors(selectedTheme, localConfig.theme),
    [selectedTheme, localConfig.theme]
  );

  useEffect(() => {
    let isCancelled = false;

    const loadModels = async () => {
      setModelsLoading(true);
      try {
        const response = await api.getModels(selectedProvider);
        if (isCancelled) {
          return;
        }

        setAvailableModels(response.models);
        setModelsNotice(response.error || null);
      } catch (error) {
        if (isCancelled) {
          return;
        }

        setAvailableModels([]);
        setModelsNotice(error instanceof Error ? error.message : 'Failed to load models');
      } finally {
        if (!isCancelled) {
          setModelsLoading(false);
        }
      }
    };

    void loadModels();

    return () => {
      isCancelled = true;
    };
  }, [selectedProvider, localConfig.api_keys?.[selectedProvider]]);

  // Test connection with client-side engine
  const testConnection = async (provider: string) => {
    setTestResult(null);

    try {
      const apiKey = localConfig.api_keys?.[provider];
      if (!apiKey) {
        setTestResult({
          provider,
          success: false,
          message: 'No API key configured',
        });
        return;
      }

      const model = modelSuggestions[0] || localConfig.model || 'test-model';
      const engine = createEngine({
        model,
        apiKey,
        provider: provider as Provider,
        engineMode: 'explicit',
      });

      const startTime = performance.now();
      const result = await engine.testConnection();
      const latency = performance.now() - startTime;

      if (result.success) {
        setTestResult({
          provider,
          success: true,
          message: `${latency.toFixed(0)}ms`,
        });
      } else {
        setTestResult({
          provider,
          success: false,
          message: result.error || 'Connection failed',
        });
      }
    } catch (error) {
      setTestResult({
        provider,
        success: false,
        message: error instanceof Error ? error.message : 'Connection failed',
      });
    }
  };

  useEffect(() => {
    previewTheme(selectedThemeName, localConfig.theme);

    return () => {
      clearPreview();
    };
  }, [previewTheme, clearPreview, selectedThemeName, localConfig.theme]);

  const handleTest = (provider: string) => {
    testConnection(provider);
  };

  const toggleShowKey = (provider: string) => {
    setShowKeys((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleApiKeyChange = (provider: Provider, value: string) => {
    const normalizedValue = normalizeApiKeyValue(value);

    setLocalConfig((previous) => {
      const nextApiKeys = { ...(previous.api_keys || {}) };
      if (normalizedValue && !isInvalidApiKeyValue(normalizedValue)) {
        nextApiKeys[provider] = normalizedValue;
        configManager.setApiKey(provider, normalizedValue);
      } else {
        delete nextApiKeys[provider];
        configManager.clearApiKey(provider);
      }
      return {
        ...previous,
        api_keys: nextApiKeys,
      };
    });
  };

  const handleProviderSelect = (provider: Provider) => {
    setSelectedProvider(provider);
    setLocalConfig((previous) => ({
      ...previous,
      engine: provider,
      engine_mode: 'explicit',
      model: previous.engine === provider ? previous.model : '',
    }));
  };

  const handleModelSelect = (modelId: string) => {
    setLocalConfig((previous) => ({
      ...previous,
      engine: selectedProvider,
      engine_mode: 'explicit',
      model: modelId,
    }));
  };

  const handlePersistKeysToggle = (checked: boolean) => {
    setPersistKeys(checked);
    configManager.setPersistApiKeys(checked);
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

  const handleThemeFieldChange = (
    section: 'app' | 'tokenizer',
    key: string,
    value: string
  ) => {
    const themeSections = (localConfig.theme ?? {}) as Record<string, Record<string, string | undefined> | undefined>;
    const sectionValues = themeSections[section] ?? {};
    const nextTheme = {
      ...localConfig.theme,
      [section]: {
        ...sectionValues,
        [key]: value || undefined,
      },
    } as ThemeOverride;

    updateTheme(selectedThemeName, nextTheme);
    setThemeNotice('Preview updated. Save settings when you want to keep these overrides.');
    setThemeError(null);
  };

  const getThemeOverrideValue = (section: 'app' | 'tokenizer', key: string) => {
    const themeSections = (localConfig.theme ?? {}) as Record<string, Record<string, string | undefined> | undefined>;
    const sectionValues = themeSections[section] as Record<string, string | undefined> | undefined;
    return sectionValues?.[key] || '';
  };

  const handleResetThemeOverrides = () => {
    updateTheme(selectedThemeName, {});
    setThemeNotice('Custom overrides cleared. Preset colors restored.');
    setThemeError(null);
  };

  const handleExportTheme = async () => {
    const payload = {
      version: 1,
      exported_at: new Date().toISOString(),
      theme_name: selectedThemeName,
      theme: localConfig.theme ?? {},
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    await saveBlobDownload(blob, `${selectedThemeName.replace(/[^a-z0-9_-]/gi, '_')}_theme.json`);

    setThemeNotice('Theme JSON exported.');
    setThemeError(null);
  };

  const handleImportThemeClick = () => {
    importInputRef.current?.click();
  };

  const handleImportTheme = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

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

  const handleRestartGettingStarted = () => {
    const baseHelp = localConfig.help ?? configManager.getHelpState();
    const nextHelpState = {
      ...baseHelp,
      first_run_completed: false,
      completed_guides: (baseHelp.completed_guides ?? []).filter((guideId) => guideId !== 'getting-started'),
      completed_tours: (baseHelp.completed_tours ?? []).filter((tourId) => tourId !== 'getting-started'),
    };

    setLocalConfig((previous) => ({
      ...previous,
      help: nextHelpState,
    }));
    configManager.updateHelpState(nextHelpState);
    setThemeNotice('Getting Started has been reset. Return to Home to run through it again.');
    setThemeError(null);
  };

  const handleResetHelpPreferences = () => {
    configManager.resetHelpState();
    setLocalConfig((previous) => ({
      ...previous,
      help: configManager.getHelpState(),
    }));
    setThemeNotice('Help preferences were reset. Inline tips and first-run guidance are enabled again.');
    setThemeError(null);
  };

  const currentModel = localConfig.model || '';

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div className="text-center space-y-2 mb-8">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Configure providers, generation defaults, and customize your theme.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* API Keys Section */}
        <section className="lg:col-span-2 space-y-4">

        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
          <div className="font-semibold text-foreground">Browser-only persistence</div>
          <p className="mt-1 text-muted-foreground">
            Settings, API keys, drafts, templates, themes, and blueprint overrides are stored locally in this browser profile. No backend service is required for the web app runtime.
          </p>
        </div>
          <InlineHelpTip
            tipId="settings-provider-tip"
            title="Most early generation failures start here"
            description="Pick the provider you actually use, enter its key, then confirm the model. If direct OpenAI browser calls are blocked, switch to OpenRouter or your own relay instead of retrying blindly."
            actionLabel={isTourCompleted(GETTING_STARTED_TOUR_ID) ? 'Replay provider setup tour step' : 'Run Getting Started Tour'}
            onAction={() => (isTourCompleted(GETTING_STARTED_TOUR_ID) ? restartTour(GETTING_STARTED_TOUR_ID) : startTour(GETTING_STARTED_TOUR_ID))}
          />
          <div data-tour-anchor="settings-api-keys" className="rounded-2xl border border-border/50 bg-card/50 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-xl bg-gradient-to-br from-primary to-accent">
                <Lock className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">API Keys</h2>
                <p className="text-sm text-muted-foreground">
                  Keys stay in browser and are sent with each request.
                </p>
              </div>
            </div>

            <label className="flex items-center gap-3 p-3 rounded-lg bg-background/60 hover:bg-background/80 transition-colors cursor-pointer">
              <input
                type="checkbox"
                checked={persistKeys}
                onChange={(e) => handlePersistKeysToggle(e.target.checked)}
                className="h-5 w-5 rounded border-input"
              />
              <span className="text-sm font-medium">
                Save API keys to browser storage
              </span>
            </label>

            {persistKeys && (
              <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3">
                <p className="text-sm text-amber-900 dark:text-amber-100">
                  Warning: API keys are stored in localStorage. Clearing browser data will remove them. Use with caution on shared devices.
                </p>
              </div>
            )}

            <div className="space-y-3">
              {ALL_PROVIDERS.map((provider) => (
                <div key={provider} className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {provider}
                  </label>
                  <div className="relative">
                    <input
                      type={showKeys[provider] ? 'text' : 'password'}
                      value={localConfig.api_keys?.[provider] || ''}
                      onChange={(e) => handleApiKeyChange(provider, e.target.value)}
                      placeholder={`Enter your ${provider} API key`}
                      className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 pr-20 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    />
                    <button
                      type="button"
                      onClick={() => toggleShowKey(provider)}
                      className="absolute right-11 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-accent transition-colors"
                    >
                      {showKeys[provider] ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleTest(provider)}
                      disabled={!localConfig.api_keys?.[provider]}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
                    >
                      {testResult?.provider === provider ? (
                        <div className={`flex items-center gap-2 ${testResult.success ? 'text-green-500' : 'text-destructive'}`}>
                          {testResult.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                          <span className="text-xs">{testResult.message}</span>
                        </div>
                      ) : (
                        <Zap className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Model Selection */}
        <section className="space-y-4">
          <div data-tour-anchor="settings-model" className="rounded-2xl border border-border/50 bg-card/50 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 rounded-xl bg-gradient-to-br ${PROVIDER_COLORS[selectedProvider]}`}>
                <Zap className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Model</h2>
                <p className="text-sm text-muted-foreground">
                  Choose your preferred LLM provider and model.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {selectedProvider === 'openai' && (
                <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-900 dark:text-amber-100">
                  Direct OpenAI calls from this browser app are blocked by CORS on api.openai.com. Use OpenRouter for browser-direct usage, or point the base URL at your own proxy or relay.
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium">Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => handleProviderSelect(e.target.value as Provider)}
                  className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {ALL_PROVIDERS.map((provider) => (
                    <option key={provider} value={provider}>
                      {provider.charAt(0).toUpperCase() + provider.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <select
                  value={currentModel}
                  onChange={(e) => handleModelSelect(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">Select a model...</option>
                  {modelSuggestions.map((model: string) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  {modelsLoading
                    ? 'Loading models from provider API...'
                    : availableModels.length > 0
                      ? `Loaded ${availableModels.length} models from ${selectedProvider}.`
                      : 'Showing built-in suggestions.'}
                </p>
                {modelsNotice && (
                  <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                    {modelsNotice}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Or enter custom model ID</label>
                <input
                  type="text"
                  value={currentModel}
                  onChange={(e) => handleModelSelect(e.target.value)}
                  placeholder="e.g., openrouter/openai/gpt-4o-mini"
                  className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Use format: provider/model-name
                </p>
              </div>
            </div>

            <div className="grid gap-4 grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Temperature</label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={localConfig.temperature ?? 0.7}
                  onChange={(e) => setLocalConfig((previous) => ({ ...previous, temperature: parseFloat(e.target.value) }))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Focused (0.0)</span>
                  <span>Creative (2.0)</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Max Tokens</label>
                <input
                  type="number"
                  value={localConfig.max_tokens ?? 4096}
                  onChange={(e) => setLocalConfig((previous) => ({ ...previous, max_tokens: parseInt(e.target.value, 10) || 0 }))}
                  className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
            </div>
          </div>

          {/* Quick Save Button */}
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={updateConfig}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:from-primary/90 hover:to-accent/90 transition-all duration-200 shadow-lg shadow-primary/20"
            >
              <Save className="h-4 w-4" />
              Save Settings
            </button>
            {themeNotice && (
              <span className="text-sm text-green-600 dark:text-green-400">{themeNotice}</span>
            )}
          </div>
        </section>
      </div>

      {/* Batch Settings */}
      <section className="rounded-2xl border border-border/50 bg-card/50 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-bold">Batch Generation</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">Max Concurrent</label>
            <input
              type="number"
              min="1"
              max="10"
              value={localConfig.batch?.max_concurrent ?? 3}
              onChange={(e) =>
                setLocalConfig((previous) => ({
                  ...previous,
                  batch: {
                    ...(previous.batch || { max_concurrent: 3, rate_limit_delay: 1 }),
                    max_concurrent: parseInt(e.target.value, 10) || 1,
                  },
                }))
              }
              className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Rate Limit Delay</label>
            <input
              type="number"
              min="0"
              max="60"
              step="0.5"
              value={localConfig.batch?.rate_limit_delay ?? 1}
              onChange={(e) =>
                setLocalConfig((previous) => ({
                  ...previous,
                  batch: {
                    ...(previous.batch || { max_concurrent: 3, rate_limit_delay: 1 }),
                    rate_limit_delay: parseFloat(e.target.value) || 0,
                  },
                }))
              }
              className="w-full rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
        </div>
      </section>

      <section data-tour-anchor="settings-help-tutorials" className="rounded-2xl border border-border/50 bg-card/50 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-600">
            <BookOpen className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Help and Tutorials</h2>
            <p className="text-sm text-muted-foreground">
              Control the first-run guide and inline help surfaces.
            </p>
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-xl border border-border/50 bg-background/40 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-medium text-foreground">Inline tips</h3>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  Keep plain-language helper copy visible on high-friction screens like generation, review, export, templates, blueprints, and settings.
                </p>
              </div>
              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={localConfig.help?.show_inline_tips ?? true}
                  onChange={(event) =>
                    setLocalConfig((previous) => ({
                      ...previous,
                      help: {
                        ...(previous.help ?? configManager.getHelpState()),
                        show_inline_tips: event.target.checked,
                      },
                    }))
                  }
                  className="rounded border-input"
                />
                Show tips
              </label>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-xl border border-border/50 bg-background/40 p-4">
              <h3 className="font-medium text-foreground">Getting Started guide</h3>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Reopen or reset the home-screen starter guide if you want to walk through setup, generation, review, and export again.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link
                  to="/help"
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-accent transition-colors"
                >
                  <BookOpen className="h-4 w-4" />
                  Open Help Center
                </Link>
                <button
                  type="button"
                  onClick={handleRestartGettingStarted}
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-accent transition-colors"
                >
                  <RotateCcw className="h-4 w-4" />
                  Restart Getting Started
                </button>
              </div>
            </div>

            <div className="rounded-xl border border-border/50 bg-background/40 p-4">
              <h3 className="font-medium text-foreground">Reset help state</h3>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Restore default tutorial settings and turn first-run guidance back on for this browser profile.
              </p>
              <button
                type="button"
                onClick={handleResetHelpPreferences}
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-accent transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                Reset Help Preferences
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Theme Section */}
      <section className="rounded-2xl border border-border/50 bg-card/50 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500">
            <Palette className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Theme Studio</h2>
            <p className="text-sm text-muted-foreground">
              Load a preset, tweak key colors, and export as JSON.
            </p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Preset Selection */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium uppercase tracking-wider text-muted-foreground mb-3">Presets</h3>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {themesLoading ? (
                <div className="col-span-full flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="h-4 w-4 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
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
                      className={`relative overflow-hidden rounded-xl p-4 text-left transition-all duration-200 hover:scale-105 ${
                        isSelected ? 'bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-lg shadow-primary/20' : 'bg-background/50 border border-border/50 hover:border-primary/50 hover:bg-accent/50'
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 -z-10" />
                      )}
                      <div className="relative">
                        <div className="flex items-center justify-between mb-2">
                          <div className="space-y-0.5">
                            <div className="font-semibold">{theme.display_name}</div>
                            <div className="text-xs text-muted-foreground">{theme.name}</div>
                          </div>
                          {isSelected && <CheckCircle2 className="h-4 w-4" />}
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">{theme.description || 'No description'}</p>
                        <div className="flex gap-2 mt-3">
                          {[theme.colors.background, theme.colors.surface, theme.colors.accent, theme.colors.highlight].map((color) => (
                            <span
                              key={`${theme.name}-${color}`}
                              className="h-6 w-6 rounded-full border border-border/50"
                              style={{ backgroundColor: color }}
                            />
                          ))}
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
            {/* Custom Overrides */}
            <div className="space-y-4 rounded-xl border border-border/50 bg-background/60 p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold">Custom Overrides</h3>
                  <p className="text-sm text-muted-foreground">
                    Apply on top of the selected preset and preview live.
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleResetThemeOverrides}
                    className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-accent transition-colors"
                  >
                    <RotateCcw className="h-4 w-4" />
                    Reset
                  </button>
                  <Link
                    to="/themes"
                    className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-accent transition-colors"
                  >
                    <Palette className="h-4 w-4" />
                    Manage
                  </Link>
                </div>
              </div>

              <div className="space-y-5">
                {EDITABLE_THEME_SECTIONS.map((section) => (
                  <div key={section.title} className="space-y-3">
                    <div>
                      <h4 className="font-medium text-sm">{section.title}</h4>
                      <p className="text-xs text-muted-foreground">{section.description}</p>
                    </div>
                    <div className="grid gap-3 md:grid-cols-2">
                      {section.fields.map((field) => (
                        <label key={`${section.title}-${field.key}`} className="space-y-1.5 text-sm">
                          <span className="font-medium">{field.label}</span>
                          <div className="flex gap-2">
                            <input
                              type="color"
                              value={getThemeOverrideValue(field.section, field.key) || resolvedTheme?.[field.colorKey] || '#000000'}
                              onChange={(e) => handleThemeFieldChange(field.section, field.key, e.target.value)}
                              className="h-9 w-9 rounded-lg border border-border bg-background/50 p-1"
                            />
                            <input
                              type="text"
                              value={getThemeOverrideValue(field.section, field.key)}
                              onChange={(e) => handleThemeFieldChange(field.section, field.key, e.target.value)}
                              placeholder={resolvedTheme?.[field.colorKey] || '#000000'}
                              className="flex-1 rounded-lg border border-border bg-background/50 px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            />
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Preview */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm">Preview</h3>
              {resolvedTheme && (
                <div
                  className="rounded-2xl border p-4"
                  style={{
                    background: `linear-gradient(180deg, ${resolvedTheme.window} 0%, ${resolvedTheme.background} 100%)`,
                    borderColor: resolvedTheme.border,
                    color: resolvedTheme.text,
                  }}
                >
                  <div className="flex items-center justify-between mb-3 rounded-lg px-3 py-2"
                    style={{ backgroundColor: resolvedTheme.surface }}>
                    <span className="font-semibold">Eidolon Simulacra</span>
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{ backgroundColor: resolvedTheme.accent, color: resolvedTheme.button_text }}
                    >
                      Theme Live
                    </span>
                  </div>

                  <div className="grid gap-2 grid-cols-3">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Review panel</p>
                      <div
                        className="rounded-lg p-3 text-sm"
                        style={{ backgroundColor: resolvedTheme.surface }}
                      >
                        Review your generated character drafts and assets
                      </div>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Colors</p>
                      <div className="flex gap-1.5">
                        <div
                          className="flex-1 rounded-lg p-2 text-sm font-medium"
                          style={{ backgroundColor: resolvedTheme.accent, color: resolvedTheme.button_text }}
                        >
                          Primary Action
                        </div>
                        <div
                          className="flex-1 rounded-lg p-2 text-sm font-medium border"
                          style={{ borderColor: resolvedTheme.border, color: resolvedTheme.text }}
                        >
                          Secondary
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1.5">
                      <div
                        className="flex-1 rounded-lg p-2 text-xs font-medium"
                        style={{ backgroundColor: resolvedTheme.surface, color: resolvedTheme.success_text }}
                      >
                        Success
                      </div>
                      <div
                        className="flex-1 rounded-lg p-2 text-xs font-medium"
                        style={{ backgroundColor: resolvedTheme.surface, color: resolvedTheme.warning_text }}
                      >
                        Warning
                      </div>
                      <div
                        className="flex-1 rounded-lg p-2 text-xs font-medium"
                        style={{ backgroundColor: resolvedTheme.surface, color: resolvedTheme.error_text }}
                      >
                        Error
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Import/Export */}
              <div className="space-y-3">
                <h3 className="font-medium text-sm">Import / Export</h3>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleExportTheme}
                    className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-primary to-accent px-4 py-2.5 text-sm font-medium text-primary-foreground hover:from-primary/90 hover:to-accent/90 transition-all duration-200 shadow-lg shadow-primary/20"
                  >
                    <Download className="h-4 w-4" />
                    Export JSON
                  </button>
                  <button
                    type="button"
                    onClick={handleImportThemeClick}
                    className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium hover:bg-accent transition-colors"
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
        </div>
      </section>

      {/* Footer Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-border/50">
        {(themeNotice || themeError) && (
          <div className={`flex-1 rounded-lg px-4 py-2.5 text-sm flex items-center gap-2 ${
            themeError
              ? 'bg-destructive/10 border-destructive/30 text-destructive'
              : 'bg-primary/10 border-primary/30 text-foreground'
          }`}>
            <Shield className={`h-4 w-4 flex-shrink-0 ${themeError ? 'text-destructive' : 'text-primary'}`} />
            {themeError || themeNotice}
            <button
              onClick={() => { setThemeError(null); setThemeNotice(null); }}
              className="ml-auto p-1 rounded hover:bg-black/10 transition-colors"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        )}
        <button
          onClick={updateConfig}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:from-primary/90 hover:to-accent/90 transition-all duration-200 shadow-lg shadow-primary/20"
        >
          <Save className="h-4 w-4" />
          Save All Settings
        </button>
      </div>
    </div>
  );
}
