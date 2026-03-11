/**
 * API Client for Eidolon Simulacra
 * Isomorphic - works in browser and Node.js
 */

import type {
  Config,
  Draft,
  DraftListResponse,
  DraftFilters,
  Template,
  CreateTemplateRequest,
  DuplicateTemplateRequest,
  TemplateValidationResult,
  TemplateBlueprintContentsResponse,
  UpdateTemplateRequest,
  SeedGenerationRequest,
  SeedGenerationResponse,
  LineageResponse,
  ValidatePathRequest,
  ValidationResponse,
  GenerateRequest,
  GenerateAssetRequest,
  GenerateAssetResponse,
  FinalizeGenerationRequest,
  GenerationProgress,
  GenerationComplete,
  SimilarityRequest,
  SimilarityResult,
  OffspringRequest,
  ExportRequest,
  ConnectionTestRequest,
  ConnectionTestResult,
  ModelsResponse,
  ChatRequest,
  RefineRequest,
  Blueprint,
  BlueprintList,
  ExportPresetSummary,
  ThemePreset,
  ThemePresetCreate,
  ThemePresetUpdate,
  ThemeDuplicateRequest,
  ThemeRenameRequest,
  ThemeImportRequest,
} from '../types';

export interface DownloadResponse {
  blob: Blob;
  filename: string | null;
  contentType: string | null;
}

interface BrowserStorageLike {
  getItem(key: string): string | null;
}

type HeaderInput = ConstructorParameters<typeof Headers>[0];

const API_KEYS_STORAGE_KEY = 'eidolon.web.apiKeys';
const LEGACY_API_KEYS_STORAGE_KEYS = ['bpui.web.apiKeys'];
const API_KEYS_HEADER = 'X-BPUI-API-KEYS';

function getBrowserStorage(): BrowserStorageLike | null {
  const maybeStorage = (globalThis as { localStorage?: BrowserStorageLike }).localStorage;
  return maybeStorage ?? null;
}

function encodeBase64(value: string): string {
  const withBtoa = globalThis as { btoa?: (data: string) => string };
  if (typeof withBtoa.btoa === 'function') {
    return withBtoa.btoa(value);
  }

  return Buffer.from(value, 'utf-8').toString('base64');
}

function getBrowserApiKeysHeader(): Record<string, string> {
  const storage = getBrowserStorage();
  if (!storage) {
    return {};
  }

  try {
    for (const key of [API_KEYS_STORAGE_KEY, ...LEGACY_API_KEYS_STORAGE_KEYS]) {
      const raw = storage.getItem(key);
      if (!raw) {
        continue;
      }

      const parsed = JSON.parse(raw) as Record<string, string>;
      const keys = Object.fromEntries(
        Object.entries(parsed).filter(([, value]) => typeof value === 'string' && value.trim().length > 0)
      );

      if (Object.keys(keys).length === 0) {
        return {};
      }

      return {
        [API_KEYS_HEADER]: encodeBase64(JSON.stringify(keys)),
      };
    }
  } catch {
    return {};
  }

  return {};
}

export class CharacterGeneratorAPI {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  private buildHeaders(headers: HeaderInput = {}, contentType?: string): Headers {
    const merged = new Headers(headers);

    Object.entries(getBrowserApiKeysHeader()).forEach(([key, value]) => {
      merged.set(key, value);
    });

    if (contentType && !merged.has('Content-Type')) {
      merged.set('Content-Type', contentType);
    }

    return merged;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: this.buildHeaders(options.headers, 'application/json'),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string };
      throw new APIError(response.status, errorData.detail || 'Request failed');
    }

    return response.json() as Promise<T>;
  }

  private parseFilename(contentDisposition: string | null): string | null {
    if (!contentDisposition) {
      return null;
    }

    const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match?.[1]) {
      try {
        return decodeURIComponent(utf8Match[1]);
      } catch {
        return utf8Match[1];
      }
    }

    const quotedMatch = contentDisposition.match(/filename="([^"]+)"/i);
    if (quotedMatch?.[1]) {
      return quotedMatch[1];
    }

    const plainMatch = contentDisposition.match(/filename=([^;]+)/i);
    return plainMatch?.[1]?.trim() ?? null;
  }

  private async requestDownload(
    path: string,
    options: RequestInit = {},
    fallbackError: string
  ): Promise<DownloadResponse> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: this.buildHeaders(options.headers),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string };
      throw new APIError(response.status, errorData.detail || fallbackError);
    }

    return {
      blob: await response.blob(),
      filename: this.parseFilename(response.headers.get('Content-Disposition')),
      contentType: response.headers.get('Content-Type'),
    };
  }

  // ===========================================================================
  // Configuration
  // ===========================================================================

  async getConfig(): Promise<Config> {
    return this.request<Config>('/config');
  }

  async updateConfig(config: Partial<Config>): Promise<Config> {
    return this.request<Config>('/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async testConnection(request: ConnectionTestRequest): Promise<ConnectionTestResult> {
    return this.request<ConnectionTestResult>('/config/test', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getThemes(): Promise<ThemePreset[]> {
    return this.request<ThemePreset[]>('/config/themes');
  }

  async createTheme(theme: ThemePresetCreate): Promise<ThemePreset> {
    return this.request<ThemePreset>('/config/themes', {
      method: 'POST',
      body: JSON.stringify(theme),
    });
  }

  async exportTheme(name: string): Promise<DownloadResponse> {
    return this.requestDownload(
      `/config/themes/${encodeURIComponent(name)}/export`,
      {},
      'Theme export failed'
    );
  }

  async importTheme(file: File, options: ThemeImportRequest = {}): Promise<ThemePreset> {
    const formData = new FormData();
    formData.append('file', file);
    if (options.conflict_strategy) {
      formData.append('conflict_strategy', options.conflict_strategy);
    }
    if (options.target_name) {
      formData.append('target_name', options.target_name);
    }

    const response = await fetch(`${this.baseUrl}/config/themes/import`, {
      method: 'POST',
      body: formData,
      headers: this.buildHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string };
      throw new APIError(response.status, errorData.detail || 'Theme import failed');
    }

    return response.json() as Promise<ThemePreset>;
  }

  async updateTheme(name: string, theme: ThemePresetUpdate): Promise<ThemePreset> {
    return this.request<ThemePreset>(`/config/themes/${encodeURIComponent(name)}`, {
      method: 'PUT',
      body: JSON.stringify(theme),
    });
  }

  async duplicateTheme(name: string, request: ThemeDuplicateRequest): Promise<ThemePreset> {
    return this.request<ThemePreset>(`/config/themes/${encodeURIComponent(name)}/duplicate`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async renameTheme(name: string, request: ThemeRenameRequest): Promise<ThemePreset> {
    return this.request<ThemePreset>(`/config/themes/${encodeURIComponent(name)}/rename`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async deleteTheme(name: string): Promise<{ status: string; name: string }> {
    return this.request<{ status: string; name: string }>(`/config/themes/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });
  }

  // ===========================================================================
  // Models
  // ===========================================================================

  async getModels(provider: string, refresh: boolean = false): Promise<ModelsResponse> {
    const query = refresh ? '?refresh=true' : '';
    return this.request<ModelsResponse>(`/models/${provider}${query}`);
  }

  async refreshModels(provider: string): Promise<{ status: string; model_count: number; error?: string }> {
    return this.request<{ status: string; model_count: number; error?: string }>(`/models/${provider}/refresh`, {
      method: 'POST',
    });
  }

  // ===========================================================================
  // Templates
  // ===========================================================================

  async getTemplates(): Promise<Template[]> {
    return this.request<Template[]>('/templates');
  }

  async listTemplates(): Promise<Template[]> {
    return this.getTemplates();
  }

  async getTemplate(name: string): Promise<Template> {
    return this.request<Template>(`/templates/${encodeURIComponent(name)}`);
  }

  async getTemplateBlueprintContents(name: string): Promise<TemplateBlueprintContentsResponse> {
    return this.request<TemplateBlueprintContentsResponse>(
      `/templates/${encodeURIComponent(name)}/blueprint-contents`
    );
  }

  async createTemplate(template: CreateTemplateRequest): Promise<Template> {
    return this.request<Template>('/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    });
  }

  async updateTemplate(name: string, template: UpdateTemplateRequest): Promise<Template> {
    return this.request<Template>(`/templates/${encodeURIComponent(name)}`, {
      method: 'PUT',
      body: JSON.stringify(template),
    });
  }

  async deleteTemplate(name: string): Promise<void> {
    return this.request<void>(`/templates/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });
  }

  async validateTemplate(name: string): Promise<TemplateValidationResult> {
    return this.request<TemplateValidationResult>(`/templates/${encodeURIComponent(name)}/validate`);
  }

  async duplicateTemplate(name: string, request: DuplicateTemplateRequest): Promise<Template> {
    return this.request<Template>(`/templates/${encodeURIComponent(name)}/duplicate`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async exportTemplate(name: string): Promise<DownloadResponse> {
    return this.requestDownload(
      `/templates/${encodeURIComponent(name)}/export`,
      {},
      'Template export failed'
    );
  }

  async importTemplate(file: File): Promise<Template> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/templates/import`, {
      method: 'POST',
      body: formData,
      headers: this.buildHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string };
      throw new APIError(response.status, errorData.detail || 'Template import failed');
    }

    return response.json() as Promise<Template>;
  }

  async generateSeeds(request: SeedGenerationRequest): Promise<SeedGenerationResponse> {
    return this.request<SeedGenerationResponse>('/seedgen', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getLineage(): Promise<LineageResponse> {
    return this.request<LineageResponse>('/lineage');
  }

  async validatePath(request: ValidatePathRequest): Promise<ValidationResponse> {
    return this.request<ValidationResponse>('/validate/path', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async validateDraft(draftId: string): Promise<ValidationResponse> {
    return this.request<ValidationResponse>(`/validate/draft/${encodeURIComponent(draftId)}`);
  }

  // ===========================================================================
  // Generation (SSE Streaming)
  // ===========================================================================

  generate(request: GenerateRequest): GenerationStream {
    return new GenerationStream(
      `${this.baseUrl}/generate/single`,
      request
    );
  }

  async generateAsset(request: GenerateAssetRequest, signal?: AbortSignal): Promise<GenerateAssetResponse> {
    return this.request<GenerateAssetResponse>('/generate/asset', {
      method: 'POST',
      body: JSON.stringify(request),
      signal,
    });
  }

  async finalizeGeneration(request: FinalizeGenerationRequest, signal?: AbortSignal): Promise<GenerationComplete> {
    return this.request<GenerationComplete>('/generate/finalize', {
      method: 'POST',
      body: JSON.stringify(request),
      signal,
    });
  }

  generateBatch(seeds: string[], options: Omit<GenerateRequest, 'seed'> & { parallel?: boolean; max_concurrent?: number }): GenerationStream {
    return new GenerationStream(
      `${this.baseUrl}/generate/batch`,
      { seeds, ...options }
    );
  }

  // ===========================================================================
  // Drafts
  // ===========================================================================

  async getDrafts(filters?: DraftFilters): Promise<DraftListResponse> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, String(v)));
          } else {
            params.set(key, String(value));
          }
        }
      });
    }
    const query = params.toString();
    return this.request<DraftListResponse>(`/drafts${query ? `?${query}` : ''}`);
  }

  async listDrafts(filters?: DraftFilters): Promise<DraftListResponse> {
    return this.getDrafts(filters);
  }

  async getDraft(draftId: string): Promise<Draft> {
    return this.request<Draft>(`/drafts/${encodeURIComponent(draftId)}`);
  }

  async saveDraft(draftId: string, updates: Partial<Draft>): Promise<Draft> {
    return this.request<Draft>(`/drafts/${encodeURIComponent(draftId)}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteDraft(draftId: string): Promise<void> {
    return this.request<void>(`/drafts/${encodeURIComponent(draftId)}`, {
      method: 'DELETE',
    });
  }

  async updateAsset(draftId: string, assetName: string, content: string): Promise<void> {
    return this.request<void>(
      `/drafts/${encodeURIComponent(draftId)}/assets/${encodeURIComponent(assetName)}`,
      {
        method: 'PUT',
        body: JSON.stringify({ content }),
      }
    );
  }

  async updateMetadata(draftId: string, metadata: Partial<Draft['metadata']>): Promise<void> {
    return this.request<void>(
      `/drafts/${encodeURIComponent(draftId)}/metadata`,
      {
        method: 'PUT',
        body: JSON.stringify(metadata),
      }
    );
  }

  // ===========================================================================
  // Similarity
  // ===========================================================================

  async analyzeSimilarity(request: SimilarityRequest): Promise<SimilarityResult> {
    return this.request<SimilarityResult>('/similarity', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async compareCharacters(request: SimilarityRequest & { mode?: string; use_llm?: boolean }): Promise<SimilarityResult> {
    return this.request<SimilarityResult>('/similarity/compare', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ===========================================================================
  // Offspring
  // ===========================================================================

  generateOffspring(request: OffspringRequest): GenerationStream {
    return new GenerationStream(
      `${this.baseUrl}/offspring`,
      request
    );
  }

  // ===========================================================================
  // Export
  // ===========================================================================

  async exportDraft(request: ExportRequest): Promise<DownloadResponse> {
    return this.requestDownload(
      '/export',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      },
      'Export failed'
    );
  }

  async getExportPresets(): Promise<ExportPresetSummary[]> {
    const response = await this.request<{ presets: ExportPresetSummary[] } | ExportPresetSummary[]>('/export/presets');
    return Array.isArray(response) ? response : response.presets;
  }

  // ===========================================================================
  // Chat/Refinement
  // ===========================================================================

  chat(request: ChatRequest): GenerationStream {
    return new GenerationStream(
      `${this.baseUrl}/chat`,
      request
    );
  }

  refine(request: RefineRequest): GenerationStream {
    return new GenerationStream(
      `${this.baseUrl}/chat/refine`,
      request
    );
  }

  // ===========================================================================
  // Blueprints
  // ===========================================================================

  async getBlueprints(): Promise<BlueprintList> {
    return this.request<BlueprintList>('/blueprints');
  }

  async getBlueprint(path: string): Promise<Blueprint> {
    return this.request<Blueprint>(`/blueprints/${encodeURIComponent(path)}`);
  }

  async updateBlueprint(path: string, content: string): Promise<Blueprint> {
    return this.request<Blueprint>(`/blueprints/${encodeURIComponent(path)}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }
}

// ============================================================================
// SSE Streaming Helper
// ============================================================================

export type GenerationEventType = 'status' | 'chunk' | 'asset' | 'asset_complete' | 'progress' | 'complete' | 'error' | 'batch_start' | 'batch_complete' | 'batch_error';

export type GenerationEventData =
  | GenerationProgress
  | GenerationComplete
  | { content: string }
  | { error: string }
  | { name: string; [key: string]: unknown }
  | Record<string, unknown>;

export interface GenerationEvent {
  event: GenerationEventType;
  data: GenerationEventData;
}

export class GenerationStream {
  private controller: AbortController | null = null;
  private readers: Set<(event: GenerationEvent) => void> = new Set();
  private onComplete: ((data: GenerationComplete) => void) | null = null;
  private onError: ((error: string) => void) | null = null;
  private currentEventType: GenerationEventType = 'chunk';
  private currentDataLines: string[] = [];

  constructor(
    private url: string,
    private body: object
  ) {}

  subscribe(callback: (event: GenerationEvent) => void): () => void {
    this.readers.add(callback);
    return () => this.readers.delete(callback);
  }

  onComplete_(callback: (data: GenerationComplete) => void): this {
    this.onComplete = callback;
    return this;
  }

  onError_(callback: (error: string) => void): this {
    this.onError = callback;
    return this;
  }

  async start(): Promise<void> {
    this.controller = new AbortController();

    try {
      const response = await fetch(this.url, {
        method: 'POST',
        headers: new Headers({
          'Content-Type': 'application/json',
          ...getBrowserApiKeysHeader(),
        }),
        body: JSON.stringify(this.body),
        signal: this.controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const event = this.parseSSELine(line);
          if (event) {
            this.readers.forEach(cb => cb(event));

            if (event.event === 'complete' && this.onComplete) {
              this.onComplete(event.data as GenerationComplete);
            }
            if (event.event === 'error' && this.onError) {
              this.onError((event.data as { error: string }).error);
            }
          }
        }
      }

      const trailingEvent = this.parseSSELine('');
      if (trailingEvent) {
        this.readers.forEach(cb => cb(trailingEvent));
        if (trailingEvent.event === 'complete' && this.onComplete) {
          this.onComplete(trailingEvent.data as GenerationComplete);
        }
        if (trailingEvent.event === 'error' && this.onError) {
          this.onError((trailingEvent.data as { error: string }).error);
        }
      }
    } catch (err) {
      if (this.onError) {
        this.onError(err instanceof Error ? err.message : 'Stream error');
      }
    }
  }

  abort(): void {
    this.controller?.abort();
  }

  private parseSSELine(line: string): GenerationEvent | null {
    if (line.startsWith('event:')) {
      this.currentEventType = line.slice(6).trim() as GenerationEventType;
      return null;
    }
    if (line.startsWith('data:')) {
      this.currentDataLines.push(line.slice(5).trim());
      return null;
    }
    if (line.trim() === '' && this.currentDataLines.length > 0) {
      try {
        const event = {
          event: this.currentEventType,
          data: JSON.parse(this.currentDataLines.join('\n')) as GenerationEventData,
        } satisfies GenerationEvent;
        this.currentEventType = 'chunk';
        this.currentDataLines = [];
        return event;
      } catch {
        this.currentEventType = 'chunk';
        this.currentDataLines = [];
        return null;
      }
    }
    return null;
  }
}

// ============================================================================
// Error Class
// ============================================================================

export class APIError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Default instance
export const api = new CharacterGeneratorAPI();
