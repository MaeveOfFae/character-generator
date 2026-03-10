/**
 * Mock API object for client-side character generator.
 * TODO: Implement client-side services to replace backend API calls.
 */

import type {
  ApiKeys,
  BatchConfig,
  Config,
  DraftMetadata,
  Draft,
  DraftListResponse,
  DraftFilters,
  GenerateRequest,
  GenerateBatchRequest,
  GenerateAssetRequest,
  GenerateAssetResponse,
  FinalizeGenerationRequest,
  GenerationProgress,
  GenerationComplete,
  SeedGenerationRequest,
  SeedGenerationResponse,
  ValidatePathRequest,
  ValidationResponse,
  ThemeOverride,
  ThemePreset,
  ThemePresetCreate,
  ThemePresetUpdate,
  ThemeDuplicateRequest,
  ThemeRenameRequest,
  ThemeImportRequest,
  ExportRequest,
  ExportPresetSummary,
  OffspringRequest,
  LineageNode,
  LineageResponse,
  SimilarityResult,
  SimilarityRequest,
  ConnectionTestRequest,
  ConnectionTestResult,
  Template,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  DuplicateTemplateRequest,
  TemplateValidationResult,
  TemplateBlueprintContentsResponse,
  Blueprint,
  BlueprintList,
  BlueprintCategory,
  ChatMessage,
  ChatRequest,
  RefineRequest,
  ModelInfo,
  ModelsResponse,
} from './types';

/**
 * Mock API for client-side operations.
 * Currently no-op - needs implementation for client-side LLM calls.
 */
export const api = {
  // ============================================================================
  // Configuration
  // ============================================================================

  async getConfig(): Promise<Config> {
    throw new Error('Not implemented: Use client-side config storage');
  },

  async updateConfig(config: Partial<Config>): Promise<Config> {
    throw new Error('Not implemented: Use client-side config storage');
  },

  async testConnection(request: ConnectionTestRequest): Promise<ConnectionTestResult> {
    throw new Error('Not implemented: Use LLMEngine.testConnection()');
  },

  async getModels(provider: string): Promise<ModelsResponse> {
    throw new Error('Not implemented: Use LLMEngine.listModels()');
  },

  // ============================================================================
  // Drafts
  // ============================================================================

  async listDrafts(filters?: DraftFilters): Promise<DraftListResponse> {
    throw new Error('Not implemented: Use IndexedDB draft storage');
  },

  // Alias for listDrafts
  async getDrafts(filters?: DraftFilters): Promise<DraftListResponse> {
    return this.listDrafts(filters);
  },

  async getDraft(reviewId: string): Promise<Draft> {
    throw new Error('Not implemented: Use IndexedDB draft storage');
  },

  async saveDraft(draft: Draft): Promise<void> {
    throw new Error('Not implemented: Use IndexedDB draft storage');
  },

  async deleteDraft(reviewId: string): Promise<void> {
    throw new Error('Not implemented: Use IndexedDB draft storage');
  },

  async updateDraftMetadata(reviewId: string, metadata: Partial<DraftMetadata>): Promise<DraftMetadata> {
    throw new Error('Not implemented: Use IndexedDB draft storage');
  },

  async validateDraft(reviewId: string): Promise<ValidationResponse> {
    throw new Error('Not implemented');
  },


  // ============================================================================
  // Generation
  // ============================================================================

  async generateCharacter(request: GenerateRequest): Promise<GenerationComplete> {
    throw new Error('Not implemented: Use generateCharacter from services');
  },

  async generateBatch(request: GenerateBatchRequest): Promise<GenerationComplete[]> {
    throw new Error('Not implemented: Use generateBatch from services');
  },

  async generateAsset(request: GenerateAssetRequest): Promise<GenerateAssetResponse> {
    throw new Error('Not implemented: Use generateAsset from services');
  },

  async finalizeGeneration(request: FinalizeGenerationRequest): Promise<GenerationComplete> {
    throw new Error('Not implemented: Use finalizeGeneration from services');
  },

  // ============================================================================
  // Seed Generation
  // ============================================================================

  async generateSeeds(request: SeedGenerationRequest): Promise<SeedGenerationResponse> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Validation
  // ============================================================================

  async validatePath(request: ValidatePathRequest): Promise<ValidationResponse> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Themes
  // ============================================================================

  async getThemes(): Promise<ThemePreset[]> {
    throw new Error('Not implemented');
  },

  async getTheme(name: string): Promise<ThemePreset> {
    throw new Error('Not implemented');
  },

  async createTheme(theme: ThemePresetCreate): Promise<ThemePreset> {
    throw new Error('Not implemented');
  },

  async updateTheme(name: string, theme: ThemePresetUpdate): Promise<ThemePreset> {
    throw new Error('Not implemented');
  },

  async deleteTheme(name: string): Promise<void> {
    throw new Error('Not implemented');
  },

  async duplicateTheme(name: string, request: ThemeDuplicateRequest): Promise<ThemePreset> {
    throw new Error('Not implemented');
  },

  async renameTheme(name: string, request: ThemeRenameRequest): Promise<ThemePreset> {
    throw new Error('Not implemented');
  },

  async importTheme(content: string, request?: ThemeImportRequest): Promise<ThemePreset> {
    throw new Error('Not implemented');
  },

  async exportTheme(name: string): Promise<string> {
    throw new Error('Not implemented');
  },

  async getThemeOverride(): Promise<ThemeOverride> {
    throw new Error('Not implemented');
  },

  async updateThemeOverride(override: ThemeOverride): Promise<ThemeOverride> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Export
  // ============================================================================

  async listExportPresets(): Promise<ExportPresetSummary[]> {
    throw new Error('Not implemented');
  },

  // Alias for listExportPresets
  async getExportPresets(): Promise<ExportPresetSummary[]> {
    return this.listExportPresets();
  },

  async getExportPreset(name: string): Promise<string> {
    throw new Error('Not implemented');
  },

  async exportCharacter(request: ExportRequest): Promise<string> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Lineage
  // ============================================================================

  async getLineage(): Promise<LineageResponse> {
    throw new Error('Not implemented');
  },

  async getLineageNode(reviewId: string): Promise<LineageNode> {
    throw new Error('Not implemented');
  },

  async createOffspring(request: OffspringRequest): Promise<GenerationComplete> {
    throw new Error('Not implemented');
  },

  async generateOffspring(request: OffspringRequest): Promise<GenerationComplete> {
    return this.createOffspring(request);
  },

  async analyzeSimilarity(request: SimilarityRequest): Promise<SimilarityResult> {
    throw new Error('Not implemented');
  },

  async analyzeSimilarityForIds(draft1Id: string, draft2Id: string): Promise<SimilarityResult> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Draft Management (additional methods)
  // ============================================================================

  async exportDraft(reviewId: string): Promise<string> {
    throw new Error('Not implemented');
  },

  async updateMetadata(reviewId: string, metadata: Partial<DraftMetadata>): Promise<void> {
    throw new Error('Not implemented');
  },

  async updateAsset(reviewId: string, assetName: string, content: string): Promise<void> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Export Presets (additional methods)
  // ============================================================================

  // ============================================================================
  // Templates (additional methods)
  // ============================================================================

  async getTemplates(): Promise<Template[]> {
    throw new Error('Not implemented');
  },

  async importTemplate(content: string): Promise<Template> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Similarity
  // ============================================================================

  async compareCharacters(request: SimilarityRequest): Promise<SimilarityResult> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Blueprints
  // ============================================================================

  async listBlueprints(): Promise<BlueprintList> {
    throw new Error('Not implemented');
  },

  async getBlueprint(path: string): Promise<Blueprint> {
    throw new Error('Not implemented');
  },

  async getBlueprintContents(path: string): Promise<TemplateBlueprintContentsResponse> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Templates
  // ============================================================================

  async listTemplates(): Promise<Template[]> {
    throw new Error('Not implemented');
  },

  async getTemplate(name: string): Promise<Template> {
    throw new Error('Not implemented');
  },

  async createTemplate(request: CreateTemplateRequest): Promise<Template> {
    throw new Error('Not implemented');
  },

  async updateTemplate(name: string, request: UpdateTemplateRequest): Promise<Template> {
    throw new Error('Not implemented');
  },

  async deleteTemplate(name: string): Promise<void> {
    throw new Error('Not implemented');
  },

  async duplicateTemplate(name: string, request: DuplicateTemplateRequest): Promise<Template> {
    throw new Error('Not implemented');
  },

  async validateTemplate(request: CreateTemplateRequest | string): Promise<TemplateValidationResult> {
    throw new Error('Not implemented');
  },

  async getTemplateBlueprintContents(name: string): Promise<TemplateBlueprintContentsResponse> {
    throw new Error('Not implemented');
  },

  async exportTemplate(name: string): Promise<string> {
    throw new Error('Not implemented');
  },


  // ============================================================================
  // Chat/Refinement
  // ============================================================================

  async chat(request: ChatRequest): Promise<ChatMessage> {
    throw new Error('Not implemented');
  },

  async refine(request: RefineRequest): Promise<GenerateAssetResponse> {
    throw new Error('Not implemented');
  },

  // ============================================================================
  // Stream
  // ============================================================================

  async *generateCharacterStream(request: GenerateRequest): AsyncIterable<GenerationProgress> {
    throw new Error('Not implemented: Use generateCharacterStream from services');
  },

  async *generateBatchStream(request: GenerateBatchRequest): AsyncIterable<GenerationProgress> {
    throw new Error('Not implemented');
  },
};

export default api;
