import type { ContentMode } from '@char-gen/shared';

const ACTIVE_GENERATION_SESSION_KEY = 'eidolon.active-generation-session';

export type ActiveGenerationStatus = 'initializing' | 'generating' | 'reviewing' | 'saving';

export interface ActiveGenerationSession {
  version: 1;
  seed: string;
  mode: ContentMode;
  template?: string;
  assetDrafts: Record<string, string>;
  currentAsset: string | null;
  currentAssetContent: string;
  currentStatus: ActiveGenerationStatus;
  startedAt: number;
  updatedAt: number;
}

function canUseStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function isValidSession(value: unknown): value is ActiveGenerationSession {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const session = value as Partial<ActiveGenerationSession>;
  return session.version === 1
    && typeof session.seed === 'string'
    && typeof session.mode === 'string'
    && (typeof session.template === 'string' || typeof session.template === 'undefined')
    && !!session.assetDrafts
    && typeof session.assetDrafts === 'object'
    && (typeof session.currentAsset === 'string' || session.currentAsset === null)
    && typeof session.currentAssetContent === 'string'
    && typeof session.currentStatus === 'string'
    && typeof session.startedAt === 'number'
    && typeof session.updatedAt === 'number';
}

export function loadActiveGenerationSession(): ActiveGenerationSession | null {
  if (!canUseStorage()) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(ACTIVE_GENERATION_SESSION_KEY);
    if (!raw) {
      return null;
    }

    const parsed: unknown = JSON.parse(raw);
    return isValidSession(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function saveActiveGenerationSession(session: ActiveGenerationSession): void {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(ACTIVE_GENERATION_SESSION_KEY, JSON.stringify(session));
}

export function clearActiveGenerationSession(): void {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.removeItem(ACTIVE_GENERATION_SESSION_KEY);
}

export function matchesActiveGenerationSession(
  session: ActiveGenerationSession,
  params: { seed: string; mode: ContentMode; template?: string }
): boolean {
  return session.seed === params.seed
    && session.mode === params.mode
    && (session.template || '') === (params.template || '');
}