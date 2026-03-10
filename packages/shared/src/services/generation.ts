/**
 * Client-side generation service using direct LLM provider calls.
 * Replaces backend API with direct browser-based generation.
 */

import type {
  ChatMessage,
  GenerateOptions,
  GenerateResult,
  StreamChunk,
  StreamGenerateOptions,
} from '../llm/types';
import type { CreateEngineOptions } from '../llm/factory';
import type { Template } from '../templates';
import type { ParseResult } from '../parse/parse-blocks';

import { createEngine } from '../llm/factory';
import { buildOrchestrator, getOfficialTemplate, getDefaultAssetOrder } from '../blueprint/orchestrator';
import { parseBlueprintOutput, extractCharacterName, inferCharacterNameFromAssets } from '../parse/parse-blocks';

export type ContentMode = 'SFW' | 'NSFW' | 'Platform-Safe' | 'Auto';

export interface GenerateRequest {
  seed: string;
  template?: Template;
  mode: ContentMode;
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface GenerateStreamChunk {
  type: 'status' | 'chunk' | 'asset' | 'asset_complete' | 'complete' | 'error';
  asset?: string;
  content?: string;
  progress?: number;
  error?: string;
}

export interface GenerationOptions extends GenerateRequest {
  onChunk?: (chunk: GenerateStreamChunk) => void;
  signal?: AbortSignal;
}

/**
 * Generate a character from a seed.
 */
export async function generateCharacter(request: GenerationOptions): Promise<GenerateResult> {
  const {
    seed,
    template = getOfficialTemplate(),
    mode = 'NSFW',
    model,
    temperature = 0.7,
    maxTokens = 4096,
    onChunk,
    signal,
  } = request;

  // Build the system prompt (orchestrator)
  const systemPrompt = buildOrchestrator({ template, mode });

  // Create the user prompt
  const userPrompt = `Seed: ${seed}`;

  // Create LLM engine
  const engine = createEngine({
    model: model || 'openrouter/openai/gpt-4o-mini',
    temperature,
    maxTokens: maxTokens,
    // API keys should come from user's local storage or input
    apiKey: '', // Will be set separately
  });

  // Generate response
  const messages: ChatMessage[] = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ];

  const result = await engine.generate(messages);

  return result;
}

/**
 * Generate a character with streaming support.
 */
export async function* generateCharacterStream(
  request: GenerationOptions
): AsyncGenerator<GenerateStreamChunk> {
  const {
    seed,
    template = getOfficialTemplate(),
    mode = 'NSFW',
    model,
    temperature = 0.7,
    maxTokens = 4096,
    onChunk,
    signal,
  } = request;

  // Build the system prompt (orchestrator)
  const systemPrompt = buildOrchestrator({ template, mode });

  // Create the user prompt
  const userPrompt = `Seed: ${seed}`;

  // Create LLM engine
  const engine = createEngine({
    model: model || 'openrouter/openai/gpt-4o-mini',
    temperature,
    maxTokens: maxTokens,
    apiKey: '', // Will be set separately
  });

  // Generate response with streaming
  const messages: ChatMessage[] = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ];

  // Emit status
  yield { type: 'status', progress: 0 };

  let fullContent = '';
  const assetOrder = getDefaultAssetOrder();

  try {
    for await (const chunk of engine.generateStream(messages, { signal })) {
      if (chunk.done) {
        break;
      }
      fullContent += chunk.content;

      // Try to parse and emit assets as they become available
      const parseResult = tryParseAssets(fullContent, assetOrder);
      if (parseResult) {
        for (const [assetName, content] of Object.entries(parseResult.assets)) {
          yield { type: 'asset', asset: assetName, content };
        }
        yield { type: 'asset_complete', progress: Math.min(100, (parseResult.assets.size / assetOrder.length) * 100) };
      }

      // Emit raw chunk
      if (onChunk) {
        onChunk({ type: 'chunk', content: chunk.content });
      }
    }
  } catch (e) {
    yield { type: 'error', error: e instanceof Error ? e.message : 'Generation failed' };
    return;
  }

  // Final parse
  let parseResult: ParseResult | null = null;
  try {
    parseResult = parseBlueprintOutput(fullContent, template);
  } catch {
    // Parse failed
    yield { type: 'error', error: 'Failed to parse generated assets' };
    return;
  }

  if (!parseResult) {
    yield { type: 'error', error: 'Failed to parse generated assets' };
    return;
  }

  // Extract character name
  const characterName = parseResult.assets.character_sheet
    ? extractCharacterName(parseResult.assets.character_sheet)
    : inferCharacterNameFromAssets(parseResult.assets);

  // Emit completion
  yield {
    type: 'complete',
    asset: 'character_sheet',
    content: parseResult.assets.character_sheet || '',
  };

  if (characterName) {
    yield { type: 'status', progress: 100 };
  }
}

/**
 * Try to parse assets from partial content.
 * Returns null if not enough codeblocks are available.
 */
function tryParseAssets(content: string, expectedAssets: readonly string[]): ParseResult | null {
  const codeblockPattern = /```(?:[a-z]*\n)?(.*?)```/gs;
  const matches = content.match(codeblockPattern);

  if (!matches || matches.length < expectedAssets.length) {
    return null;
  }

  // Parse into assets
  const assets: Map<string, string> = new Map();
  for (let i = 0; i < Math.min(matches.length, expectedAssets.length); i++) {
    assets.set(expectedAssets[i], matches[i].trim());
  }

  return { assets: Object.fromEntries(assets) };
}

/**
 * Generate a single asset for a character.
 */
export async function generateAsset(
  assetName: string,
  seed: string,
  template?: Template,
  mode: ContentMode = 'NSFW',
  priorAssets: Record<string, string> = {},
  options: Partial<GenerationOptions> = {}
): Promise<string> {
  const systemPrompt = buildOrchestrator({ template, mode });

  // Build prior context
  let priorContext = '';
  if (Object.keys(priorAssets).length > 0) {
    priorContext = '\n\nPrior assets generated:\n';
    for (const [name, content] of Object.entries(priorAssets)) {
      priorContext += `\n\n### ${name}\n\n${content.substring(0, 500)}${content.length > 500 ? '...' : ''}\n`;
    }
  }

  const userPrompt = `Seed: ${seed}${priorContext}\n\nGenerate only the ${assetName} asset.`;

  const engine = createEngine({
    model: options.model || 'openrouter/openai/gpt-4o-mini',
    temperature: options.temperature || 0.7,
    maxTokens: options.maxTokens || 4096,
    apiKey: '',
  });

  const messages: ChatMessage[] = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ];

  const result = await engine.generate(messages);
  return result.content;
}
