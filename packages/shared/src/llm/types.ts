/**
 * LLM Engine Types for Client-Side Character Generator
 */

export type LLMProvider =
  | 'openai'
  | 'google'
  | 'openrouter'
  | 'anthropic'
  | 'deepseek'
  | 'zai'
  | 'moonshot';

export type LLMEngineMode = 'auto' | 'explicit';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
  apiKey?: string;
  temperature?: number;
  maxTokens?: number;
  baseUrl?: string;
  timeout?: number;
}

export interface LLMChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface GenerateOptions {
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  signal?: AbortSignal;
}

export interface GenerateResult {
  content: string;
  finishReason?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface StreamChunk {
  content: string;
  done: boolean;
  finishReason?: string;
}

export interface StreamGenerateOptions extends GenerateOptions {
  signal?: AbortSignal;
}

export interface LLMConnectionTestResult {
  success: boolean;
  latencyMs?: number;
  error?: string;
  modelInfo?: {
    name: string;
    contextLength?: number;
  };
}

export interface LLMEngine {
  /**
   * Generate a completion (non-streaming)
   */
  generate(
    messages: LLMChatMessage[],
    options?: GenerateOptions
  ): Promise<GenerateResult>;

  /**
   * Generate a completion with streaming
   */
  generateStream(
    messages: LLMChatMessage[],
    options?: StreamGenerateOptions
  ): AsyncIterable<StreamChunk>;

  /**
   * Test connection to LLM provider
   */
  testConnection(): Promise<LLMConnectionTestResult>;

  /**
   * Get provider type
   */
  getProvider(): LLMProvider;

  /**
   * Get model name
   */
  getModel(): string;
}

export interface LLMEngineConstructor {
  new (config: LLMConfig): LLMEngine;
}

/**
 * Provider-specific API endpoints
 */
export const ProviderEndpoints: Record<LLMProvider, string> = {
  openai: 'https://api.openai.com/v1',
  google: 'https://generativelanguage.googleapis.com/v1beta',
  openrouter: 'https://openrouter.ai/api/v1',
  anthropic: 'https://api.anthropic.com/v1',
  deepseek: 'https://api.deepseek.com',
  zai: 'https://open.bigmodel.cn/api/paas/v4',
  moonshot: 'https://api.moonshot.cn/v1',
} as const;

/**
 * Provider-specific header keys
 */
export const ProviderAuthHeaders: Record<LLMProvider, string> = {
  openai: 'Authorization',
  google: 'x-goog-api-key',
  openrouter: 'Authorization',
  anthropic: 'x-api-key',
  deepseek: 'Authorization',
  zai: 'Authorization',
  moonshot: 'Authorization',
} as const;

/**
 * Helper to format auth header value
 */
export function formatAuthHeader(provider: LLMProvider, apiKey: string): string {
  switch (provider) {
    case 'openai':
    case 'openrouter':
    case 'deepseek':
    case 'zai':
    case 'moonshot':
      return `Bearer ${apiKey}`;
    case 'google':
    case 'anthropic':
      return apiKey;
    default:
      return apiKey;
  }
}

/**
 * Detect provider from model name
 */
export function detectProviderFromModel(model: string): LLMProvider {
  const modelLower = model.toLowerCase();

  // Check for explicit provider prefixes
  if (modelLower.startsWith('openrouter/')) return 'openrouter';
  if (modelLower.startsWith('openai/')) return 'openai';
  if (modelLower.startsWith('google/')) return 'google';
  if (modelLower.startsWith('anthropic/')) return 'anthropic';
  if (modelLower.startsWith('deepseek/')) return 'deepseek';
  if (modelLower.startsWith('zai/')) return 'zai';
  if (modelLower.startsWith('moonshot')) return 'moonshot';

  // Auto-detect based on model name patterns
  if (modelLower.startsWith('gpt-') || modelLower.startsWith('o1')) {
    return 'openai';
  }
  if (modelLower.startsWith('gemini')) {
    return 'google';
  }
  if (modelLower.startsWith('claude')) {
    return 'anthropic';
  }

  // Default to openrouter for unknown models
  return 'openrouter';
}
