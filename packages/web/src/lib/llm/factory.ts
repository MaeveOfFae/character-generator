/**
 * LLM Engine Factory
 * Creates appropriate LLM engines based on model name and configuration
 */

import type { ApiKeys, LLMConfig, LLMProvider } from '@char-gen/shared';
import { detectProviderFromModel } from '@char-gen/shared';
import { OpenAICompatEngine } from './openai-compat.js';
import { GoogleEngine } from './google.js';
import { AnthropicEngine } from './anthropic.js';

export interface CreateEngineOptions {
  model: string;
  apiKey?: string;
  apiKeys?: ApiKeys;
  provider?: LLMProvider;
  baseUrl?: string;
  temperature?: number;
  maxTokens?: number;
  engineMode?: 'auto' | 'explicit';
}

function resolveApiKey(provider: LLMProvider, apiKey?: string, apiKeys?: ApiKeys): string | undefined {
  if (typeof apiKey === 'string' && apiKey.trim().length > 0) {
    return apiKey;
  }

  const providerKey = apiKeys?.[provider];
  if (typeof providerKey === 'string' && providerKey.trim().length > 0) {
    return providerKey;
  }

  return Object.values(apiKeys ?? {}).find(
    (value): value is string => typeof value === 'string' && value.trim().length > 0
  );
}

/**
 * Create an LLM engine based on the model name and configuration
 */
export function createEngine(options: CreateEngineOptions) {
  const {
    model,
    apiKey,
    apiKeys,
    provider: explicitProvider,
    baseUrl,
    temperature,
    maxTokens,
  } = options;

  const provider = explicitProvider ?? detectProviderFromModel(model);

  const config: LLMConfig = {
    provider,
    model,
    apiKey: resolveApiKey(provider, apiKey, apiKeys),
    baseUrl,
    temperature,
    maxTokens,
  };

  // Create appropriate engine based on provider
  switch (provider) {
    case 'google':
      return new GoogleEngine(config);

    case 'anthropic':
      return new AnthropicEngine(config);

    case 'openai':
    case 'openrouter':
    case 'deepseek':
    case 'zai':
    case 'moonshot':
    default:
      return new OpenAICompatEngine(config);
  }
}

/**
 * Get the provider that would be used for a given model
 * Useful for UI display without creating an engine
 */
export function getProviderForModel(
  model: string,
  engineMode: 'auto' | 'explicit' = 'auto',
  explicitProvider?: LLMProvider
): LLMProvider {
  if (engineMode === 'explicit' && explicitProvider) {
    return explicitProvider;
  }
  if (explicitProvider) {
    return explicitProvider;
  }
  return detectProviderFromModel(model);
}

/**
 * Check if a provider requires a specific API key format
 */
export function getProviderAuthType(provider: LLMProvider): 'bearer' | 'raw' {
  switch (provider) {
    case 'google':
    case 'anthropic':
      return 'raw';
    default:
      return 'bearer';
  }
}

/**
 * Get the default base URL for a provider
 */
export function getDefaultBaseUrl(provider: LLMProvider): string {
  switch (provider) {
    case 'openai':
      return 'https://api.openai.com/v1';
    case 'google':
      return 'https://generativelanguage.googleapis.com/v1beta';
    case 'openrouter':
      return 'https://openrouter.ai/api/v1';
    case 'anthropic':
      return 'https://api.anthropic.com';
    case 'deepseek':
      return 'https://api.deepseek.com';
    case 'zai':
      return 'https://open.bigmodel.cn/api/paas/v4';
    case 'moonshot':
      return 'https://api.moonshot.cn/v1';
    default:
      return 'https://api.openai.com/v1';
  }
}

/**
 * Get popular model suggestions for each provider
 */
export const MODEL_SUGGESTIONS: Record<LLMProvider, string[]> = {
  openai: [
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-turbo',
    'gpt-3.5-turbo',
    'o1-preview',
  ],
  google: [
    'gemini-2.0-flash-exp',
    'gemini-2.0-flash-thinking-exp',
    'gemini-1.5-pro',
    'gemini-1.5-flash',
  ],
  openrouter: [
    'anthropic/claude-3.5-sonnet',
    'anthropic/claude-3.5-haiku',
    'google/gemini-pro-1.5',
    'openai/gpt-4o-mini',
  ],
  anthropic: [
    'claude-3.5-sonnet',
    'claude-3.5-haiku',
    'claude-3-opus',
  ],
  deepseek: [
    'deepseek-chat',
    'deepseek-coder',
  ],
  zai: [
    'glm-4',
    'glm-4-flash',
  ],
  moonshot: [
    'moonshot-v1-8k',
    'moonshot-v1-32k',
    'moonshot-v1-128k',
  ],
} as const;
