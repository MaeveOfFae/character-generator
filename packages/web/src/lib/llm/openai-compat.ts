/**
 * OpenAI-Compatible LLM Engine
 * Handles OpenAI, OpenRouter, DeepSeek, Zai, and Moonshot APIs
 */

import {
  BaseLLMEngine,
} from './base.js';
import type {
  ChatMessage,
  ConnectionTestResult,
  GenerateOptions,
  GenerateResult,
  LLMConfig,
  StreamChunk,
  StreamGenerateOptions,
} from '@char-gen/shared';

interface OpenAIChoice {
  message?: {
    role: string;
    content: string;
  };
  delta?: {
    content?: string;
  };
  finish_reason?: string;
}

interface OpenAIResponse {
  id?: string;
  choices: OpenAIChoice[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model?: string;
}

interface OpenAIErrorResponse {
  error?: {
    message: string;
    type?: string;
  };
}

export class OpenAICompatEngine extends BaseLLMEngine {
  private baseUrl: string;

  constructor(config: LLMConfig) {
    super(config);
    this.baseUrl = config.baseUrl || this.getDefaultBaseUrl();
  }

  private getDefaultBaseUrl(): string {
    switch (this.config.provider) {
      case 'openai':
        return 'https://api.openai.com/v1';
      case 'openrouter':
        return 'https://openrouter.ai/api/v1';
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

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    // Add OpenRouter-specific headers for better routing
    if (this.config.provider === 'openrouter') {
      headers['HTTP-Referer'] = typeof window !== 'undefined' ? window.location.href : 'https://char-gen.app';
      headers['X-Title'] = 'Character Generator';
    }

    return headers;
  }

  private formatMessages(messages: ChatMessage[]): Array<{
    role: string;
    content: string;
  }> {
    return messages.map(m => ({
      role: m.role,
      content: m.content,
    }));
  }

  async generate(
    messages: ChatMessage[],
    options?: GenerateOptions
  ): Promise<GenerateResult> {
    const opts = this.mergeOptions(options);

    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      ...this.getFetchOptions(options?.signal),
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        model: this.config.model,
        messages: this.formatMessages(messages),
        temperature: opts.temperature,
        max_tokens: opts.maxTokens,
        top_p: opts.topP,
        frequency_penalty: opts.frequencyPenalty,
        presence_penalty: opts.presencePenalty,
      }),
    });

    if (!response.ok) {
      const error = await this.parseError(response);
      throw new Error(error);
    }

    const data: OpenAIResponse = await response.json();

    const choice = data.choices[0];
    if (!choice?.message) {
      throw new Error('No content in response');
    }

    return {
      content: choice.message.content,
      finishReason: choice.finish_reason,
      usage: data.usage ? {
        promptTokens: data.usage.prompt_tokens,
        completionTokens: data.usage.completion_tokens,
        totalTokens: data.usage.total_tokens,
      } : undefined,
    };
  }

  async *generateStream(
    messages: ChatMessage[],
    options?: StreamGenerateOptions
  ): AsyncIterable<StreamChunk> {
    const opts = this.mergeOptions(options);

    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      ...this.getFetchOptions(options?.signal),
      method: 'POST',
      headers: {
        ...this.getHeaders(),
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: this.formatMessages(messages),
        temperature: opts.temperature,
        max_tokens: opts.maxTokens,
        top_p: opts.topP,
        frequency_penalty: opts.frequencyPenalty,
        presence_penalty: opts.presencePenalty,
        stream: true,
      }),
    });

    if (!response.ok) {
      const error = await this.parseError(response);
      throw new Error(error);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === 'data: [DONE]') continue;
          if (!trimmed.startsWith('data: ')) continue;

          try {
            const jsonStr = trimmed.slice(6);
            const data: OpenAIResponse = JSON.parse(jsonStr);

            const choice = data.choices[0];
            if (!choice) continue;

            const content = choice.delta?.content;
            if (content) {
              yield {
                content,
                done: false,
              };
            }

            if (choice.finish_reason) {
              yield {
                content: '',
                done: true,
                finishReason: choice.finish_reason,
              };
            }
          } catch {
            // Skip invalid JSON lines
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async testConnection(): Promise<ConnectionTestResult> {
    const startTime = performance.now();

    try {
      const response = await fetch(`${this.baseUrl}/models`, {
        ...this.getFetchOptions(),
        method: 'GET',
        headers: this.getHeaders(),
      });

      const latency_ms = performance.now() - startTime;

      if (!response.ok) {
        return {
          success: false,
          latency_ms,
          error: await this.parseError(response),
        };
      }

      // Try to get model info
      try {
        const data: { data?: Array<{ id: string }>; object?: string } = await response.json();
        const models = data.data || [];

        return {
          success: true,
          latency_ms,
          model_info: {
            name: this.config.model,
            context_length: undefined, // Would need model-specific lookup
          },
        };
      } catch {
        return {
          success: true,
          latency_ms,
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  private async parseError(response: Response): Promise<string> {
    try {
      const data: OpenAIErrorResponse = await response.json();
      return data.error?.message || `HTTP ${response.status}`;
    } catch {
      return `HTTP ${response.status}`;
    }
  }
}
