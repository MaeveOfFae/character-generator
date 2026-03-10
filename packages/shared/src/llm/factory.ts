/**
 * LLM Engine Factory for creating engines based on model and configuration.
 * Handles provider detection and API key resolution.
 */

import type { LLMEngine, LLMConfig, LLMProvider, ChatMessage } from './types';
import { OpenAICompatEngine, OpenAICompatConfig } from './openai-compat';
import { detectProviderFromModel, ProviderEndpoints } from './types';

export interface CreateEngineOptions extends LLMConfig {
  apiKeys?: Record<string, string>;
  defaultApiKey?: string;
}

/**
 * Normalize model names for OpenAI-compatible APIs.
 * OpenRouter expects provider/model IDs and does not accept legacy "openrouter/" prefix.
 */
function normalizeOpenAICompatModel(model: string, baseUrl: string): string {
  if (baseUrl.includes('openrouter.ai') && model.startsWith('openrouter/')) {
    return model.slice('openrouter/'.length);
  }
  return model;
}

/**
 * Get base URL for a provider (if not explicitly provided)
 */
function getProviderBaseUrl(provider: LLMProvider): string {
  return ProviderEndpoints[provider];
}

/**
 * Get API key for a provider from the keys object.
 * Falls back to defaultApiKey if no provider-specific key is found.
 */
function getApiKey(
  provider: LLMProvider,
  options: CreateEngineOptions
): string | undefined {
  if (options.apiKeys?.[provider]) {
    return options.apiKeys[provider];
  }
  // Fallback to legacy default key
  return options.apiKey || options.defaultApiKey;
}

/**
 * Create appropriate LLM engine based on config and model.
 * This is the main entry point for creating engines.
 */
export function createEngine(options: CreateEngineOptions): LLMEngine {
  const { model, baseUrl: explicitBaseUrl, apiKeys, defaultApiKey, ...rest } = options;

  // Detect provider from model if not explicitly set
  const provider = options.provider || detectProviderFromModel(model);

  // Determine base URL
  const baseUrl = explicitBaseUrl || getProviderBaseUrl(provider);

  // Get API key
  const apiKey = getApiKey(provider, { ...rest, apiKeys, defaultApiKey });

  // Normalize model name
  const normalizedModel = normalizeOpenAICompatModel(model, baseUrl);

  // Create engine configuration
  const config: OpenAICompatConfig = {
    provider,
    model: normalizedModel,
    apiKey: apiKey || '',
    baseUrl,
    temperature: rest.temperature,
    maxTokens: rest.maxTokens,
    timeout: rest.timeout,
  };

  // For now, all providers use the OpenAI-compatible API
  // This covers: OpenAI, OpenRouter, Anthropic, DeepSeek, Zai, Moonshot
  return new OpenAICompatEngine(config);
}

/**
 * Get the engine type that would be used for a given model.
 * Useful for UI display without actually creating an engine.
 */
export function getEngineType(model: string, provider?: LLMProvider): string {
  const detected = provider || detectProviderFromModel(model);
  return `OpenAICompatEngine (${detected})`;
}

/**
 * List available models from a provider.
 */
export async function listModels(
  provider: LLMProvider,
  apiKey?: string,
  baseUrl?: string
): Promise<string[]> {
  const resolvedBaseUrl = baseUrl || getProviderBaseUrl(provider);
  return OpenAICompatEngine.listModels(resolvedBaseUrl, apiKey);
}

/**
 * Test connection to a provider.
 */
export async function testConnection(
  provider: LLMProvider,
  model: string,
  apiKey?: string,
  baseUrl?: string,
  options?: Partial<Omit<CreateEngineOptions, 'provider' | 'model'>>
): Promise<{ success: boolean; latencyMs?: number; error?: string }> {
  try {
    const engine = createEngine({
      provider,
      model,
      apiKey,
      baseUrl,
      ...options,
    });

    const result = await engine.testConnection();
    return {
      success: result.success,
      latencyMs: result.latencyMs,
      error: result.error,
    };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : 'Unknown error',
    };
  }
}
