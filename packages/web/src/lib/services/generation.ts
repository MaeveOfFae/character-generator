/**
 * Generation Service
 * Client-side character generation using LLM engines
 */

import type {
  ApiKeys,
  ContentMode,
  Config,
  Draft,
  GenerateRequest,
  GenerateAssetRequest,
  OffspringRequest,
  SeedGenerationRequest,
  ChatMessage,
  LLMProvider,
} from '@char-gen/shared';
import {
  detectProviderFromModel,
  parseBlueprintOutput as parseGeneratedBlueprintOutput,
} from '@char-gen/shared';
import { createEngine } from '../llm/factory.js';
import { configManager } from '../config/manager.js';
import { DraftStorage } from '../storage/draft-db.js';
import {
  buildOrchestratorPrompt,
  buildAssetPrompt,
  buildSeedGenPrompt,
  buildSimilarityPrompt,
  buildOffspringPrompt,
  formatMessages,
} from '../prompting/builder.js';
import {
  inferCharacterDisplayNameForTemplate,
  resolveTemplateAssets,
  resolveTemplateBlueprintContent,
  resolveTemplateDefinition,
} from '../templates/browser.js';
import {
  parseSeedGenerationResponse,
  resolveSeedGenerationInput,
} from '../seed-generator.js';

/**
 * Progress callback for generation
 */
export interface GenerationProgress {
  type: 'status' | 'asset' | 'chunk' | 'complete' | 'error';
  stage?: string;
  asset?: string;
  content?: string;
  progress?: number;
  error?: string;
  systemPrompt?: string;
  userPrompt?: string;
}

/**
 * Generation Service
 */
export class GenerationService {
  private static resolveConfiguredProvider(config: Config): LLMProvider | undefined {
    if (config.engine_mode === 'explicit' && config.engine !== 'auto' && config.engine !== 'openai_compatible') {
      return config.engine as LLMProvider;
    }

    return config.model ? detectProviderFromModel(config.model) : undefined;
  }

  private static getFallbackApiKey(apiKeys: ApiKeys): string | undefined {
    return Object.values(apiKeys).find(
      (value): value is string => typeof value === 'string' && value.trim().length > 0
    );
  }

  private static createConfiguredEngine() {
    const apiKeys = configManager.getApiKeys();
    const config = configManager.getConfig();
    const provider = this.resolveConfiguredProvider(config);

    return createEngine({
      model: config.model,
      apiKey: provider ? apiKeys[provider] : this.getFallbackApiKey(apiKeys),
      apiKeys,
      provider,
      baseUrl: config.base_url,
      temperature: config.temperature,
      maxTokens: config.max_tokens,
    });
  }

  /**
   * Generate a full character from a seed
   */
  static async *generate(request: GenerateRequest): AsyncIterable<GenerationProgress> {
    const { seed, template, mode = 'Auto', stream = true } = request;

    yield { type: 'status', stage: 'initializing' };

    const config = configManager.getConfig();
    const engine = this.createConfiguredEngine();

    // Get template assets
    const templateAssets = resolveTemplateAssets(template);
    const templateDefinition = template ? resolveTemplateDefinition(template) : undefined;

    yield { type: 'status', stage: 'building_prompt' };

    // Build orchestrator prompt
    const [systemPrompt, userPrompt] = await buildOrchestratorPrompt(
      seed,
      mode,
      templateAssets
    );

    yield { type: 'status', stage: 'generating' };

    // Generate response
    const messages = formatMessages(systemPrompt, userPrompt);
    let fullContent = '';

    if (stream) {
      for await (const chunk of engine.generateStream(messages)) {
        if (chunk.content) {
          fullContent += chunk.content;
          yield {
            type: 'chunk',
            content: chunk.content,
          };
        }
        if (chunk.done) {
          break;
        }
      }
    } else {
      const result = await engine.generate(messages);
      fullContent = result.content;
    }

    yield { type: 'status', stage: 'parsing' };

    // Parse the response into assets
    let assets: Record<string, string>;
    try {
      assets = templateDefinition
        ? parseGeneratedBlueprintOutput(fullContent, templateDefinition).assets
        : this.parseBlueprintOutput(fullContent);
    } catch {
      assets = this.parseBlueprintOutput(fullContent);
    }

    yield { type: 'status', stage: 'saving' };

    // Save draft
    const reviewId = this.generateReviewId();
    const characterName = inferCharacterDisplayNameForTemplate(assets, template);
    const draft: Draft = {
      path: reviewId,
      metadata: {
        review_id: reviewId,
        seed,
        mode,
        model: config.model,
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        favorite: false,
        template_name: template,
        character_name: characterName,
      },
      assets,
    };

    await DraftStorage.saveDraft(draft);

    yield {
      type: 'complete',
      asset: reviewId,
    };
  }

  /**
   * Generate a single asset
   */
  static async *generateAsset(
    request: GenerateAssetRequest,
    stream: boolean = true
  ): AsyncIterable<GenerationProgress> {
    const blueprintContent = resolveTemplateBlueprintContent(request.template, request.asset_name);
    yield* this.generateAssetWithBlueprint(request, blueprintContent, stream);
  }

  static async *previewBlueprint(
    request: GenerateAssetRequest & { blueprint_content: string },
    stream: boolean = true
  ): AsyncIterable<GenerationProgress> {
    yield* this.generateAssetWithBlueprint(request, request.blueprint_content, stream);
  }

  private static async *generateAssetWithBlueprint(
    request: GenerateAssetRequest,
    blueprintContent: string | undefined,
    stream: boolean
  ): AsyncIterable<GenerationProgress> {
    const { seed, mode = 'Auto', asset_name, prior_assets } = request;

    yield { type: 'status', stage: 'initializing' };

    const engine = this.createConfiguredEngine();

    yield { type: 'status', stage: 'building_prompt' };

    // Build asset prompt
    const [systemPrompt, userPrompt] = await buildAssetPrompt(
      asset_name,
      seed,
      mode,
      prior_assets,
      blueprintContent
    );

    yield {
      type: 'status',
      stage: 'prompt_ready',
      asset: asset_name,
      systemPrompt,
      userPrompt,
    };

    yield { type: 'status', stage: 'generating', asset: asset_name };

    // Generate response
    const messages = formatMessages(systemPrompt, userPrompt);
    let fullContent = '';

    if (stream) {
      for await (const chunk of engine.generateStream(messages)) {
        if (chunk.content) {
          fullContent += chunk.content;
          yield {
            type: 'chunk',
            content: chunk.content,
            asset: asset_name,
          };
        }
        if (chunk.done) {
          break;
        }
      }
    } else {
      const result = await engine.generate(messages);
      fullContent = result.content;
    }

    yield {
      type: 'asset',
      asset: asset_name,
      content: fullContent,
      systemPrompt,
      userPrompt,
    };
  }

  /**
   * Generate offspring from two parents
   */
  static async *generateOffspring(
    request: OffspringRequest
  ): AsyncIterable<GenerationProgress> {
    const { parent1_id, parent2_id, seed, mode = 'Auto', template } = request;

    yield { type: 'status', stage: 'loading_parents' };

    // Load parent drafts
    const parent1 = await DraftStorage.getDraft(parent1_id);
    const parent2 = await DraftStorage.getDraft(parent2_id);

    if (!parent1 || !parent2) {
      yield {
        type: 'error',
        error: 'Parent drafts not found',
      };
      return;
    }

    yield { type: 'status', stage: 'building_prompt' };

    // Get API keys and config
    const apiKeys = configManager.getApiKeys();
    const config = configManager.getConfig();

    // Create engine
    const provider = this.resolveConfiguredProvider(config);
    const engine = createEngine({
      model: config.model,
      apiKey: provider ? apiKeys[provider] : this.getFallbackApiKey(apiKeys),
      apiKeys,
      provider,
      baseUrl: config.base_url,
      temperature: config.temperature,
      maxTokens: config.max_tokens,
    });

    // Build offspring prompt
    const [systemPrompt, userPrompt] = await buildOffspringPrompt(
      parent1.assets,
      parent2.assets,
      parent1.metadata.character_name || 'Parent 1',
      parent2.metadata.character_name || 'Parent 2',
      mode
    );

    yield { type: 'status', stage: 'generating' };

    // Generate seed
    const messages = formatMessages(systemPrompt, userPrompt);
    const result = await engine.generate(messages);
    const offspringSeed = result.content.trim();

    // Now generate the full character from the seed
    yield { type: 'status', stage: 'generating_character' };

    const [orchestratorSystem, orchestratorUser] = await buildOrchestratorPrompt(
      offspringSeed,
      mode,
      resolveTemplateAssets(template)
    );

    const orchestratorMessages = formatMessages(orchestratorSystem, orchestratorUser);
    const orchestratorResult = await engine.generate(orchestratorMessages);
    let assets: Record<string, string>;
    const templateDefinition = template ? resolveTemplateDefinition(template) : undefined;
    try {
      assets = templateDefinition
        ? parseGeneratedBlueprintOutput(orchestratorResult.content, templateDefinition).assets
        : this.parseBlueprintOutput(orchestratorResult.content);
    } catch {
      assets = this.parseBlueprintOutput(orchestratorResult.content);
    }

    yield { type: 'status', stage: 'saving' };

    // Save draft
    const reviewId = this.generateReviewId();
    const characterName = inferCharacterDisplayNameForTemplate(assets, template);
    const draft: Draft = {
      path: reviewId,
      metadata: {
        review_id: reviewId,
        seed: offspringSeed,
        mode,
        model: config.model,
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        favorite: false,
        template_name: template,
        parent_drafts: [parent1_id, parent2_id],
        offspring_type: 'offspring',
        character_name: characterName,
      },
      assets,
    };

    await DraftStorage.saveDraft(draft);

    yield {
      type: 'complete',
      asset: reviewId,
    };
  }

  /**
   * Generate seeds from genre lines
   */
  static async *generateSeeds(request: SeedGenerationRequest | string): AsyncIterable<GenerationProgress> {
    yield { type: 'status', stage: 'initializing' };

    const resolvedRequest = typeof request === 'string'
      ? { genre_lines: request }
      : request;
    const { genreLines } = resolveSeedGenerationInput(resolvedRequest);

    // Get API keys and config
    const apiKeys = configManager.getApiKeys();
    const config = configManager.getConfig();

    // Create engine
    const provider = this.resolveConfiguredProvider(config);
    const engine = createEngine({
      model: config.model,
      apiKey: provider ? apiKeys[provider] : this.getFallbackApiKey(apiKeys),
      apiKeys,
      provider,
      baseUrl: config.base_url,
      temperature: config.temperature,
      maxTokens: config.max_tokens,
    });

    yield { type: 'status', stage: 'building_prompt' };

    // Build seed generation prompt
    const [systemPrompt, userPrompt] = await buildSeedGenPrompt(genreLines);

    yield { type: 'status', stage: 'generating' };

    // Generate seeds
    const messages = formatMessages(systemPrompt, userPrompt);
    const result = await engine.generate(messages);

    // Parse seeds (one per line)
    const seeds = parseSeedGenerationResponse(result.content);

    yield {
      type: 'complete',
      content: seeds.join('\n'),
    };
  }

  /**
   * Chat with LLM (for refinement/assistance)
   */
  static async *chat(
    draftId: string,
    messages: ChatMessage[],
    contextAsset?: string
  ): AsyncIterable<GenerationProgress> {
    yield { type: 'status', stage: 'initializing' };

    // Get API keys and config
    const apiKeys = configManager.getApiKeys();
    const config = configManager.getConfig();

    // Create engine
    const provider = this.resolveConfiguredProvider(config);
    const engine = createEngine({
      model: config.model,
      apiKey: provider ? apiKeys[provider] : this.getFallbackApiKey(apiKeys),
      apiKeys,
      provider,
      baseUrl: config.base_url,
      temperature: config.temperature,
      maxTokens: config.max_tokens,
    });

    yield { type: 'status', stage: 'generating' };

    // Use first message as system if provided, otherwise use default
    let systemPrompt = messages[0]?.role === 'system' ? messages[0].content : undefined;
    const chatMessages = systemPrompt
      ? messages.slice(1)
      : messages;

    // Generate response
    let fullContent = '';

    for await (const chunk of engine.generateStream(chatMessages)) {
      if (chunk.content) {
        fullContent += chunk.content;
        yield {
          type: 'chunk',
          content: chunk.content,
        };
      }
      if (chunk.done) {
        break;
      }
    }

    yield {
      type: 'complete',
      content: fullContent,
    };
  }

  /**
   * Analyze similarity between two characters
   */
  static async analyzeSimilarity(
    draft1Id: string,
    draft2Id: string
  ): Promise<unknown> {
    // Load drafts
    const draft1 = await DraftStorage.getDraft(draft1Id);
    const draft2 = await DraftStorage.getDraft(draft2Id);

    if (!draft1 || !draft2) {
      throw new Error('One or both drafts not found');
    }

    // Extract character profiles from character sheets
    const profile1 = this.parseCharacterProfile(draft1.assets.character_sheet || '');
    const profile2 = this.parseCharacterProfile(draft2.assets.character_sheet || '');

    // Get API keys and config
    const apiKeys = configManager.getApiKeys();
    const config = configManager.getConfig();

    // Create engine
    const provider = this.resolveConfiguredProvider(config);
    const engine = createEngine({
      model: config.model,
      apiKey: provider ? apiKeys[provider] : this.getFallbackApiKey(apiKeys),
      apiKeys,
      provider,
      baseUrl: config.base_url,
      temperature: config.temperature,
      maxTokens: config.max_tokens,
    });

    // Build similarity prompt
    const [systemPrompt, userPrompt] = buildSimilarityPrompt(profile1, profile2);
    const messages = formatMessages(systemPrompt, userPrompt);

    // Generate analysis
    const result = await engine.generate(messages);

    // Parse JSON response
    try {
      return JSON.parse(result.content);
    } catch {
      // Return text if JSON parsing fails
      return { raw: result.content };
    }
  }

  /**
   * Parse blueprint output into asset dictionary
   */
  private static parseBlueprintOutput(content: string): Record<string, string> {
    const assets: Record<string, string> = {};

    // Look for code blocks with asset names
    // Format: ```asset_name ... content ... ```
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;

    // Known asset names in order
    const knownAssets = [
      'Adjustment Note',
      'system_prompt',
      'post_history',
      'character_sheet',
      'intro_scene',
      'intro_page',
      'a1111',
      'suno',
    ];

    // Try to match code blocks with asset name
    let match: RegExpExecArray | null;
    while ((match = codeBlockRegex.exec(content)) !== null) {
      const assetName = match[1];
      const assetContent = match[2]?.trim();

      if (assetName && assetContent && knownAssets.includes(assetName)) {
        assets[assetName] = assetContent;
      }
    }

    // If no code blocks found, try to parse by known sections
    if (Object.keys(assets).length === 0) {
      for (let i = 0; i < knownAssets.length; i++) {
        const asset = knownAssets[i];
        const nextAsset = knownAssets[i + 1];

        const startRegex = new RegExp(`^##\\s*${asset}`, 'im');
        const startMatch = content.search(startRegex);

        if (startMatch === -1) continue;

        let endMatch: number;
        if (nextAsset) {
          const endRegex = new RegExp(`^##\\s*${nextAsset}`, 'im');
          const endSearch = content.slice(startMatch).search(endRegex);
          endMatch = endSearch === -1 ? content.length : startMatch + endSearch;
        } else {
          endMatch = content.length;
        }

        const assetContent = content.slice(startMatch, endMatch).trim();
        if (assetContent) {
          assets[asset] = assetContent;
        }
      }
    }

    return assets;
  }

  /**
   * Parse character sheet into profile object
   */
  private static parseCharacterProfile(characterSheet: string): Record<string, unknown> {
    const profile: Record<string, unknown> = {};

    // Simple key-value parsing from character sheet
    // Format: Key: Value
    const lines = characterSheet.split('\n');
    let currentKey: string | null = null;
    let currentValue: string[] = [];

    for (const line of lines) {
      const keyMatch = line.match(/^([A-Z][A-Za-z\s]+):\s*(.+)$/);
      if (keyMatch) {
        // Save previous key-value pair
        if (currentKey && currentValue.length > 0) {
          profile[currentKey] = currentValue.join('\n').trim();
        }

        currentKey = keyMatch[1].trim().toLowerCase().replace(/\s+/g, '_');
        currentValue = [keyMatch[2].trim()];
      } else if (currentKey && line.trim()) {
        currentValue.push(line.trim());
      }
    }

    // Save last key-value pair
    if (currentKey && currentValue.length > 0) {
      profile[currentKey] = currentValue.join('\n').trim();
    }

    // Extract arrays from comma-separated values
    for (const key of ['personality_traits', 'core_values', 'goals', 'fears', 'motivations']) {
      if (typeof profile[key] === 'string') {
        profile[key] = (profile[key] as string)
          .split(',')
          .map(s => s.trim())
          .filter(s => s.length > 0);
      }
    }

    return profile;
  }

  /**
   * Generate a unique review ID
   */
  private static generateReviewId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 9);
    return `${timestamp}_${random}`;
  }
}

/**
 * Default export
 */
export default GenerationService;
