// ============================================================================
// Core Types
// ============================================================================

export * from './types';

// ============================================================================
// API (Mock - to be replaced with client-side services)
// ============================================================================

export { api } from './api';

// ============================================================================
// LLM Engine (Direct client-side calls)
// ============================================================================

export * from './llm/types';
export * from './llm/factory';
export { OpenAICompatEngine, OpenAICompatConfig } from './llm/openai-compat';

// ============================================================================
// Parsing
// ============================================================================

export {
  ASSET_ORDER,
  DEFAULT_ASSET_FILENAMES,
  AssetName,
  ParseResult,
  ParseError,
  extractCodeblocks,
  parseBlueprintOutput,
  extractSingleAsset,
  extractCharacterName,
  extractCharacterDisplayName,
  sanitizeCharacterName,
  inferCharacterDisplayNameFromAssets,
  inferCharacterNameFromAssets,
  validateAssetContent,
  validateAssetsContent,
} from './parse/parse-blocks';

// ============================================================================
// Export Presets
// ============================================================================

export {
  applyPreset,
  formatExport,
  validatePreset,
} from './export/presets';

// ============================================================================
// Templates
// ============================================================================

export {
  OFFICIAL_TEMPLATE,
  DEFAULT_ASSET_ORDER as TemplateAssetOrder,
  AssetDefinition,
  Template as TemplateType,
  topologicalSort,
  getOrderedAssets,
  validateTemplate,
} from './templates';

// ============================================================================
// Blueprint Orchestrator
// ============================================================================

export {
  buildOrchestrator,
  getDefaultAssetOrder as GetDefaultAssetOrder,
  getOfficialTemplate,
} from './blueprint/orchestrator';
