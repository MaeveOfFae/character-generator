/**
 * Client-Side Services
 * Main entry point for all client-side services
 */

export * from './llm/index.js';
export * from './config/index.js';
export * from './storage/index.js';
export * from './prompting/index.js';
export * from './services/generation.js';

// Re-export shared LLM types so they're available in this package
export type {
  LLMProvider,
  LLMEngineMode,
  ChatMessage,
  GenerateOptions,
  GenerateResult,
  StreamChunk,
  StreamGenerateOptions,
  ConnectionTestResult,
  LLMEngine,
} from '@char-gen/shared';
