/**
 * Client-Side Configuration Manager
 * Handles configuration persistence in localStorage with API key management
 */

import type {
  ApiKeys,
  Config,
} from '@char-gen/shared';

const CONFIG_STORAGE_KEY = 'bpui.web.config';
const API_KEYS_STORAGE_KEY = 'bpui.web.apiKeys';
const API_KEYS_PERSISTENCE_KEY = 'bpui.web.apiKeys.persist';

/**
 * In-memory API keys storage (cleared on page refresh by default)
 * Can be persisted to localStorage with user consent
 */
let sessionApiKeys: ApiKeys = {};

const CORRUPTED_API_KEY_PATTERNS = [
  /^window\.fetch:/i,
  /cannot convert value in record<bytestring/i,
  /^bearer\s+window\.fetch:/i,
];

export function normalizeApiKeyValue(value: string): string {
  return value
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .trim()
    .replace(/^['"]+|['"]+$/g, '');
}

export function isInvalidApiKeyValue(value: string): boolean {
  if (!value) {
    return true;
  }

  if (/[^\x20-\x7E]/.test(value)) {
    return true;
  }

  if (/\r|\n/.test(value)) {
    return true;
  }

  return CORRUPTED_API_KEY_PATTERNS.some((pattern) => pattern.test(value));
}

function normalizeApiKeys(keys: ApiKeys): ApiKeys {
  return Object.fromEntries(
    Object.entries(keys)
      .map(([provider, key]) => [provider, typeof key === 'string' ? normalizeApiKeyValue(key) : key])
      .filter(([, key]) => typeof key === 'string' && !isInvalidApiKeyValue(key))
      .filter(([, key]) => typeof key === 'string' && key.length > 0)
  );
}
let persistKeys = false;

export interface ConfigManagerOptions {
  /**
   * Whether to persist API keys to localStorage
   * Default: false (keys only in memory)
   */
  persistApiKeys?: boolean;
}

/**
 * Client-side configuration manager
 */
export class ConfigManager {
  private config: Config;
  private options: ConfigManagerOptions;

  constructor(options: ConfigManagerOptions = {}) {
    this.options = {
      persistApiKeys: false,
      ...options,
    };

    persistKeys = this.loadPersistPreference(this.options.persistApiKeys || false);

    // Load config from localStorage or use defaults
    this.config = this.loadConfig();
    this.loadPersistedApiKeys();
  }

  private loadPersistPreference(defaultValue: boolean): boolean {
    try {
      const stored = localStorage.getItem(API_KEYS_PERSISTENCE_KEY);
      if (stored === 'true') {
        return true;
      }
      if (stored === 'false') {
        return false;
      }
    } catch {
      // Ignore parse errors
    }

    return defaultValue;
  }

  private savePersistPreference(value: boolean): void {
    try {
      localStorage.setItem(API_KEYS_PERSISTENCE_KEY, String(value));
    } catch (error) {
      console.warn('Failed to save API key persistence preference:', error);
    }
  }

  private loadConfig(): Config {
    try {
      const stored = localStorage.getItem(CONFIG_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Ignore parse errors
    }

    return this.getDefaultConfig();
  }

  private saveConfig(): void {
    try {
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(this.config));
    } catch (error) {
      console.warn('Failed to save config to localStorage:', error);
    }
  }

  private getDefaultConfig(): Config {
    return {
      engine: 'openai_compatible',
      engine_mode: 'auto',
      model: 'openrouter/openai/gpt-4o-mini',
      temperature: 0.7,
      max_tokens: 4096,
      api_keys: {},
      batch: {
        max_concurrent: 3,
        rate_limit_delay: 1000,
      },
    };
  }

  /**
   * Get the current configuration
   */
  getConfig(): Config {
    return { ...this.config };
  }

  /**
   * Get API keys (from session or localStorage)
   */
  getApiKeys(): ApiKeys {
    return normalizeApiKeys(sessionApiKeys);
  }

  /**
   * Get a specific API key
   */
  getApiKey(provider: string): string | undefined {
    const key = sessionApiKeys[provider];
    return typeof key === 'string' ? normalizeApiKeyValue(key) : undefined;
  }

  /**
   * Set an API key (stored in session, persisted if enabled)
   */
  setApiKey(provider: string, key: string): void {
    const normalizedKey = normalizeApiKeyValue(key);
    if (normalizedKey) {
      sessionApiKeys[provider] = normalizedKey;
    } else {
      delete sessionApiKeys[provider];
    }
    this.persistApiKeysIfNeeded();
  }

  /**
   * Set multiple API keys
   */
  setApiKeys(keys: ApiKeys): void {
    sessionApiKeys = {
      ...normalizeApiKeys(sessionApiKeys),
      ...normalizeApiKeys(keys),
    };
    this.persistApiKeysIfNeeded();
  }

  /**
   * Clear an API key
   */
  clearApiKey(provider: string): void {
    delete sessionApiKeys[provider];
    this.persistApiKeysIfNeeded();
  }

  /**
   * Clear all API keys
   */
  clearAllApiKeys(): void {
    sessionApiKeys = {};
    this.persistApiKeysIfNeeded();
  }

  /**
   * Load API keys from localStorage (for persistence mode)
   */
  private loadPersistedApiKeys(): void {
    if (!persistKeys) {
      return;
    }

    try {
      const stored = localStorage.getItem(API_KEYS_STORAGE_KEY);
      if (stored) {
        sessionApiKeys = normalizeApiKeys(JSON.parse(stored) as ApiKeys);
      }
    } catch {
      // Ignore parse errors
    }
  }

  /**
   * Persist API keys to localStorage if enabled
   */
  private persistApiKeysIfNeeded(): void {
    if (persistKeys) {
      try {
        localStorage.setItem(API_KEYS_STORAGE_KEY, JSON.stringify(normalizeApiKeys(sessionApiKeys)));
      } catch (error) {
        console.warn('Failed to persist API keys:', error);
      }
    }
  }

  /**
   * Toggle API key persistence
   */
  setPersistApiKeys(persist: boolean): void {
    persistKeys = persist;
    this.savePersistPreference(persist);

    if (persist) {
      this.persistApiKeysIfNeeded();
    } else {
      // Clear persisted keys if disabling persistence
      try {
        localStorage.removeItem(API_KEYS_STORAGE_KEY);
      } catch {
        // Ignore errors
      }
    }
  }

  /**
   * Check if API keys are being persisted
   */
  isPersistingApiKeys(): boolean {
    return persistKeys;
  }

  /**
   * Export API keys as JSON (for backup)
   */
  exportApiKeys(): string {
    return JSON.stringify(normalizeApiKeys(sessionApiKeys), null, 2);
  }

  /**
   * Import API keys from JSON (for restore)
   */
  importApiKeys(json: string): void {
    try {
      const keys = JSON.parse(json) as ApiKeys;
      sessionApiKeys = normalizeApiKeys(keys);
      this.persistApiKeysIfNeeded();
    } catch {
      throw new Error('Invalid API keys JSON');
    }
  }

  /**
   * Update configuration
   */
  updateConfig(updates: Partial<Config>): void {
    this.config = { ...this.config, ...updates };
    this.saveConfig();
  }

  /**
   * Reset configuration to defaults
   */
  resetConfig(): void {
    this.config = this.getDefaultConfig();
    this.saveConfig();
  }

  /**
   * Export configuration as JSON
   */
  exportConfig(): string {
    const exportData = {
      config: this.config,
      version: '1.0',
      exportedAt: new Date().toISOString(),
    };
    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Import configuration from JSON
   */
  importConfig(json: string): void {
    try {
      const data = JSON.parse(json);
      if (data.config) {
        this.config = { ...this.getDefaultConfig(), ...data.config };
        this.saveConfig();
      }
    } catch {
      throw new Error('Invalid configuration JSON');
    }
  }

  /**
   * Clear all stored data (config and API keys)
   */
  clearAll(): void {
    this.config = this.getDefaultConfig();
    sessionApiKeys = {};
    persistKeys = false;
    try {
      localStorage.removeItem(CONFIG_STORAGE_KEY);
      localStorage.removeItem(API_KEYS_STORAGE_KEY);
      localStorage.removeItem(API_KEYS_PERSISTENCE_KEY);
    } catch {
      // Ignore errors
    }
  }
}

// Global instance
export const configManager = new ConfigManager();

/**
 * Get API keys for use in API headers (base64 encoded)
 */
export function getApiKeysHeader(): Record<string, string> | undefined {
  const keys = configManager.getApiKeys();
  if (Object.keys(keys).length === 0) {
    return undefined;
  }

  // Encode as base64 for safe transmission
  const encoded = btoa(JSON.stringify(keys));
  return {
    'X-BPUI-API-KEYS': encoded,
  };
}

/**
 * Parse API keys from header value
 */
export function parseApiKeysHeader(header: string): ApiKeys {
  try {
    const decoded = atob(header);
    return JSON.parse(decoded) as ApiKeys;
  } catch {
    return {};
  }
}
