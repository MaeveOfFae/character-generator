/**
 * OpenAI-compatible REST API engine for direct provider calls.
 * Supports OpenRouter, DeepSeek, Anthropic, Zai, Moonshot, etc.
 */

import type {
  LLMEngine,
  LLMChatMessage,
  GenerateOptions,
  GenerateResult,
  StreamChunk,
  StreamGenerateOptions,
  LLMConnectionTestResult,
  LLMProvider,
} from "./types";

interface OpenAICompatErrorResponse {
  error?: { message?: string } | string;
}

interface OpenAICompatUsage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}

interface OpenAICompatChoice {
  message?: { content?: string };
  finish_reason?: string;
  delta?: {
    content?: string;
    tool_calls?: unknown[];
  };
}

interface OpenAICompatChatCompletionResponse {
  choices?: OpenAICompatChoice[];
  usage?: OpenAICompatUsage;
}

interface OpenAICompatModelSummary {
  id: string;
}

interface OpenAICompatModelsResponse {
  data?: OpenAICompatModelSummary[] | null;
}

function normalizeUsage(
  usage?: OpenAICompatUsage
): GenerateResult['usage'] {
  if (
    usage?.prompt_tokens === undefined ||
    usage.completion_tokens === undefined ||
    usage.total_tokens === undefined
  ) {
    return undefined;
  }

  return {
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    totalTokens: usage.total_tokens,
  };
}

export interface OpenAICompatConfig {
  provider: LLMProvider;
  model: string;
  apiKey: string;
  baseUrl: string;
  temperature?: number;
  maxTokens?: number;
  timeout?: number;
}

export class OpenAICompatEngine implements LLMEngine {
  private config: OpenAICompatConfig;

  constructor(config: OpenAICompatConfig) {
    this.config = {
      temperature: 0.7,
      maxTokens: 4096,
      timeout: 120000,
      ...config,
    };
  }

  getProvider(): LLMProvider {
    return this.config.provider;
  }

  getModel(): string {
    return this.config.model;
  }

  async generate(
    messages: LLMChatMessage[],
    options?: GenerateOptions
  ): Promise<GenerateResult> {
    const temperature = options?.temperature ?? this.config.temperature;
    const maxTokens = options?.maxTokens ?? this.config.maxTokens;

    const response = await fetch(this.config.baseUrl + "/chat/completions", {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify({
        model: this.config.model,
        messages,
        temperature,
        max_tokens: maxTokens,
        stream: false,
        ...(this.buildExtraParams(options)),
      }),
      signal: options?.signal,
    });

    if (!response.ok) {
      const error = await this.parseErrorResponse(response);
      throw new Error(error);
    }

    const responseJson = await response.json();
    const data = responseJson as OpenAICompatChatCompletionResponse;
    const content = data?.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error("No content in response");
    }

    return {
      content,
      finishReason: data?.choices?.[0]?.finish_reason,
      usage: normalizeUsage(data.usage),
    };
  }

  async *generateStream(
    messages: LLMChatMessage[],
    options?: StreamGenerateOptions
  ): AsyncIterable<StreamChunk> {
    const temperature = options?.temperature ?? this.config.temperature;
    const maxTokens = options?.maxTokens ?? this.config.maxTokens;

    const response = await fetch(this.config.baseUrl + "/chat/completions", {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify({
        model: this.config.model,
        messages,
        temperature,
        max_tokens: maxTokens,
        stream: true,
        ...(this.buildExtraParams(options)),
      }),
      signal: options?.signal,
    });

    if (!response.ok) {
      const error = await this.parseErrorResponse(response);
      throw new Error(error);
    }

    if (!response.body) {
      throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            if (dataStr.trim() === "[DONE]") {
              yield { content: "", done: true };
              return;
            }

            try {
              const data = JSON.parse(dataStr);
              const delta = data.choices?.[0]?.delta;
              if (delta?.content) {
                yield { content: delta.content, done: false };
              }
              if (delta?.tool_calls) {
                yield { content: JSON.stringify({ tool_calls: delta.tool_calls }), done: false };
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async testConnection(): Promise<LLMConnectionTestResult> {
    const start = performance.now();

    try {
      const response = await fetch(this.config.baseUrl + "/chat/completions", {
        method: "POST",
        headers: this.buildHeaders(),
        body: JSON.stringify({
          model: this.config.model,
          messages: [{ role: "user", content: "test" }],
          max_tokens: 5,
          stream: false,
        }),
      });

      const latency = performance.now() - start;

      if (!response.ok) {
        const error = await this.parseErrorResponse(response);
        return {
          success: false,
          error,
          modelInfo: {
            name: this.config.model,
          },
        };
      }

      return {
        success: true,
        latencyMs: Math.round(latency),
        modelInfo: {
          name: this.config.model,
        },
      };
    } catch (e) {
      return {
        success: false,
        error: e instanceof Error ? e.message : "Unknown error",
        modelInfo: {
          name: this.config.model,
        },
      };
    }
  }

  private buildHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.config.apiKey) {
      headers["Authorization"] = "Bearer " + this.config.apiKey;
    }

    // OpenRouter-specific headers
    if (this.config.baseUrl.includes("openrouter.ai")) {
      headers["HTTP-Referer"] = "https://github.com/maeveoffae/character-generator";
      headers["X-OpenRouter-Title"] = "Eidolon Simulacra";
    }

    return headers;
  }

  private buildExtraParams(options?: GenerateOptions | StreamGenerateOptions): Record<string, unknown> {
    const params: Record<string, unknown> = {};

    if (options?.topP !== undefined) params.top_p = options.topP;
    if (options?.frequencyPenalty !== undefined) params.frequency_penalty = options.frequencyPenalty;
    if (options?.presencePenalty !== undefined) params.presence_penalty = options.presencePenalty;

    return params;
  }

  private async parseErrorResponse(response: Response): Promise<string> {
    try {
      const data = await response.json() as OpenAICompatErrorResponse;
      if (typeof data.error === 'object' && data.error?.message) {
        return data.error.message;
      }
      if (data.error) {
        return String(data.error);
      }
      return "HTTP " + response.status;
    } catch {
      return "HTTP " + response.status;
    }
  }
}

/**
 * List available models from an OpenAI-compatible API endpoint.
 */
export async function listModels(baseUrl: string, apiKey?: string): Promise<string[]> {
  const headers: Record<string, string> = {};

  if (apiKey) {
    headers["Authorization"] = "Bearer " + apiKey;
  }

  // OpenRouter-specific headers
  if (baseUrl.includes("openrouter.ai")) {
    headers["HTTP-Referer"] = "https://github.com/maeveoffae/character-generator";
    headers["X-OpenRouter-Title"] = "Eidolon Simulacra";
  }

  const response = await fetch(baseUrl + "/models", {
    method: "GET",
    headers,
  });

  if (response.status === 404) {
    return [];
  }

  if (!response.ok) {
    throw new Error("Failed to list models: HTTP " + response.status);
  }

  const responseJson = await response.json();
  const data = responseJson as OpenAICompatModelsResponse;
  const dataData = data.data;

  if (dataData && Array.isArray(dataData)) {
    return dataData.map((model) => model.id).sort();
  }

  return [];
}
