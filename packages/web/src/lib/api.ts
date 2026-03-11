import {
  OFFICIAL_TEMPLATE,
  validateTemplate as validateTemplateDefinition,
  getOrderedAssets,
  type Blueprint,
  type BlueprintList,
  type ChatMessage,
  type ChatRequest,
  type Config,
  type ConnectionTestRequest,
  type ConnectionTestResult,
  type ContentMode,
  type CreateTemplateRequest,
  type Draft,
  type DraftFilters,
  type DraftListResponse,
  type DraftMetadata,
  type DuplicateTemplateRequest,
  type ExportPresetSummary,
  type ExportRequest,
  type FinalizeGenerationRequest,
  type GenerateAssetRequest,
  type GenerateAssetResponse,
  type GenerateBatchRequest,
  type GenerateRequest,
  type GenerationComplete,
  type LineageNode,
  type LineageResponse,
  type ModelsResponse,
  type OffspringRequest,
  type RefineRequest,
  type SeedGenerationRequest,
  type SeedGenerationResponse,
  type SimilarityRequest,
  type SimilarityResult,
  type Template,
  type TemplateBlueprintContentsResponse,
  type TemplateValidationResult,
  type ThemeDuplicateRequest,
  type ThemeImportRequest,
  type ThemePreset,
  type ThemePresetCreate,
  type ThemePresetUpdate,
  type ThemeRenameRequest,
  type UpdateTemplateRequest,
  type ValidatePathRequest,
  type ValidationResponse,
} from '@char-gen/shared';
import { MODEL_SUGGESTIONS, createEngine } from './llm/factory.js';
import { configManager } from './config/manager.js';
import { DraftStorage } from './storage/draft-db.js';
import { GenerationService } from './services/generation.js';
import {
  type StoredTemplateRecord,
  getAllTemplateRecords,
  getBlueprintCatalog,
  getBlueprintOverrides,
  getStoredTemplates,
  getTemplateRecord,
  inferCharacterDisplayNameForTemplate,
  resolveTemplateDefinition,
  saveBlueprintOverrides,
  saveStoredTemplates,
} from './templates/browser.js';

export interface DownloadResponse {
  blob: Blob;
  filename: string | null;
  contentType: string | null;
}

type StreamEventType = 'chunk' | 'complete' | 'error' | 'batch_start' | 'batch_complete' | 'batch_error';

type StreamEvent = {
  event: StreamEventType;
  data: unknown;
};

type StreamReader = (event: StreamEvent) => void;

type BlueprintPreviewRequest = GenerateAssetRequest & {
  blueprint_content: string;
};

type BlueprintPreviewResponse = GenerateAssetResponse & {
  system_prompt: string;
  user_prompt: string;
};

const CUSTOM_THEMES_STORAGE_KEY = 'bpui.web.themes.custom';

const EXPORT_PRESETS: ExportPresetSummary[] = [
  {
    name: 'json',
    path: 'json',
    format: 'json',
    description: 'Export the full draft as JSON.',
  },
  {
    name: 'text',
    path: 'text',
    format: 'text',
    description: 'Export draft assets as plain text sections.',
  },
  {
    name: 'combined',
    path: 'combined',
    format: 'combined',
    description: 'Export a markdown bundle with metadata and assets.',
  },
];

const builtinThemes: ThemePreset[] = [
  {
    name: 'dark',
    display_name: 'Dark',
    description: 'Default dark theme for browser-only mode.',
    author: 'Character Generator',
    tags: ['builtin', 'dark'],
    based_on: '',
    is_builtin: true,
    colors: {
      background: '#0f172a',
      text: '#e5e7eb',
      accent: '#38bdf8',
      button: '#1d4ed8',
      button_text: '#f8fafc',
      border: '#334155',
      highlight: '#7dd3fc',
      window: '#111827',
      tok_brackets: '#60a5fa',
      tok_asterisk: '#f472b6',
      tok_parentheses: '#f59e0b',
      tok_double_brackets: '#a78bfa',
      tok_curly_braces: '#34d399',
      tok_pipes: '#22d3ee',
      tok_at_sign: '#fb7185',
      muted_text: '#94a3b8',
      surface: '#1e293b',
      success_bg: '#052e16',
      danger_bg: '#450a0a',
      accent_bg: '#082f49',
      accent_title: '#e0f2fe',
      success_text: '#86efac',
      error_text: '#fca5a5',
      warning_text: '#fcd34d',
      tui_primary: '#38bdf8',
      tui_secondary: '#818cf8',
      tui_surface: '#0f172a',
      tui_panel: '#111827',
      tui_warning: '#f59e0b',
      tui_error: '#ef4444',
      tui_success: '#22c55e',
      tui_accent: '#8b5cf6',
    },
  },
  {
    name: 'light',
    display_name: 'Light',
    description: 'Default light theme for browser-only mode.',
    author: 'Character Generator',
    tags: ['builtin', 'light'],
    based_on: '',
    is_builtin: true,
    colors: {
      background: '#f8fafc',
      text: '#0f172a',
      accent: '#2563eb',
      button: '#1d4ed8',
      button_text: '#eff6ff',
      border: '#cbd5e1',
      highlight: '#0ea5e9',
      window: '#ffffff',
      tok_brackets: '#2563eb',
      tok_asterisk: '#db2777',
      tok_parentheses: '#d97706',
      tok_double_brackets: '#7c3aed',
      tok_curly_braces: '#059669',
      tok_pipes: '#0891b2',
      tok_at_sign: '#e11d48',
      muted_text: '#64748b',
      surface: '#ffffff',
      success_bg: '#dcfce7',
      danger_bg: '#fee2e2',
      accent_bg: '#dbeafe',
      accent_title: '#1e3a8a',
      success_text: '#166534',
      error_text: '#991b1b',
      warning_text: '#92400e',
      tui_primary: '#2563eb',
      tui_secondary: '#7c3aed',
      tui_surface: '#f8fafc',
      tui_panel: '#ffffff',
      tui_warning: '#d97706',
      tui_error: '#dc2626',
      tui_success: '#16a34a',
      tui_accent: '#7c3aed',
    },
  },
  {
    name: 'nyx',
    display_name: 'Nyx',
    description: 'High-contrast theme tuned for the blueprint workflow.',
    author: 'Character Generator',
    tags: ['builtin', 'editorial'],
    based_on: 'dark',
    is_builtin: true,
    colors: {
      background: '#111113',
      text: '#f3f4f6',
      accent: '#f97316',
      button: '#c2410c',
      button_text: '#fff7ed',
      border: '#3f3f46',
      highlight: '#fb923c',
      window: '#18181b',
      tok_brackets: '#60a5fa',
      tok_asterisk: '#f472b6',
      tok_parentheses: '#f59e0b',
      tok_double_brackets: '#c084fc',
      tok_curly_braces: '#4ade80',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#fb7185',
      muted_text: '#a1a1aa',
      surface: '#18181b',
      success_bg: '#052e16',
      danger_bg: '#431407',
      accent_bg: '#431407',
      accent_title: '#ffedd5',
      success_text: '#86efac',
      error_text: '#fdba74',
      warning_text: '#fed7aa',
      tui_primary: '#f97316',
      tui_secondary: '#fb7185',
      tui_surface: '#111113',
      tui_panel: '#18181b',
      tui_warning: '#f59e0b',
      tui_error: '#f97316',
      tui_success: '#22c55e',
      tui_accent: '#ec4899',
    },
  },
];

class BrowserStream {
  private readers: StreamReader[] = [];
  private onComplete?: (data: unknown) => void;
  private onError?: (error: string) => void;
  private controller = new AbortController();

  constructor(
    private readonly executor: (helpers: {
      emit: (event: StreamEventType, data: unknown) => void;
      signal: AbortSignal;
    }) => Promise<void>
  ) {}

  subscribe(callback: StreamReader): this {
    this.readers.push(callback);
    return this;
  }

  onComplete_(callback: (data: unknown) => void): this {
    this.onComplete = callback;
    return this;
  }

  onError_(callback: (error: string) => void): this {
    this.onError = callback;
    return this;
  }

  async start(): Promise<void> {
    try {
      await this.executor({
        emit: (event, data) => this.emit(event, data),
        signal: this.controller.signal,
      });
    } catch (error) {
      if (this.controller.signal.aborted) {
        return;
      }
      this.emit('error', { error: error instanceof Error ? error.message : 'Stream failed' });
    }
  }

  abort(): void {
    this.controller.abort();
  }

  private emit(event: StreamEventType, data: unknown): void {
    const payload = { event, data } satisfies StreamEvent;
    this.readers.forEach((reader) => reader(payload));

    if (event === 'complete' && this.onComplete) {
      this.onComplete(data);
    }

    if (event === 'error' && this.onError) {
      const message = typeof data === 'object' && data && 'error' in data
        ? String((data as { error: unknown }).error)
        : 'Stream failed';
      this.onError(message);
    }
  }
}

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

function slugifyFileName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

function getBrowserConfig(): Config {
  return {
    ...configManager.getConfig(),
    api_keys: configManager.getApiKeys(),
  };
}

function getBuiltinTheme(name: string): ThemePreset | undefined {
  return builtinThemes.find((theme) => theme.name === name);
}

function getCustomThemes(): ThemePreset[] {
  return readStorage<ThemePreset[]>(CUSTOM_THEMES_STORAGE_KEY, []);
}

function saveCustomThemes(themes: ThemePreset[]): void {
  writeStorage(CUSTOM_THEMES_STORAGE_KEY, themes);
}

function getAllThemes(): ThemePreset[] {
  return [...builtinThemes, ...getCustomThemes()];
}

function buildDraftListResponse(
  metadata: DraftMetadata[],
  total: number,
  statsSource: DraftMetadata[] = metadata
): DraftListResponse {
  const stats = statsSource.reduce<DraftListResponse['stats']>((accumulator, draft) => {
    accumulator.total_drafts += 1;
    if (draft.favorite) {
      accumulator.favorites += 1;
    }

    const genre = draft.genre || 'unknown';
    const mode = draft.mode || 'unknown';
    accumulator.by_genre[genre] = (accumulator.by_genre[genre] || 0) + 1;
    accumulator.by_mode[mode] = (accumulator.by_mode[mode] || 0) + 1;
    return accumulator;
  }, {
    total_drafts: 0,
    favorites: 0,
    by_genre: {},
    by_mode: {},
  });

  return {
    drafts: metadata,
    total,
    stats,
  };
}

function applyDraftFilters(metadata: DraftMetadata[], filters?: DraftFilters): DraftMetadata[] {
  let result = [...metadata];

  if (filters?.search) {
    const query = filters.search.toLowerCase();
    result = result.filter((draft) => [draft.character_name, draft.seed, draft.genre, draft.notes]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
    );
  }

  if (filters?.genre) {
    result = result.filter((draft) => draft.genre === filters.genre);
  }

  if (filters?.mode) {
    result = result.filter((draft) => draft.mode === filters.mode);
  }

  if (filters?.favorite !== undefined) {
    result = result.filter((draft) => draft.favorite === filters.favorite);
  }

  if (filters?.tags?.length) {
    result = result.filter((draft) => filters.tags?.every((tag) => draft.tags?.includes(tag)));
  }

  const sortOrder = filters?.sort_order === 'asc' ? 1 : -1;
  const sortBy = filters?.sort_by ?? 'modified';
  result.sort((left, right) => {
    const leftValue = sortBy === 'name'
      ? (left.character_name || left.seed || '')
      : (sortBy === 'created' ? left.created : left.modified) || '';
    const rightValue = sortBy === 'name'
      ? (right.character_name || right.seed || '')
      : (sortBy === 'created' ? right.created : right.modified) || '';
    return leftValue.localeCompare(rightValue) * sortOrder;
  });

  const offset = filters?.offset ?? 0;
  const limit = filters?.limit;
  if (limit !== undefined) {
    result = result.slice(offset, offset + limit);
  } else if (offset > 0) {
    result = result.slice(offset);
  }

  return result;
}

function validateDraftAssets(draft: Draft): ValidationResponse {
  const findings: string[] = [];
  const template = resolveTemplateDefinition(draft.metadata.template_name) || OFFICIAL_TEMPLATE;
  const requiredAssets = getOrderedAssets(template).filter((asset) => asset.required);
  const placeholderPatterns = [
    /\{[A-Z_][A-Z0-9_]*\}/g,
    /\(\([^\n]+?\)\)/g,
    /\[(Name|Age|Content):?[^\]]*\]/g,
  ];

  requiredAssets.forEach((asset) => {
    const content = draft.assets[asset.name];
    if (!content?.trim()) {
      findings.push(`- missing required asset ${asset.name}`);
    }
  });

  Object.entries(draft.assets).forEach(([assetName, content]) => {
    if (!content.trim()) {
      findings.push(`- ${assetName}: asset is empty`);
      return;
    }

    const matches = placeholderPatterns.flatMap((pattern) => content.match(pattern) ?? []);
    if (matches.length > 0) {
      findings.push(`- ${assetName}: unresolved placeholders ${matches.join(', ')}`);
    }
  });

  if (findings.length === 0) {
    findings.push('OK: no obvious placeholder violations found in saved assets.');
  } else {
    findings.unshift('VALIDATION FAILED');
  }

  return {
    path: draft.metadata.review_id,
    output: findings.join('\n'),
    errors: '',
    exit_code: findings[0] === 'VALIDATION FAILED' ? 1 : 0,
    success: findings[0] !== 'VALIDATION FAILED',
  };
}

function tokenizeDraft(draft: Draft): Set<string> {
  const corpus = `${draft.metadata.character_name || ''}\n${draft.metadata.seed}\n${Object.values(draft.assets).join('\n')}`
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, ' ')
    .split(/\s+/)
    .filter((token) => token.length > 3);
  return new Set(corpus);
}

function toCompatibility(score: number): SimilarityResult['compatibility'] {
  if (score >= 0.7) {
    return 'high';
  }
  if (score >= 0.45) {
    return 'medium';
  }
  return 'low';
}

function buildSimilarityResult(left: Draft, right: Draft): SimilarityResult {
  const leftTokens = tokenizeDraft(left);
  const rightTokens = tokenizeDraft(right);
  const common = [...leftTokens].filter((token) => rightTokens.has(token));
  const leftOnly = [...leftTokens].filter((token) => !rightTokens.has(token));
  const rightOnly = [...rightTokens].filter((token) => !leftTokens.has(token));
  const unionCount = new Set([...leftTokens, ...rightTokens]).size || 1;
  const score = common.length / unionCount;
  const conflictPotential = Math.min(1, (leftOnly.length + rightOnly.length) / Math.max(unionCount, 1));
  const synergyPotential = Math.min(1, score + 0.15);

  return {
    character1_name: left.metadata.character_name || left.metadata.seed,
    character2_name: right.metadata.character_name || right.metadata.seed,
    overall_score: score,
    compatibility: toCompatibility(score),
    conflict_potential: conflictPotential,
    synergy_potential: synergyPotential,
    commonalities: common.slice(0, 8),
    differences: [...leftOnly.slice(0, 4), ...rightOnly.slice(0, 4)],
    relationship_suggestions: score >= 0.6
      ? ['Shared themes suggest an easy alliance arc.', 'Overlapping traits support collaborative scenes.']
      : ['Use the contrast between their goals for tension.', 'Differences suggest rivalry or uneasy partnership.'],
    meta_analysis: {
      archetype_match: score,
      narrative_compatibility: synergyPotential,
      audience_appeal: Math.max(score, 0.35),
    },
  };
}

function buildLineageResponse(metadata: DraftMetadata[]): LineageResponse {
  const childMap = new Map<string, string[]>();
  metadata.forEach((draft) => {
    draft.parent_drafts?.forEach((parentId) => {
      const children = childMap.get(parentId) ?? [];
      children.push(draft.review_id);
      childMap.set(parentId, children);
    });
  });

  const metadataMap = new Map(metadata.map((draft) => [draft.review_id, draft]));
  const generationCache = new Map<string, number>();
  const getGeneration = (reviewId: string): number => {
    if (generationCache.has(reviewId)) {
      return generationCache.get(reviewId)!;
    }
    const draft = metadataMap.get(reviewId);
    if (!draft?.parent_drafts?.length) {
      generationCache.set(reviewId, 0);
      return 0;
    }
    const generation = 1 + Math.max(...draft.parent_drafts.map((parentId) => getGeneration(parentId)));
    generationCache.set(reviewId, generation);
    return generation;
  };

  const nodes: LineageNode[] = metadata.map((draft) => {
    const parentIds = draft.parent_drafts ?? [];
    const childIds = childMap.get(draft.review_id) ?? [];
    const generation = getGeneration(draft.review_id);
    const parentNames = parentIds.map((parentId) => metadataMap.get(parentId)?.character_name || parentId);
    const childNames = childIds.map((childId) => metadataMap.get(childId)?.character_name || childId);

    return {
      id: draft.review_id,
      review_id: draft.review_id,
      draft_name: draft.seed,
      character_name: draft.character_name || draft.seed,
      generation,
      is_root: parentIds.length === 0,
      is_leaf: childIds.length === 0,
      offspring_type: draft.offspring_type,
      mode: draft.mode,
      model: draft.model,
      created: draft.created,
      parent_ids: parentIds,
      child_ids: childIds,
      parent_names: parentNames,
      child_names: childNames,
      sibling_names: parentIds.flatMap((parentId) => (childMap.get(parentId) ?? []).filter((id) => id !== draft.review_id)).map((id) => metadataMap.get(id)?.character_name || id),
      num_ancestors: parentIds.length,
      num_descendants: childIds.length,
    };
  });

  const roots = nodes.filter((node) => node.is_root).map((node) => node.id);
  const maxGeneration = nodes.reduce((max, node) => Math.max(max, node.generation), 0);

  return {
    nodes,
    roots,
    max_generation: maxGeneration,
    stats: {
      total_characters: nodes.length,
      root_characters: nodes.filter((node) => node.is_root).length,
      leaf_characters: nodes.filter((node) => node.is_leaf).length,
      generations: maxGeneration + 1,
    },
  };
}

function createDownload(content: string, filename: string, type: string): DownloadResponse {
  return {
    blob: new Blob([content], { type }),
    filename,
    contentType: type,
  };
}

async function generateWithCurrentConfig(messages: ChatMessage[]): Promise<AsyncIterable<{ content?: string; done?: boolean }>> {
  const config = configManager.getConfig();
  const apiKeys = configManager.getApiKeys();
  const provider = config.engine_mode === 'explicit' ? config.engine : config.model;
  const engine = createEngine({
    model: config.model,
    apiKey: apiKeys.openai || apiKeys.openrouter || apiKeys.google || apiKeys.deepseek || apiKeys.zai || apiKeys.moonshot,
    provider: provider === 'openai_compatible' ? undefined : provider,
    baseUrl: config.base_url,
    temperature: config.temperature,
    maxTokens: config.max_tokens,
  });
  return engine.generateStream(messages);
}

export class CharacterGeneratorAPI {
  async getConfig(): Promise<Config> {
    return getBrowserConfig();
  }

  async updateConfig(config: Partial<Config>): Promise<Config> {
    const nextConfig = { ...config };
    if (config.api_keys) {
      configManager.setApiKeys(config.api_keys);
      delete nextConfig.api_keys;
    }
    configManager.updateConfig(nextConfig);
    return this.getConfig();
  }

  async testConnection(request: ConnectionTestRequest): Promise<ConnectionTestResult> {
    const apiKey = configManager.getApiKeys()[request.provider];
    if (!apiKey) {
      return { success: false, error: `No API key configured for ${request.provider}` };
    }

    const model = request.model || MODEL_SUGGESTIONS[request.provider as keyof typeof MODEL_SUGGESTIONS]?.[0] || getBrowserConfig().model;
    const engine = createEngine({
      model,
      apiKey,
      provider: request.provider as never,
      baseUrl: request.base_url,
    });

    return engine.testConnection();
  }

  async getThemes(): Promise<ThemePreset[]> {
    return getAllThemes();
  }

  async createTheme(theme: ThemePresetCreate): Promise<ThemePreset> {
    const themes = getCustomThemes();
    if (getAllThemes().some((candidate) => candidate.name === theme.name)) {
      throw new APIError(409, `Theme ${theme.name} already exists`);
    }

    const created: ThemePreset = {
      ...theme,
      description: theme.description || '',
      author: theme.author || '',
      tags: theme.tags || [],
      based_on: theme.based_on || '',
      is_builtin: false,
    };
    themes.push(created);
    saveCustomThemes(themes);
    return created;
  }

  async exportTheme(name: string): Promise<DownloadResponse> {
    const theme = getAllThemes().find((candidate) => candidate.name === name);
    if (!theme) {
      throw new APIError(404, `Theme ${name} not found`);
    }
    return createDownload(JSON.stringify(theme, null, 2), `${slugifyFileName(name)}.json`, 'application/json');
  }

  async importTheme(file: File, options: ThemeImportRequest = {}): Promise<ThemePreset> {
    const payload = JSON.parse(await file.text()) as ThemePreset;
    const incoming: ThemePreset = {
      ...payload,
      is_builtin: false,
    };

    const themes = getCustomThemes();
    const existingIndex = themes.findIndex((theme) => theme.name === incoming.name);
    if (existingIndex >= 0) {
      if (options.conflict_strategy === 'overwrite') {
        themes[existingIndex] = incoming;
      } else if (options.conflict_strategy === 'rename') {
        incoming.name = options.target_name || `${incoming.name}_copy`;
        themes.push(incoming);
      } else {
        throw new APIError(409, `Theme ${incoming.name} already exists`);
      }
    } else {
      themes.push(incoming);
    }

    saveCustomThemes(themes);
    return incoming;
  }

  async updateTheme(name: string, theme: ThemePresetUpdate): Promise<ThemePreset> {
    const themes = getCustomThemes();
    const index = themes.findIndex((candidate) => candidate.name === name);
    if (index < 0) {
      throw new APIError(404, `Theme ${name} is builtin or missing`);
    }
    themes[index] = { ...themes[index], ...theme };
    saveCustomThemes(themes);
    return themes[index];
  }

  async duplicateTheme(name: string, request: ThemeDuplicateRequest): Promise<ThemePreset> {
    const source = getAllThemes().find((theme) => theme.name === name);
    if (!source) {
      throw new APIError(404, `Theme ${name} not found`);
    }
    return this.createTheme({
      name: request.new_name,
      display_name: request.display_name || source.display_name,
      description: request.description || source.description,
      author: request.author || source.author,
      tags: request.tags || source.tags,
      based_on: request.based_on || source.name,
      colors: source.colors,
    });
  }

  async renameTheme(name: string, request: ThemeRenameRequest): Promise<ThemePreset> {
    return this.updateTheme(name, {
      display_name: request.display_name,
      ...(request.new_name !== name ? {} : {}),
    }).then((theme) => {
      const themes = getCustomThemes();
      const index = themes.findIndex((candidate) => candidate.name === name);
      if (index < 0) {
        throw new APIError(404, `Theme ${name} is builtin or missing`);
      }
      themes[index] = { ...theme, name: request.new_name };
      saveCustomThemes(themes);
      return themes[index];
    });
  }

  async deleteTheme(name: string): Promise<{ status: string; name: string }> {
    const themes = getCustomThemes().filter((theme) => theme.name !== name);
    saveCustomThemes(themes);
    return { status: 'deleted', name };
  }

  async getModels(provider: string): Promise<ModelsResponse> {
    const models = (MODEL_SUGGESTIONS[provider as keyof typeof MODEL_SUGGESTIONS] || []).map((id) => ({
      id,
      name: id,
      provider,
    }));
    return { provider, models, cached: true };
  }

  async refreshModels(provider: string): Promise<{ status: string; model_count: number; error?: string }> {
    const response = await this.getModels(provider);
    return { status: 'ok', model_count: response.models.length };
  }

  async generateSeeds(request: SeedGenerationRequest): Promise<SeedGenerationResponse> {
    const seeds: string[] = [];

    for await (const progress of GenerationService.generateSeeds(request)) {
      if (progress.type === 'complete' && progress.content) {
        seeds.push(...progress.content.split('\n').map((seed) => seed.trim()).filter(Boolean));
      }
    }

    return { seeds: [...new Set(seeds)] };
  }

  async getTemplates(): Promise<Template[]> {
    return getAllTemplateRecords().map((record) => record.template);
  }

  async listTemplates(): Promise<Template[]> {
    return this.getTemplates();
  }

  async getTemplate(name: string): Promise<Template> {
    const record = getTemplateRecord(name);
    if (!record) {
      throw new APIError(404, `Template ${name} not found`);
    }
    return record.template;
  }

  async getTemplateBlueprintContents(name: string): Promise<TemplateBlueprintContentsResponse> {
    const record = getTemplateRecord(name);
    if (!record) {
      throw new APIError(404, `Template ${name} not found`);
    }
    return { blueprint_contents: record.blueprint_contents };
  }

  async createTemplate(template: CreateTemplateRequest): Promise<Template> {
    const records = getStoredTemplates();
    if (records.some((record) => record.template.name === template.name)) {
      throw new APIError(409, `Template ${template.name} already exists`);
    }
    const created: Template = {
      name: template.name,
      version: template.version,
      description: template.description,
      assets: template.assets,
      is_official: false,
    };
    records.push({ template: created, blueprint_contents: template.blueprint_contents });
    saveStoredTemplates(records);
    return created;
  }

  async updateTemplate(name: string, template: UpdateTemplateRequest): Promise<Template> {
    const records = getStoredTemplates();
    const index = records.findIndex((record) => record.template.name === name);
    if (index < 0) {
      throw new APIError(404, `Custom template ${name} not found`);
    }
    records[index] = {
      template: {
        name: template.name,
        version: template.version,
        description: template.description,
        assets: template.assets,
        is_official: false,
      },
      blueprint_contents: template.blueprint_contents,
    };
    saveStoredTemplates(records);
    return records[index].template;
  }

  async deleteTemplate(name: string): Promise<{ status: string; name: string }> {
    const records = getStoredTemplates().filter((record) => record.template.name !== name);
    saveStoredTemplates(records);
    return { status: 'deleted', name };
  }

  async duplicateTemplate(name: string, request: DuplicateTemplateRequest): Promise<Template> {
    const source = getTemplateRecord(name);
    if (!source) {
      throw new APIError(404, `Template ${name} not found`);
    }
    return this.createTemplate({
      name: request.name,
      version: request.version || source.template.version,
      description: source.template.description,
      assets: source.template.assets,
      blueprint_contents: source.blueprint_contents,
    });
  }

  async validateTemplate(name: string): Promise<TemplateValidationResult> {
    const record = getTemplateRecord(name);
    if (!record) {
      throw new APIError(404, `Template ${name} not found`);
    }
    const validation = validateTemplateDefinition(record.template);
    const warnings = record.template.assets
      .filter((asset) => !record.blueprint_contents[asset.blueprint_file || `${asset.name}.md`])
      .map((asset) => `Missing blueprint content for ${asset.name}`);
    return { errors: validation.errors, warnings };
  }

  async exportTemplate(name: string): Promise<DownloadResponse> {
    const record = getTemplateRecord(name);
    if (!record) {
      throw new APIError(404, `Template ${name} not found`);
    }
    return createDownload(JSON.stringify(record, null, 2), `${slugifyFileName(name)}.json`, 'application/json');
  }

  async importTemplate(file: File): Promise<Template> {
    const parsed = JSON.parse(await file.text()) as Partial<StoredTemplateRecord & CreateTemplateRequest>;
    if ('template' in parsed && parsed.template) {
      const record = parsed as StoredTemplateRecord;
      return this.createTemplate({
        name: record.template.name,
        version: record.template.version,
        description: record.template.description,
        assets: record.template.assets,
        blueprint_contents: record.blueprint_contents,
      });
    }
    return this.createTemplate({
      name: parsed.name || file.name.replace(/\.[^.]+$/, ''),
      version: parsed.version || '1.0',
      description: parsed.description || '',
      assets: parsed.assets || [],
      blueprint_contents: parsed.blueprint_contents || {},
    } as CreateTemplateRequest);
  }

  async getDrafts(filters?: DraftFilters): Promise<DraftListResponse> {
    const allMetadata = await DraftStorage.getAllMetadata();
    const filtered = applyDraftFilters(allMetadata, filters);
    return buildDraftListResponse(filtered, filtered.length, allMetadata);
  }

  async listDrafts(filters?: DraftFilters): Promise<DraftListResponse> {
    return this.getDrafts(filters);
  }

  async getDraft(reviewId: string): Promise<Draft> {
    const draft = await DraftStorage.getDraft(reviewId);
    if (!draft) {
      throw new APIError(404, `Draft ${reviewId} not found`);
    }
    return draft;
  }

  async updateMetadata(reviewId: string, updates: Partial<DraftMetadata>): Promise<{ status: string; draft_id: string }> {
    await DraftStorage.updateMetadata(reviewId, updates);
    return { status: 'updated', draft_id: reviewId };
  }

  async deleteDraft(reviewId: string): Promise<{ status: string; draft_id: string }> {
    await DraftStorage.deleteDraft(reviewId);
    return { status: 'deleted', draft_id: reviewId };
  }

  async updateAsset(reviewId: string, assetName: string, content: string): Promise<{ status: string; draft_id: string; asset_name: string }> {
    await DraftStorage.updateAsset(reviewId, assetName, content);
    return { status: 'updated', draft_id: reviewId, asset_name: assetName };
  }

  async validateDraft(reviewId: string): Promise<ValidationResponse> {
    const draft = await this.getDraft(reviewId);
    return validateDraftAssets(draft);
  }

  async validatePath(request: ValidatePathRequest): Promise<ValidationResponse> {
    const reviewId = request.path.trim().replace(/^drafts\//, '');
    const draft = await DraftStorage.getDraft(reviewId);
    if (!draft) {
      return {
        path: request.path,
        output: 'VALIDATION FAILED\n- Browser-only mode can validate saved IndexedDB drafts by review ID only.',
        errors: '',
        exit_code: 1,
        success: false,
      };
    }
    return validateDraftAssets(draft);
  }

  generate(_request: GenerateRequest): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      for await (const progress of GenerationService.generate(_request)) {
        if (signal.aborted) {
          return;
        }
        if (progress.type === 'chunk') {
          emit('chunk', { content: progress.content || '' });
        }
        if (progress.type === 'complete') {
          const draftId = progress.asset || '';
          const draft = draftId ? await DraftStorage.getDraft(draftId) : null;
          emit('complete', {
            draft_path: draftId,
            draft_id: draftId,
            character_name: draft?.metadata.character_name,
            duration_ms: 0,
          } satisfies GenerationComplete);
        }
        if (progress.type === 'error') {
          emit('error', { error: progress.error || 'Generation failed' });
        }
      }
    });
  }

  generateAsset(request: GenerateAssetRequest): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      for await (const progress of GenerationService.generateAsset(request)) {
        if (signal.aborted) {
          return;
        }
        if (progress.type === 'chunk') {
          emit('chunk', { content: progress.content || '' });
        }
        if (progress.type === 'asset') {
          emit('complete', {
            asset_name: request.asset_name,
            content: progress.content || '',
          } satisfies GenerateAssetResponse);
        }
        if (progress.type === 'error') {
          emit('error', { error: progress.error || 'Asset generation failed' });
        }
      }
    });
  }

  previewBlueprint(request: BlueprintPreviewRequest): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      for await (const progress of GenerationService.previewBlueprint(request)) {
        if (signal.aborted) {
          return;
        }
        if (progress.type === 'chunk') {
          emit('chunk', { content: progress.content || '' });
        }
        if (progress.type === 'asset') {
          emit('complete', {
            asset_name: request.asset_name,
            content: progress.content || '',
            system_prompt: progress.systemPrompt || '',
            user_prompt: progress.userPrompt || '',
          } satisfies BlueprintPreviewResponse);
        }
        if (progress.type === 'error') {
          emit('error', { error: progress.error || 'Blueprint preview failed' });
        }
      }
    });
  }

  async finalizeGeneration(request: FinalizeGenerationRequest): Promise<GenerationComplete> {
    const reviewId = crypto.randomUUID();
    const characterName = inferCharacterDisplayNameForTemplate(request.assets, request.template);
    const draft: Draft = {
      path: reviewId,
      metadata: {
        review_id: reviewId,
        seed: request.seed,
        mode: request.mode,
        model: configManager.getConfig().model,
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        favorite: false,
        template_name: request.template,
        character_name: characterName,
      },
      assets: request.assets,
    };
    await DraftStorage.saveDraft(draft);
    return {
      draft_path: reviewId,
      draft_id: reviewId,
      character_name: characterName,
      duration_ms: 0,
    };
  }

  generateBatch(seeds: string[], request: Omit<GenerateBatchRequest, 'seeds'>): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      const runSeed = async (seed: string, index: number) => {
        emit('batch_start', { index, seed });
        try {
          let draftId = '';
          for await (const progress of GenerationService.generate({
            seed,
            mode: request.mode,
            template: request.template,
          })) {
            if (signal.aborted) {
              return;
            }
            if (progress.type === 'complete') {
              draftId = progress.asset || '';
            }
          }
          emit('batch_complete', { index, seed, draft_path: draftId });
        } catch (error) {
          emit('batch_error', { index, seed, error: error instanceof Error ? error.message : 'Batch generation failed' });
        }
      };

      if (request.parallel) {
        let nextIndex = 0;
        const workerCount = Math.min(Math.max(request.max_concurrent ?? 3, 1), seeds.length || 1);
        await Promise.all(Array.from({ length: workerCount }, async () => {
          while (!signal.aborted) {
            const index = nextIndex;
            nextIndex += 1;
            if (index >= seeds.length) {
              return;
            }
            await runSeed(seeds[index], index);
          }
        }));
      } else {
        for (let index = 0; index < seeds.length; index += 1) {
          if (signal.aborted) {
            return;
          }
          await runSeed(seeds[index], index);
        }
      }

      if (signal.aborted) {
        return;
      }

      emit('complete', { status: 'done' });
    });
  }

  async getLineage(): Promise<LineageResponse> {
    const metadata = await DraftStorage.getAllMetadata();
    return buildLineageResponse(metadata);
  }

  async analyzeSimilarity(request: SimilarityRequest): Promise<SimilarityResult> {
    const left = await this.getDraft(request.draft1_id);
    const right = await this.getDraft(request.draft2_id);
    const baseResult = buildSimilarityResult(left, right);

    if (!request.include_llm_analysis) {
      return baseResult;
    }

    try {
      const analysis = await GenerationService.analyzeSimilarity(request.draft1_id, request.draft2_id) as {
        narrative_dynamics?: unknown;
        relationship_arc?: unknown;
        story_opportunities?: unknown;
        scene_suggestions?: unknown;
        raw?: unknown;
      };

      const storyHooks = Array.isArray(analysis.story_opportunities)
        ? analysis.story_opportunities.map((item) => String(item)).slice(0, 4)
        : baseResult.relationship_suggestions;
      const sceneSuggestions = Array.isArray(analysis.scene_suggestions)
        ? analysis.scene_suggestions.map((item) => String(item)).slice(0, 3)
        : baseResult.relationship_suggestions;
      const relationshipPotential = [analysis.narrative_dynamics, analysis.relationship_arc]
        .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
        .join('\n\n') || (typeof analysis.raw === 'string' ? analysis.raw : 'LLM analysis unavailable.');

      return {
        ...baseResult,
        relationship_suggestions: sceneSuggestions,
        llm_analysis: {
          relationship_potential: relationshipPotential,
          conflict_areas: baseResult.differences.slice(0, 4),
          synergy_areas: baseResult.commonalities.slice(0, 4),
          story_hooks: storyHooks,
        },
      };
    } catch {
      return baseResult;
    }
  }

  generateOffspring(request: OffspringRequest): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      for await (const progress of GenerationService.generateOffspring(request)) {
        if (signal.aborted) {
          return;
        }
        if (progress.type === 'chunk') {
          emit('chunk', { content: progress.content || '' });
        }
        if (progress.type === 'complete') {
          const draftId = progress.asset || '';
          const draft = draftId ? await DraftStorage.getDraft(draftId) : null;
          emit('complete', {
            draft_id: draftId,
            character_name: draft?.metadata.character_name,
          });
        }
        if (progress.type === 'error') {
          emit('error', { error: progress.error || 'Offspring generation failed' });
        }
      }
    });
  }

  async getExportPresets(): Promise<ExportPresetSummary[]> {
    return EXPORT_PRESETS;
  }

  async exportDraft(request: ExportRequest): Promise<DownloadResponse> {
    const draft = await this.getDraft(request.draft_id);
    const preset = request.preset || 'json';
    const includeMetadata = request.include_metadata !== false;
    const fileBase = slugifyFileName(draft.metadata.character_name || draft.metadata.seed || draft.metadata.review_id);

    if (preset === 'text') {
      const content = Object.entries(draft.assets)
        .map(([assetName, value]) => `## ${assetName}\n\n${value}`)
        .join('\n\n');
      return createDownload(content, `${fileBase}.txt`, 'text/plain');
    }

    if (preset === 'combined') {
      const sections = [
        `# ${draft.metadata.character_name || draft.metadata.seed}`,
        includeMetadata ? `## Metadata\n\n${JSON.stringify(draft.metadata, null, 2)}` : '',
        ...Object.entries(draft.assets).map(([assetName, value]) => `## ${assetName}\n\n${value}`),
      ].filter(Boolean);
      return createDownload(sections.join('\n\n'), `${fileBase}.md`, 'text/markdown');
    }

    return createDownload(JSON.stringify({ metadata: includeMetadata ? draft.metadata : undefined, assets: draft.assets }, null, 2), `${fileBase}.json`, 'application/json');
  }

  async getBlueprints(): Promise<BlueprintList> {
    const values = [...getBlueprintCatalog().values()];
    return {
      core: values.filter((blueprint) => blueprint.category === 'core'),
      system: values.filter((blueprint) => blueprint.category === 'system'),
      templates: {
        local: values.filter((blueprint) => blueprint.category === 'template'),
      },
      examples: values.filter((blueprint) => blueprint.category === 'example'),
    };
  }

  async getBlueprint(path: string): Promise<Blueprint> {
    const blueprint = getBlueprintCatalog().get(path);
    if (!blueprint) {
      throw new APIError(404, `Blueprint ${path} not found`);
    }
    return blueprint;
  }

  async updateBlueprint(path: string, content: string): Promise<Blueprint> {
    const overrides = getBlueprintOverrides();
    overrides[path] = content;
    saveBlueprintOverrides(overrides);
    return this.getBlueprint(path);
  }

  chat(request: ChatRequest): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      const draft = request.draft_id ? await DraftStorage.getDraft(request.draft_id) : null;
      const contextParts = [
        draft ? `Current draft metadata: ${JSON.stringify(draft.metadata)}` : '',
        request.context_asset && draft?.assets[request.context_asset] ? `Focused asset (${request.context_asset}):\n${draft.assets[request.context_asset]}` : '',
        request.screen_context ? `Screen context: ${JSON.stringify(request.screen_context)}` : '',
      ].filter(Boolean);

      const messages: ChatMessage[] = [
        {
          role: 'system',
          content: 'You are the in-app assistant for a browser-only character generator. Be concise and practical. Use provided draft or screen context when relevant.',
        },
        ...(contextParts.length > 0 ? [{ role: 'system' as const, content: contextParts.join('\n\n') }] : []),
        ...request.messages,
      ];

      const stream = await generateWithCurrentConfig(messages);
      let fullContent = '';
      for await (const chunk of stream) {
        if (signal.aborted) {
          return;
        }
        if (chunk.content) {
          fullContent += chunk.content;
          emit('chunk', { content: chunk.content });
        }
        if (chunk.done) {
          break;
        }
      }
      emit('complete', { content: fullContent });
    });
  }

  refine(request: RefineRequest): BrowserStream {
    return new BrowserStream(async ({ emit, signal }) => {
      const draft = await this.getDraft(request.draft_id);
      const assetContent = draft.assets[request.asset];
      if (!assetContent) {
        throw new APIError(404, `Asset ${request.asset} not found in draft`);
      }

      const messages: ChatMessage[] = [
        {
          role: 'system',
          content: 'Rewrite the provided asset according to the user request. Return only the revised asset content with no extra commentary.',
        },
        {
          role: 'user',
          content: `Draft seed: ${draft.metadata.seed}\nAsset: ${request.asset}\n\nCurrent content:\n${assetContent}\n\nRevision request:\n${request.message}`,
        },
      ];

      const stream = await generateWithCurrentConfig(messages);
      let fullContent = '';
      for await (const chunk of stream) {
        if (signal.aborted) {
          return;
        }
        if (chunk.content) {
          fullContent += chunk.content;
          emit('chunk', { content: chunk.content });
        }
        if (chunk.done) {
          break;
        }
      }
      emit('complete', { content: fullContent });
    });
  }
}

export const api = new CharacterGeneratorAPI();
