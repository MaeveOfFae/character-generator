import { CharacterGeneratorAPI } from '@char-gen/shared';
import { NativeModules, Platform } from 'react-native';

const BACKEND_PORT = '8000';
const PRODUCTION_API_BASE_URL = 'https://your-api-url.com/api';

function extractHostname(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const normalized = value
    .replace(/^exp:\/\//, 'http://')
    .replace(/^exps:\/\//, 'https://');

  try {
    return new URL(normalized).hostname;
  } catch {
    const match = normalized.match(/\/\/([^/:]+)/);
    return match ? match[1] : null;
  }
}

function resolveDevHost(): string {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location.hostname) {
    return window.location.hostname;
  }

  const hostFromBundle = extractHostname(NativeModules.SourceCode?.scriptURL);
  if (hostFromBundle) {
    return hostFromBundle;
  }

  return Platform.OS === 'android' ? '10.0.2.2' : '127.0.0.1';
}

const API_BASE_URL = __DEV__
  ? `http://${resolveDevHost()}:${BACKEND_PORT}/api`
  : PRODUCTION_API_BASE_URL;

export const api = new CharacterGeneratorAPI(API_BASE_URL);
