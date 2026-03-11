import {
  OFFICIAL_TEMPLATE,
  detectProviderFromModel,
  validateTemplate as validateTemplateDefinition,
  getOrderedAssets,
  type ApiKeys,
  type Blueprint,
  type BlueprintList,
  type ChatMessage,
  type ChatRequest,
  type Config,
  type ConnectionTestRequest,
  type ConnectionTestResult,
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
  type LLMProvider,
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
import { MODEL_SUGGESTIONS, buildProviderHeaders, createEngine, getDefaultBaseUrl } from './llm/factory.js';
import { configManager } from './config/manager.js';
import { DraftStorage } from './storage/draft-db.js';
import { GenerationService } from './services/generation.js';
import {
  type StoredTemplateRecord,
  getAllTemplateRecords,
  getBlueprintCatalog,
  getBlueprintOverrides,
  getStoredTemplateRecord,
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

type ChunkStreamData = { content: string };
type ErrorStreamData = { error: string };
type BatchStartStreamData = { index: number; seed: string };
type BatchCompleteStreamData = { index: number; seed: string; draft_path: string };
type BatchErrorStreamData = { index: number; seed: string; error: string };
type CompleteStreamData =
  | GenerationComplete
  | GenerateAssetResponse
  | BlueprintPreviewResponse
  | { draft_id: string; character_name?: string }
  | { content: string }
  | { status: 'done' };

type StreamEventMap = {
  chunk: ChunkStreamData;
  complete: CompleteStreamData;
  error: ErrorStreamData;
  batch_start: BatchStartStreamData;
  batch_complete: BatchCompleteStreamData;
  batch_error: BatchErrorStreamData;
};

type StreamEvent = {
  [EventType in StreamEventType]: {
    event: EventType;
    data: StreamEventMap[EventType];
  }
}[StreamEventType];

type StreamReader = (event: StreamEvent) => void;

type BlueprintPreviewRequest = GenerateAssetRequest & {
  blueprint_content: string;
};

type BlueprintPreviewResponse = GenerateAssetResponse & {
  system_prompt: string;
  user_prompt: string;
};

const CUSTOM_THEMES_STORAGE_KEY = 'eidolon.web.themes.custom';
const LEGACY_CUSTOM_THEMES_STORAGE_KEYS = ['bpui.web.themes.custom'];
const MODEL_CACHE_TTL_MS = 5 * 60 * 1000;

type CachedModelsEntry = {
  response: ModelsResponse;
  cachedAt: number;
};

type OpenAICompatibleModelsPayload = {
  data?: Array<{
    id?: string;
    name?: string;
    context_length?: number;
    architecture?: {
      input_modalities?: string[];
    };
    supported_parameters?: string[];
  }>;
};

const modelsCache = new Map<string, CachedModelsEntry>();

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

function builtinTheme(theme: Omit<ThemePreset, 'author' | 'is_builtin'> & { author?: string }): ThemePreset {
  return {
    author: 'Eidolon Simulacra',
    is_builtin: true,
    ...theme,
  };
}

const builtinThemes: ThemePreset[] = [
  builtinTheme({
    name: 'dark',
    display_name: 'Dark',
    description: 'Default dark theme for browser-only mode.',
    tags: ['builtin', 'dark'],
    based_on: '',
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
    },
  }),
  builtinTheme({
    name: 'light',
    display_name: 'Light',
    description: 'Default light theme for browser-only mode.',
    tags: ['builtin', 'light'],
    based_on: '',
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
    },
  }),
  builtinTheme({
    name: 'nyx',
    display_name: 'Nyx',
    description: 'High-contrast theme tuned for the blueprint workflow.',
    tags: ['builtin', 'editorial'],
    based_on: 'dark',
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
    },
  }),
  builtinTheme({
    name: 'midnight',
    display_name: 'Midnight',
    description: 'Deep blue ocean theme with cyan accents.',
    tags: ['builtin', 'dark', 'blue'],
    based_on: 'dark',
    colors: {
      background: '#0a1929',
      text: '#b2d4f0',
      accent: '#00b4d8',
      button: '#014361',
      button_text: '#caf0f8',
      border: '#1d3557',
      highlight: '#48cae4',
      window: '#051923',
      tok_brackets: '#00b4d8',
      tok_asterisk: '#90e0ef',
      tok_parentheses: '#f48c06',
      tok_double_brackets: '#06ffa5',
      tok_curly_braces: '#00b4d8',
      tok_pipes: '#48cae4',
      tok_at_sign: '#f77f00',
      muted_text: '#6b8aa3',
      surface: '#0f2638',
      success_bg: '#1b4332',
      danger_bg: '#641220',
      accent_bg: '#014361',
      accent_title: '#48cae4',
      success_text: '#06ffa5',
      error_text: '#ff6b6b',
      warning_text: '#f48c06',
    },
  }),
  builtinTheme({
    name: 'ember',
    display_name: 'Ember',
    description: 'Warm theme with orange and amber tones.',
    tags: ['builtin', 'warm', 'orange'],
    based_on: 'dark',
    colors: {
      background: '#1a0f0a',
      text: '#ffd8b8',
      accent: '#ff6b35',
      button: '#c44536',
      button_text: '#fff8f0',
      border: '#5e1914',
      highlight: '#ff8c42',
      window: '#100a07',
      tok_brackets: '#ff6b35',
      tok_asterisk: '#ffa07a',
      tok_parentheses: '#ffb627',
      tok_double_brackets: '#7bed9f',
      tok_curly_braces: '#ff6348',
      tok_pipes: '#feca57',
      tok_at_sign: '#ff4757',
      muted_text: '#a67c52',
      surface: '#261612',
      success_bg: '#2d4a2b',
      danger_bg: '#5e1914',
      accent_bg: '#c44536',
      accent_title: '#ff8c42',
      success_text: '#7bed9f',
      error_text: '#ff4757',
      warning_text: '#feca57',
    },
  }),
  builtinTheme({
    name: 'forest',
    display_name: 'Forest',
    description: 'Natural green theme inspired by woodland twilight.',
    tags: ['builtin', 'green', 'nature'],
    based_on: 'dark',
    colors: {
      background: '#0d1b0f',
      text: '#d4f1d4',
      accent: '#4ecca3',
      button: '#2d5f3f',
      button_text: '#e8f5e8',
      border: '#1e4620',
      highlight: '#7bed9f',
      window: '#081108',
      tok_brackets: '#4ecca3',
      tok_asterisk: '#7bed9f',
      tok_parentheses: '#ffd93d',
      tok_double_brackets: '#6bcf7f',
      tok_curly_braces: '#48c774',
      tok_pipes: '#95e1d3',
      tok_at_sign: '#f8b500',
      muted_text: '#6b8f71',
      surface: '#152518',
      success_bg: '#2d5f3f',
      danger_bg: '#5c2a2a',
      accent_bg: '#2d5f3f',
      accent_title: '#7bed9f',
      success_text: '#95e1d3',
      error_text: '#ff6b6b',
      warning_text: '#ffd93d',
    },
  }),
  builtinTheme({
    name: 'mono',
    display_name: 'Monochrome',
    description: 'Clean grayscale theme for minimal distraction.',
    tags: ['builtin', 'minimal', 'grayscale'],
    based_on: 'dark',
    colors: {
      background: '#1c1c1c',
      text: '#e0e0e0',
      accent: '#757575',
      button: '#424242',
      button_text: '#ffffff',
      border: '#505050',
      highlight: '#9e9e9e',
      window: '#141414',
      tok_brackets: '#bdbdbd',
      tok_asterisk: '#9e9e9e',
      tok_parentheses: '#757575',
      tok_double_brackets: '#e0e0e0',
      tok_curly_braces: '#a0a0a0',
      tok_pipes: '#c0c0c0',
      tok_at_sign: '#888888',
      muted_text: '#707070',
      surface: '#242424',
      success_bg: '#3a3a3a',
      danger_bg: '#2e2e2e',
      accent_bg: '#424242',
      accent_title: '#9e9e9e',
      success_text: '#c0c0c0',
      error_text: '#a0a0a0',
      warning_text: '#b0b0b0',
    },
  }),
  builtinTheme({
    name: 'solarized_dark',
    display_name: 'Solarized Dark',
    description: 'Popular Solarized color scheme with reduced eye strain.',
    tags: ['builtin', 'dark', 'solarized'],
    based_on: 'dark',
    colors: {
      background: '#002b36',
      text: '#839496',
      accent: '#268bd2',
      button: '#073642',
      button_text: '#eee8d5',
      border: '#586e75',
      highlight: '#2aa198',
      window: '#001e26',
      tok_brackets: '#dc322f',
      tok_asterisk: '#268bd2',
      tok_parentheses: '#cb4b16',
      tok_double_brackets: '#859900',
      tok_curly_braces: '#d33682',
      tok_pipes: '#2aa198',
      tok_at_sign: '#b58900',
      muted_text: '#586e75',
      surface: '#073642',
      success_bg: '#324d32',
      danger_bg: '#4d2626',
      accent_bg: '#073642',
      accent_title: '#2aa198',
      success_text: '#859900',
      error_text: '#dc322f',
      warning_text: '#b58900',
    },
  }),
  builtinTheme({
    name: 'trans_flag',
    display_name: 'Trans Flag',
    description: 'Soft cyan and pink palette with neutral dark surfaces.',
    tags: ['builtin', 'support', 'bright'],
    based_on: 'dark',
    colors: {
      background: '#2e2e2e',
      text: '#ffffff',
      accent: '#5bcefa',
      button: '#f5a9b8',
      button_text: '#2e2e2e',
      border: '#cccccc',
      highlight: '#5bcefa',
      window: '#3e3e3e',
      tok_brackets: '#5bcefa',
      tok_asterisk: '#f5a9b8',
      tok_parentheses: '#5bcefa',
      tok_double_brackets: '#f5a9b8',
      tok_curly_braces: '#ffffff',
      tok_pipes: '#5bcefa',
      tok_at_sign: '#f5a9b8',
      muted_text: '#cccccc',
      surface: '#3e3e3e',
      success_bg: '#5bcefa',
      danger_bg: '#f5a9b8',
      accent_bg: '#3e3e3e',
      accent_title: '#5bcefa',
      success_text: '#2e2e2e',
      error_text: '#2e2e2e',
      warning_text: '#2e2e2e',
    },
  }),
  builtinTheme({
    name: 'blood_for_the_blood_god',
    display_name: 'Blood for the Blood God',
    description: 'A blood red theme with bronze accents.',
    tags: ['builtin', 'warhammer', 'chaos', 'khorne'],
    based_on: 'dark',
    colors: {
      background: '#200000',
      text: '#ffcccc',
      accent: '#cd7f32',
      button: '#600000',
      button_text: '#ffcccc',
      border: '#400000',
      highlight: '#ff0000',
      window: '#200000',
      tok_brackets: '#e00000',
      tok_asterisk: '#c00000',
      tok_parentheses: '#a00000',
      tok_double_brackets: '#e00000',
      tok_curly_braces: '#c00000',
      tok_pipes: '#a00000',
      tok_at_sign: '#ff0000',
      muted_text: '#996666',
      surface: '#400000',
      success_bg: '#600000',
      danger_bg: '#800000',
      accent_bg: '#a06629',
      accent_title: '#cd7f32',
      success_text: '#ffcccc',
      error_text: '#ffcccc',
      warning_text: '#ffcccc',
    },
  }),
  builtinTheme({
    name: 'silent_king',
    display_name: 'Silent King',
    description: 'A near-black theme with tomb-world green glow.',
    tags: ['builtin', 'warhammer', 'necron', 'green'],
    based_on: 'dark',
    colors: {
      background: '#010a01',
      text: '#a0e0a0',
      accent: '#00ff00',
      button: '#004000',
      button_text: '#a0e0a0',
      border: '#002000',
      highlight: '#00ff00',
      window: '#010501',
      tok_brackets: '#00c000',
      tok_asterisk: '#00a000',
      tok_parentheses: '#008000',
      tok_double_brackets: '#00c000',
      tok_curly_braces: '#00a000',
      tok_pipes: '#008000',
      tok_at_sign: '#00ff00',
      muted_text: '#609060',
      surface: '#010a01',
      success_bg: '#004000',
      danger_bg: '#006000',
      accent_bg: '#004000',
      accent_title: '#00ff00',
      success_text: '#a0e0a0',
      error_text: '#a0e0a0',
      warning_text: '#a0e0a0',
    },
  }),
  builtinTheme({
    name: 'ultramar',
    display_name: 'Ultramar',
    description: 'Cerulean armor, parchment ivory, and gold command trim.',
    tags: ['builtin', 'warhammer', 'space-marine', 'blue'],
    based_on: 'dark',
    colors: {
      background: '#08172f',
      text: '#e8eef7',
      accent: '#d4a72c',
      button: '#12396b',
      button_text: '#f8fafc',
      border: '#245089',
      highlight: '#4da3ff',
      window: '#0b2140',
      tok_brackets: '#60a5fa',
      tok_asterisk: '#facc15',
      tok_parentheses: '#fb7185',
      tok_double_brackets: '#93c5fd',
      tok_curly_braces: '#67e8f9',
      tok_pipes: '#c084fc',
      tok_at_sign: '#f97316',
      muted_text: '#93a9c4',
      surface: '#102949',
      success_bg: '#163b2a',
      danger_bg: '#481818',
      accent_bg: '#3d2b05',
      accent_title: '#fde68a',
      success_text: '#86efac',
      error_text: '#fca5a5',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'imperial_fists',
    display_name: 'Imperial Fists',
    description: 'Siege yellow palette with navy shadows and hazard-strip energy.',
    tags: ['builtin', 'warhammer', 'space-marine', 'yellow'],
    based_on: 'dark',
    colors: {
      background: '#1c1603',
      text: '#fff6cc',
      accent: '#ffd100',
      button: '#7c6200',
      button_text: '#fffbea',
      border: '#8e740f',
      highlight: '#ffe66d',
      window: '#241d05',
      tok_brackets: '#ffd100',
      tok_asterisk: '#60a5fa',
      tok_parentheses: '#fb923c',
      tok_double_brackets: '#fde68a',
      tok_curly_braces: '#facc15',
      tok_pipes: '#93c5fd',
      tok_at_sign: '#f87171',
      muted_text: '#c5b671',
      surface: '#302608',
      success_bg: '#2d3d1b',
      danger_bg: '#51210f',
      accent_bg: '#483701',
      accent_title: '#fff3a3',
      success_text: '#bef264',
      error_text: '#fca5a5',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'raven_guard',
    display_name: 'Raven Guard',
    description: 'Matte black surfaces with pale steel highlights and a covert red ping.',
    tags: ['builtin', 'warhammer', 'space-marine', 'stealth'],
    based_on: 'dark',
    colors: {
      background: '#09090b',
      text: '#e7e5e4',
      accent: '#d4d4d8',
      button: '#18181b',
      button_text: '#fafafa',
      border: '#3f3f46',
      highlight: '#a1a1aa',
      window: '#0f1014',
      tok_brackets: '#e4e4e7',
      tok_asterisk: '#f87171',
      tok_parentheses: '#c084fc',
      tok_double_brackets: '#93c5fd',
      tok_curly_braces: '#86efac',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#fb7185',
      muted_text: '#71717a',
      surface: '#14151a',
      success_bg: '#14231a',
      danger_bg: '#3f1014',
      accent_bg: '#20232a',
      accent_title: '#f4f4f5',
      success_text: '#86efac',
      error_text: '#fda4af',
      warning_text: '#fdba74',
    },
  }),
  builtinTheme({
    name: 'salamanders',
    display_name: 'Salamanders',
    description: 'Volcanic green palette with lava orange contrast.',
    tags: ['builtin', 'warhammer', 'space-marine', 'green'],
    based_on: 'dark',
    colors: {
      background: '#08130e',
      text: '#d9f4dd',
      accent: '#ff7a00',
      button: '#1c5b34',
      button_text: '#f7fff8',
      border: '#2f7d4e',
      highlight: '#34d399',
      window: '#0d1d16',
      tok_brackets: '#4ade80',
      tok_asterisk: '#fb923c',
      tok_parentheses: '#facc15',
      tok_double_brackets: '#86efac',
      tok_curly_braces: '#22c55e',
      tok_pipes: '#2dd4bf',
      tok_at_sign: '#f97316',
      muted_text: '#7ca58a',
      surface: '#11251b',
      success_bg: '#123825',
      danger_bg: '#4a1d11',
      accent_bg: '#4a2205',
      accent_title: '#fdba74',
      success_text: '#bbf7d0',
      error_text: '#fdba74',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'iron_warriors',
    display_name: 'Iron Warriors',
    description: 'Gunmetal, hazard yellow, and industrial rust.',
    tags: ['builtin', 'warhammer', 'chaos', 'industrial'],
    based_on: 'dark',
    colors: {
      background: '#101114',
      text: '#d8d7d2',
      accent: '#facc15',
      button: '#3a3d42',
      button_text: '#fffce8',
      border: '#5a5f69',
      highlight: '#fde047',
      window: '#17191d',
      tok_brackets: '#facc15',
      tok_asterisk: '#fb7185',
      tok_parentheses: '#fb923c',
      tok_double_brackets: '#d4d4d8',
      tok_curly_braces: '#93c5fd',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#f97316',
      muted_text: '#8f9098',
      surface: '#20242a',
      success_bg: '#243326',
      danger_bg: '#48211a',
      accent_bg: '#43370a',
      accent_title: '#fef08a',
      success_text: '#86efac',
      error_text: '#fdba74',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'mechanicus_brass',
    display_name: 'Mechanicus Brass',
    description: 'Mars red, soot black, and worn brass for forge-heavy work.',
    tags: ['builtin', 'warhammer', 'mechanicus', 'red'],
    based_on: 'dark',
    colors: {
      background: '#130909',
      text: '#f1d9c3',
      accent: '#c98b2b',
      button: '#611616',
      button_text: '#fff4e6',
      border: '#7f2a1d',
      highlight: '#e2a74a',
      window: '#1a0d0d',
      tok_brackets: '#f87171',
      tok_asterisk: '#fbbf24',
      tok_parentheses: '#fdba74',
      tok_double_brackets: '#fca5a5',
      tok_curly_braces: '#fcd34d',
      tok_pipes: '#93c5fd',
      tok_at_sign: '#fb7185',
      muted_text: '#a98a75',
      surface: '#251212',
      success_bg: '#1f3424',
      danger_bg: '#4c1515',
      accent_bg: '#3f2610',
      accent_title: '#f6d28b',
      success_text: '#86efac',
      error_text: '#fca5a5',
      warning_text: '#fcd34d',
    },
  }),
  builtinTheme({
    name: 'sororitas_rose',
    display_name: 'Sororitas Rose',
    description: 'Ivory, cathedral black, and stained-glass crimson.',
    tags: ['builtin', 'warhammer', 'imperium', 'gothic'],
    based_on: 'dark',
    colors: {
      background: '#141112',
      text: '#f7ede8',
      accent: '#b91c1c',
      button: '#3c1318',
      button_text: '#fff7f5',
      border: '#6d2730',
      highlight: '#fb7185',
      window: '#1b1718',
      tok_brackets: '#fda4af',
      tok_asterisk: '#facc15',
      tok_parentheses: '#fdba74',
      tok_double_brackets: '#f5f5f4',
      tok_curly_braces: '#c084fc',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#ef4444',
      muted_text: '#b2a29c',
      surface: '#231d1f',
      success_bg: '#203326',
      danger_bg: '#4b1319',
      accent_bg: '#3b1016',
      accent_title: '#fecdd3',
      success_text: '#bbf7d0',
      error_text: '#fecaca',
      warning_text: '#fdba74',
    },
  }),
  builtinTheme({
    name: 'cadia_stands',
    display_name: 'Cadia Stands',
    description: 'Military olive, field khaki, and disciplined gold signals.',
    tags: ['builtin', 'warhammer', 'imperium', 'guard'],
    based_on: 'dark',
    colors: {
      background: '#11160f',
      text: '#e6ecd8',
      accent: '#c8a54b',
      button: '#3a4b2a',
      button_text: '#f8faee',
      border: '#556a3e',
      highlight: '#a3c76d',
      window: '#171d14',
      tok_brackets: '#a3c76d',
      tok_asterisk: '#facc15',
      tok_parentheses: '#fb923c',
      tok_double_brackets: '#d9f99d',
      tok_curly_braces: '#86efac',
      tok_pipes: '#93c5fd',
      tok_at_sign: '#f87171',
      muted_text: '#99a58b',
      surface: '#20281b',
      success_bg: '#243624',
      danger_bg: '#4a2218',
      accent_bg: '#3e3413',
      accent_title: '#f5e6b1',
      success_text: '#bbf7d0',
      error_text: '#fca5a5',
      warning_text: '#fde68a',
    },
  }),
  builtinTheme({
    name: 'krieg_ash',
    display_name: 'Krieg Ash',
    description: 'Trenchcoat slate, muddy blue, and mask-lens amber.',
    tags: ['builtin', 'warhammer', 'imperium', 'guard'],
    based_on: 'dark',
    colors: {
      background: '#101417',
      text: '#dae1e5',
      accent: '#d1a449',
      button: '#3a4854',
      button_text: '#f6f7f8',
      border: '#55616c',
      highlight: '#9db7c7',
      window: '#151b20',
      tok_brackets: '#93c5fd',
      tok_asterisk: '#facc15',
      tok_parentheses: '#fb923c',
      tok_double_brackets: '#cbd5e1',
      tok_curly_braces: '#86efac',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#f87171',
      muted_text: '#8e9aa3',
      surface: '#1d242a',
      success_bg: '#233127',
      danger_bg: '#48231c',
      accent_bg: '#3f3118',
      accent_title: '#f4deb1',
      success_text: '#bbf7d0',
      error_text: '#fdba74',
      warning_text: '#fde68a',
    },
  }),
  builtinTheme({
    name: 'thousand_sons',
    display_name: 'Thousand Sons',
    description: 'Arcane cobalt with turquoise sorcery and gilded trim.',
    tags: ['builtin', 'warhammer', 'chaos', 'arcane'],
    based_on: 'dark',
    colors: {
      background: '#081427',
      text: '#dce9ff',
      accent: '#22d3ee',
      button: '#12335f',
      button_text: '#f0f9ff',
      border: '#1d4f91',
      highlight: '#7dd3fc',
      window: '#0d1b35',
      tok_brackets: '#38bdf8',
      tok_asterisk: '#facc15',
      tok_parentheses: '#fb7185',
      tok_double_brackets: '#67e8f9',
      tok_curly_braces: '#a78bfa',
      tok_pipes: '#22d3ee',
      tok_at_sign: '#f97316',
      muted_text: '#96a9c6',
      surface: '#132346',
      success_bg: '#14312c',
      danger_bg: '#451b2f',
      accent_bg: '#10354d',
      accent_title: '#cffafe',
      success_text: '#99f6e4',
      error_text: '#f9a8d4',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'drukhari_raid',
    display_name: 'Drukhari Raid',
    description: 'Poison teal, blade violet, and void-black lacquer.',
    tags: ['builtin', 'warhammer', 'aeldari', 'neon'],
    based_on: 'dark',
    colors: {
      background: '#09070f',
      text: '#ece7ff',
      accent: '#14b8a6',
      button: '#2c1144',
      button_text: '#f5f3ff',
      border: '#5b21b6',
      highlight: '#5eead4',
      window: '#100b1a',
      tok_brackets: '#2dd4bf',
      tok_asterisk: '#c084fc',
      tok_parentheses: '#f472b6',
      tok_double_brackets: '#67e8f9',
      tok_curly_braces: '#a78bfa',
      tok_pipes: '#22d3ee',
      tok_at_sign: '#fb7185',
      muted_text: '#9d94b8',
      surface: '#170f25',
      success_bg: '#123028',
      danger_bg: '#43162e',
      accent_bg: '#102f31',
      accent_title: '#ccfbf1',
      success_text: '#99f6e4',
      error_text: '#f9a8d4',
      warning_text: '#f0abfc',
    },
  }),
  builtinTheme({
    name: 'ork_waaagh',
    display_name: 'Ork Waaagh!',
    description: 'Scrap metal, noisy green, and red-goes-fasta contrast.',
    tags: ['builtin', 'warhammer', 'ork', 'high-energy'],
    based_on: 'dark',
    colors: {
      background: '#11140c',
      text: '#e2f5b8',
      accent: '#67e01f',
      button: '#734116',
      button_text: '#fff7ed',
      border: '#4b5f1a',
      highlight: '#84cc16',
      window: '#181d10',
      tok_brackets: '#84cc16',
      tok_asterisk: '#ef4444',
      tok_parentheses: '#f97316',
      tok_double_brackets: '#bef264',
      tok_curly_braces: '#facc15',
      tok_pipes: '#22d3ee',
      tok_at_sign: '#fb7185',
      muted_text: '#9eb279',
      surface: '#232813',
      success_bg: '#26401d',
      danger_bg: '#5a2314',
      accent_bg: '#293a12',
      accent_title: '#d9f99d',
      success_text: '#d9f99d',
      error_text: '#fdba74',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'tau_sept',
    display_name: 'Tau Sept',
    description: 'Clean ochre, alloy grey, and cool interface blue.',
    tags: ['builtin', 'warhammer', 'tau', 'clean'],
    based_on: 'dark',
    colors: {
      background: '#11161a',
      text: '#e8edf0',
      accent: '#f59e0b',
      button: '#41525f',
      button_text: '#f8fafc',
      border: '#617688',
      highlight: '#7dd3fc',
      window: '#161d23',
      tok_brackets: '#93c5fd',
      tok_asterisk: '#fbbf24',
      tok_parentheses: '#fb923c',
      tok_double_brackets: '#cbd5e1',
      tok_curly_braces: '#67e8f9',
      tok_pipes: '#38bdf8',
      tok_at_sign: '#f97316',
      muted_text: '#9aa8b2',
      surface: '#202930',
      success_bg: '#1e3430',
      danger_bg: '#4a2218',
      accent_bg: '#41320c',
      accent_title: '#fde68a',
      success_text: '#99f6e4',
      error_text: '#fdba74',
      warning_text: '#fde047',
    },
  }),
  builtinTheme({
    name: 'tyranid_hive',
    display_name: 'Tyranid Hive',
    description: 'Bone chitin, toxic magenta, and abyssal carapace purple.',
    tags: ['builtin', 'warhammer', 'tyranid', 'organic'],
    based_on: 'dark',
    colors: {
      background: '#120c18',
      text: '#f3e8ff',
      accent: '#f472b6',
      button: '#3f1b4d',
      button_text: '#fff7fb',
      border: '#6b2d78',
      highlight: '#f9a8d4',
      window: '#1a1222',
      tok_brackets: '#f5d0fe',
      tok_asterisk: '#fb7185',
      tok_parentheses: '#fdba74',
      tok_double_brackets: '#e9d5ff',
      tok_curly_braces: '#c084fc',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#f43f5e',
      muted_text: '#b7a3c4',
      surface: '#24182f',
      success_bg: '#243321',
      danger_bg: '#4f1733',
      accent_bg: '#441a3d',
      accent_title: '#fbcfe8',
      success_text: '#bef264',
      error_text: '#fda4af',
      warning_text: '#fdba74',
    },
  }),
  builtinTheme({
    name: 'genestealer_cult',
    display_name: 'Genestealer Cult',
    description: 'Industrial violet with warning pink and cult neon accents.',
    tags: ['builtin', 'warhammer', 'tyranid', 'industrial'],
    based_on: 'dark',
    colors: {
      background: '#0f1020',
      text: '#ede9fe',
      accent: '#8b5cf6',
      button: '#312e81',
      button_text: '#f5f3ff',
      border: '#5b4bc4',
      highlight: '#c084fc',
      window: '#151730',
      tok_brackets: '#a78bfa',
      tok_asterisk: '#fb7185',
      tok_parentheses: '#f97316',
      tok_double_brackets: '#ddd6fe',
      tok_curly_braces: '#67e8f9',
      tok_pipes: '#c084fc',
      tok_at_sign: '#f43f5e',
      muted_text: '#a6a1c9',
      surface: '#1d2040',
      success_bg: '#203229',
      danger_bg: '#47152a',
      accent_bg: '#2e255d',
      accent_title: '#e9d5ff',
      success_text: '#99f6e4',
      error_text: '#fda4af',
      warning_text: '#fdba74',
    },
  }),
  builtinTheme({
    name: 'golden_throne',
    display_name: 'Golden Throne',
    description: 'Black marble, relic gold, and cathedral ivory.',
    tags: ['builtin', 'warhammer', 'imperium', 'gold'],
    based_on: 'dark',
    colors: {
      background: '#110f0d',
      text: '#f6efe2',
      accent: '#d4af37',
      button: '#4a3510',
      button_text: '#fffbeb',
      border: '#6f5521',
      highlight: '#f6d365',
      window: '#171411',
      tok_brackets: '#fcd34d',
      tok_asterisk: '#fda4af',
      tok_parentheses: '#fdba74',
      tok_double_brackets: '#fef3c7',
      tok_curly_braces: '#c084fc',
      tok_pipes: '#67e8f9',
      tok_at_sign: '#f87171',
      muted_text: '#b3a58d',
      surface: '#231e18',
      success_bg: '#253224',
      danger_bg: '#472119',
      accent_bg: '#433311',
      accent_title: '#fef3c7',
      success_text: '#bbf7d0',
      error_text: '#fdba74',
      warning_text: '#fde68a',
    },
  }),
];

class BrowserStream {
  private readers: StreamReader[] = [];
  private onComplete?: (data: CompleteStreamData) => void;
  private onError?: (error: string) => void;
  private controller = new AbortController();

  constructor(
    private readonly executor: (helpers: {
      emit: <EventType extends StreamEventType>(event: EventType, data: StreamEventMap[EventType]) => void;
      signal: AbortSignal;
    }) => Promise<void>
  ) {}

  subscribe(callback: StreamReader): this {
    this.readers.push(callback);
    return this;
  }

  onComplete_(callback: (data: CompleteStreamData) => void): this {
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

  private emit<EventType extends StreamEventType>(event: EventType, data: StreamEventMap[EventType]): void {
    const payload = { event, data } as StreamEvent;
    this.readers.forEach((reader) => reader(payload));

    if (payload.event === 'complete' && this.onComplete) {
      this.onComplete(payload.data);
    }

    if (payload.event === 'error' && this.onError) {
      this.onError(payload.data.error);
    }
  }
}

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

function readStorage<T>(keys: string | readonly string[], fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const keyList = Array.isArray(keys) ? [...keys] : [keys];
  const [currentKey, ...legacyKeys] = keyList;

  try {
    for (const key of keyList) {
      const raw = window.localStorage.getItem(key);
      if (!raw) {
        continue;
      }

      const parsed = JSON.parse(raw) as T;
      if (key !== currentKey) {
        window.localStorage.setItem(currentKey, JSON.stringify(parsed));
        legacyKeys.forEach((legacyKey) => window.localStorage.removeItem(legacyKey));
      }

      return parsed;
    }
  } catch {
    return fallback;
  }

  return fallback;
}

function writeStorage<T>(key: string, legacyKeys: readonly string[], value: T): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
  legacyKeys.forEach((legacyKey) => window.localStorage.removeItem(legacyKey));
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

function resolveConfiguredProvider(config: Config): LLMProvider | undefined {
  if (config.engine_mode === 'explicit' && config.engine !== 'auto' && config.engine !== 'openai_compatible') {
    return config.engine as LLMProvider;
  }

  return config.model ? detectProviderFromModel(config.model) : undefined;
}

function getFallbackApiKey(apiKeys: ApiKeys): string | undefined {
  return Object.values(apiKeys).find(
    (value): value is string => typeof value === 'string' && value.trim().length > 0
  );
}

function resolveProviderApiKey(provider: string, apiKeys: ApiKeys): string | undefined {
  const providerKey = apiKeys[provider];
  if (typeof providerKey === 'string' && providerKey.trim().length > 0) {
    return providerKey;
  }

  return getFallbackApiKey(apiKeys);
}

function getCustomThemes(): ThemePreset[] {
  return readStorage<ThemePreset[]>([CUSTOM_THEMES_STORAGE_KEY, ...LEGACY_CUSTOM_THEMES_STORAGE_KEYS], []);
}

function saveCustomThemes(themes: ThemePreset[]): void {
  writeStorage(CUSTOM_THEMES_STORAGE_KEY, LEGACY_CUSTOM_THEMES_STORAGE_KEYS, themes);
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
  const provider = resolveConfiguredProvider(config);
  const engine = createEngine({
    model: config.model,
    apiKey: provider ? apiKeys[provider] : getFallbackApiKey(apiKeys),
    apiKeys,
    provider,
    baseUrl: config.base_url,
    temperature: config.temperature,
    maxTokens: config.max_tokens,
  });
  return engine.generateStream(messages);
}

export class EidolonBrowserAPI {
  private async fetchOpenAICompatibleModels(
    provider: string,
    apiKey: string,
    baseUrl: string
  ): Promise<ModelsResponse> {
    const response = await fetch(`${baseUrl}/models`, {
      method: 'GET',
      headers: buildProviderHeaders(provider as LLMProvider, apiKey),
    });

    if (!response.ok) {
      let error = `HTTP ${response.status}`;
      try {
        const payload = await response.json() as { error?: { message?: string } | string };
        if (typeof payload.error === 'string') {
          error = payload.error;
        } else if (payload.error?.message) {
          error = payload.error.message;
        }
      } catch {
        // Keep the HTTP status fallback.
      }

      throw new APIError(response.status, error);
    }

    const payload = await response.json() as OpenAICompatibleModelsPayload;
    const models = (payload.data || [])
      .filter((model): model is NonNullable<OpenAICompatibleModelsPayload['data']>[number] & { id: string } => Boolean(model?.id))
      .map((model) => ({
        id: model.id,
        name: model.name || model.id,
        provider,
        context_length: model.context_length,
        supports_vision: model.architecture?.input_modalities?.includes('image') || false,
        supports_tools: model.supported_parameters?.includes('tools') || false,
      }));

    return {
      provider,
      models,
      cached: false,
    };
  }

  private async loadProviderModels(provider: string, refresh: boolean = false): Promise<ModelsResponse> {
    const apiKeys = configManager.getApiKeys();
    const config = configManager.getConfig();
    const typedProvider = provider as LLMProvider;
    const baseUrl = config.base_url || getDefaultBaseUrl(typedProvider);
    const apiKey = resolveProviderApiKey(provider, apiKeys);
    const cacheKey = `${provider}|${baseUrl}|${apiKey ? 'auth' : 'anon'}`;
    const cachedEntry = modelsCache.get(cacheKey);
    if (!refresh && cachedEntry && Date.now() - cachedEntry.cachedAt < MODEL_CACHE_TTL_MS) {
      return {
        ...cachedEntry.response,
        cached: true,
      };
    }

    const fallbackModels = (MODEL_SUGGESTIONS[typedProvider] || []).map((id) => ({
      id,
      name: id,
      provider,
    }));
    const supportsRemoteListing = ['openrouter', 'openai', 'deepseek', 'zai', 'moonshot'].includes(provider);

    if (!apiKey || !supportsRemoteListing) {
      const response = {
        provider,
        models: fallbackModels,
        cached: true,
        error: apiKey || supportsRemoteListing ? undefined : 'Provider model listing is not available in browser mode.',
      };
      modelsCache.set(cacheKey, {
        response,
        cachedAt: Date.now(),
      });
      return response;
    }

    try {
      const response = await this.fetchOpenAICompatibleModels(provider, apiKey, baseUrl);
      modelsCache.set(cacheKey, {
        response,
        cachedAt: Date.now(),
      });
      return response;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load models';
      const response = {
        provider,
        models: fallbackModels,
        cached: true,
        error: message,
      };
      modelsCache.set(cacheKey, {
        response,
        cachedAt: Date.now(),
      });
      return response;
    }
  }

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
      engineMode: 'explicit',
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
    return this.loadProviderModels(provider, false);
  }

  async refreshModels(provider: string): Promise<{ status: string; model_count: number; error?: string }> {
    const response = await this.loadProviderModels(provider, true);
    return { status: 'ok', model_count: response.models.length, error: response.error };
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
    const record = getStoredTemplateRecord(name) ?? getTemplateRecord(name);
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
          content: 'You are the in-app assistant for Eidolon Simulacra, a browser-only blueprint compiler. Be concise and practical. Use provided draft or screen context when relevant.',
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

export const api = new EidolonBrowserAPI();
