/**
 * Anthropic Claude LLM Engine
 * Handles Anthropic's API using their SDK
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

// Note: Anthropic SDK is installed as @anthropic-ai/sdk
// We'll use the REST API directly for better control and to avoid SDK size

interface AnthropicMessage {
  role: string;
  content: string;
}

interface AnthropicDelta {
  type: string;
  text?: string;
  stop_reason?: string;
}

interface AnthropicEvent {
  type: string;
  delta?: AnthropicDelta;
  message?: {
    content: Array<{ type: string; text: string }>;
    stop_reason?: string;
  };
}

interface AnthropicResponse {
  id: string;
  type: string;
  role: string;
  content: Array<{ type: string; text: string }>;
  stop_reason: string | null;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

interface AnthropicErrorResponse {
  type: string;
  error: {
    type: string;
    message: string;
  };
}

const ANTHROPIC_VERSION = '2023-06-01';

export class AnthropicEngine extends BaseLLMEngine {
  private baseUrl: string;

  constructor(config: LLMConfig) {
    super(config);
    this.baseUrl = config.baseUrl || 'https://api.anthropic.com';
  }

  private getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'x-api-key': this.config.apiKey || '',
      'anthropic-version': ANTHROPIC_VERSION,
    };
  }

  private formatMessages(messages: ChatMessage[]): AnthropicMessage[] {
    const formatted: AnthropicMessage[] = [];

    for (const msg of messages) {
      if (msg.role === 'system') {
        // System messages are handled separately in Anthropic API
        // We'll handle this in the request body
        continue;
      }
      formatted.push({
        role: msg.role === 'assistant' ? 'assistant' : 'user',
        content: msg.content,
      });
    }

    return formatted;
  }

  private getSystemPrompt(messages: ChatMessage[]): string | undefined {
    const systemMsg = messages.find(m => m.role === 'system');
    return systemMsg?.content;
  }

  async generate(
    messages: ChatMessage[],
    options?: GenerateOptions
  ): Promise<GenerateResult> {
    const opts = this.mergeOptions(options);

    const system = this.getSystemPrompt(messages);
    const messagesFormatted = this.formatMessages(messages);

    const body: Record<string, unknown> = {
      model: this.config.model,
      messages: messagesFormatted,
      max_tokens: opts.maxTokens || 4096,
      temperature: opts.temperature,
    };

    if (system) {
      body.system = system;
    }

    if (opts.topP !== undefined) {
      body.top_p = opts.topP;
    }

    const response = await fetch(`${this.baseUrl}/v1/messages`, {
      ...this.getFetchOptions(options?.signal),
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await this.parseError(response);
      throw new Error(error);
    }

    const data: AnthropicResponse = await response.json();

    const textContent = data.content.find(c => c.type === 'text');
    if (!textContent) {
      throw new Error('No text content in response');
    }

    return {
      content: textContent.text,
      finishReason: data.stop_reason || undefined,
      usage: {
        promptTokens: data.usage.input_tokens,
        completionTokens: data.usage.output_tokens,
        totalTokens: data.usage.input_tokens + data.usage.output_tokens,
      },
    };
  }

  async *generateStream(
    messages: ChatMessage[],
    options?: StreamGenerateOptions
  ): AsyncIterable<StreamChunk> {
    const opts = this.mergeOptions(options);

    const system = this.getSystemPrompt(messages);
    const messagesFormatted = this.formatMessages(messages);

    const body: Record<string, unknown> = {
      model: this.config.model,
      messages: messagesFormatted,
      max_tokens: opts.maxTokens || 4096,
      temperature: opts.temperature,
      stream: true,
    };

    if (system) {
      body.system = system;
    }

    if (opts.topP !== undefined) {
      body.top_p = opts.topP;
    }

    const response = await fetch(`${this.baseUrl}/v1/messages`, {
      ...this.getFetchOptions(options?.signal),
      method: 'POST',
      headers: {
        ...this.getHeaders(),
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(body),
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
          if (!trimmed || !trimmed.startsWith('data: ')) continue;

          try {
            const jsonStr = trimmed.slice(6);
            const event: AnthropicEvent = JSON.parse(jsonStr);

            if (event.type === 'content_block_delta' && event.delta?.text) {
              yield {
                content: event.delta.text,
                done: false,
              };
            }

            if (event.type === 'message_delta' && event.delta?.stop_reason) {
              yield {
                content: '',
                done: true,
                finishReason: event.delta.stop_reason,
              };
            }

            if (event.type === 'message_stop') {
              yield {
                content: '',
                done: true,
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
      const response = await fetch(`${this.baseUrl}/v1/messages`, {
        ...this.getFetchOptions(),
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          model: this.config.model,
          messages: [{ role: 'user', content: 'Hi' }],
          max_tokens: 1,
        }),
      });

      const latency_ms = performance.now() - startTime;

      if (!response.ok) {
        return {
          success: false,
          latency_ms,
          error: await this.parseError(response),
        };
      }

      return {
        success: true,
        latency_ms,
        model_info: {
          name: this.config.model,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  private async parseError(response: Response): Promise<string> {
    try {
      const data: AnthropicErrorResponse = await response.json();
      return data.error?.message || `HTTP ${response.status}`;
    } catch {
      return `HTTP ${response.status}`;
    }
  }
}
