import {
  OFFICIAL_TEMPLATE,
  getOrderedAssets,
  inferCharacterDisplayNameFromAssets,
  type Template,
} from '@char-gen/shared';
import { parseBlueprintFrontmatter, type TemplateAsset, templateToAssets } from '../prompting/blueprint.js';

const CUSTOM_TEMPLATES_STORAGE_KEY = 'eidolon.web.templates.custom';
const LEGACY_CUSTOM_TEMPLATES_STORAGE_KEYS = ['bpui.web.templates.custom'];
const BLUEPRINT_OVERRIDES_STORAGE_KEY = 'eidolon.web.blueprints.overrides';
const LEGACY_BLUEPRINT_OVERRIDES_STORAGE_KEYS = ['bpui.web.blueprints.overrides'];

const blueprintModules = import.meta.glob('../../../../../blueprints/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

export interface StoredTemplateRecord {
  template: Template;
  blueprint_contents: Record<string, string>;
}

type BlueprintCategory = 'core' | 'system' | 'template' | 'example';

interface BrowserBlueprint {
  name: string;
  description: string;
  invokable: boolean;
  version: string;
  content: string;
  path: string;
  category: BlueprintCategory;
}

function getAssetBlueprintKey(asset: { name: string; blueprint_file?: string }): string {
  return asset.blueprint_file ?? `${asset.name}.md`;
}

function readStorage<T>(keys: string | readonly string[], fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const keyList = Array.isArray(keys) ? [...keys] : [keys];
  const [currentKey, ...legacyKeys] = keyList;

  try {
    for (const key of keyList) {
      const raw = window.localStorage.getItem(key);
      if (!raw) {
        continue;
      }

      const parsed = JSON.parse(raw) as T;
      if (key !== currentKey) {
        window.localStorage.setItem(currentKey, JSON.stringify(parsed));
        legacyKeys.forEach((legacyKey) => window.localStorage.removeItem(legacyKey));
      }

      return parsed;
    }
  } catch {
    return fallback;
  }

  return fallback;
}

function writeStorage<T>(key: string, legacyKeys: readonly string[], value: T): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
  legacyKeys.forEach((legacyKey) => window.localStorage.removeItem(legacyKey));
}

function buildDefaultBlueprintCatalog(): Map<string, BrowserBlueprint> {
  const catalog = new Map<string, BrowserBlueprint>();

  Object.entries(blueprintModules).forEach(([modulePath, content]) => {
    const normalizedPath = modulePath.replace(/^.*\/blueprints\//, 'blueprints/');
    const fileName = normalizedPath.split('/').pop()?.toLowerCase();
    if (fileName === 'readme.md') {
      return;
    }

    const metadata = parseBlueprintFrontmatter(content);

    let category: BlueprintCategory = 'core';
    if (normalizedPath.includes('/system/')) {
      category = 'system';
    } else if (normalizedPath.includes('/templates/')) {
      category = 'template';
    } else if (normalizedPath.includes('/examples/')) {
      category = 'example';
    }

    catalog.set(normalizedPath, {
      name: metadata.name,
      description: metadata.description,
      invokable: metadata.invokable,
      version: metadata.version,
      content,
      path: normalizedPath,
      category,
    });
  });

  return catalog;
}

export function getBlueprintOverrides(): Record<string, string> {
  return readStorage<Record<string, string>>(
    [BLUEPRINT_OVERRIDES_STORAGE_KEY, ...LEGACY_BLUEPRINT_OVERRIDES_STORAGE_KEYS],
    {}
  );
}

export function saveBlueprintOverrides(overrides: Record<string, string>): void {
  writeStorage(BLUEPRINT_OVERRIDES_STORAGE_KEY, LEGACY_BLUEPRINT_OVERRIDES_STORAGE_KEYS, overrides);
}

export function getBlueprintCatalog(): Map<string, BrowserBlueprint> {
  const catalog = buildDefaultBlueprintCatalog();
  const overrides = getBlueprintOverrides();

  Object.entries(overrides).forEach(([path, content]) => {
    const metadata = parseBlueprintFrontmatter(content);
    const existing = catalog.get(path);
    catalog.set(path, {
      name: metadata.name,
      description: metadata.description,
      invokable: metadata.invokable,
      version: metadata.version,
      content,
      path,
      category: existing?.category ?? 'core',
    });
  });

  return catalog;
}

export function findBlueprintContent(fileName?: string): string {
  if (!fileName) {
    return '';
  }

  const normalizedFileName = fileName.replace(/^\.?\//, '');
  const targetBase = normalizedFileName.replace(/\.(txt|md)$/i, '');
  const match = [...getBlueprintCatalog().values()].find((blueprint) => (
    blueprint.path === normalizedFileName
      || blueprint.path.endsWith(`/${normalizedFileName}`)
      || blueprint.path.endsWith(`/${targetBase}.md`)
  ));

  return match?.content ?? '';
}

function getLegacyBlueprintContent(
  blueprintContents: Record<string, string>,
  asset: { name: string; blueprint_file?: string }
): string | undefined {
  const blueprintKey = getAssetBlueprintKey(asset);
  const shortFileName = blueprintKey.split('/').pop() ?? blueprintKey;

  return blueprintContents[blueprintKey]
    ?? blueprintContents[shortFileName]
    ?? blueprintContents[asset.name];
}

function normalizeTemplateRecord(record: StoredTemplateRecord): StoredTemplateRecord {
  const normalizedContents: Record<string, string> = {};

  record.template.assets.forEach((asset) => {
    const blueprintKey = getAssetBlueprintKey(asset);
    const content = getLegacyBlueprintContent(record.blueprint_contents, asset);
    if (!content?.trim()) {
      return;
    }

    const builtinContent = findBlueprintContent(blueprintKey);
    if (builtinContent && builtinContent === content) {
      return;
    }

    normalizedContents[blueprintKey] = content;
  });

  Object.entries(record.blueprint_contents).forEach(([key, content]) => {
    if (!content?.trim() || normalizedContents[key]) {
      return;
    }

    const builtinContent = findBlueprintContent(key);
    if (builtinContent && builtinContent === content) {
      return;
    }

    normalizedContents[key] = content;
  });

  return {
    template: record.template,
    blueprint_contents: normalizedContents,
  };
}

function hydrateTemplateRecord(record: StoredTemplateRecord): StoredTemplateRecord {
  const normalized = normalizeTemplateRecord(record);
  const blueprintContents = { ...normalized.blueprint_contents };

  normalized.template.assets.forEach((asset) => {
    const blueprintKey = getAssetBlueprintKey(asset);
    if (!blueprintContents[blueprintKey]) {
      const builtinContent = findBlueprintContent(blueprintKey);
      if (builtinContent) {
        blueprintContents[blueprintKey] = builtinContent;
      }
    }
  });

  return {
    template: normalized.template,
    blueprint_contents: blueprintContents,
  };
}

function getDefaultTemplateStorageRecord(): StoredTemplateRecord {
  return {
    template: {
      ...OFFICIAL_TEMPLATE,
      is_default: true,
    },
    blueprint_contents: {},
  };
}

export function getStoredTemplates(): StoredTemplateRecord[] {
  const stored = readStorage<StoredTemplateRecord[]>(
    [CUSTOM_TEMPLATES_STORAGE_KEY, ...LEGACY_CUSTOM_TEMPLATES_STORAGE_KEYS],
    []
  );
  const normalized = stored.map(normalizeTemplateRecord);

  if (JSON.stringify(stored) !== JSON.stringify(normalized)) {
    writeStorage(CUSTOM_TEMPLATES_STORAGE_KEY, LEGACY_CUSTOM_TEMPLATES_STORAGE_KEYS, normalized);
  }

  return normalized;
}

export function saveStoredTemplates(records: StoredTemplateRecord[]): void {
  writeStorage(
    CUSTOM_TEMPLATES_STORAGE_KEY,
    LEGACY_CUSTOM_TEMPLATES_STORAGE_KEYS,
    records.map(normalizeTemplateRecord)
  );
}

export function getAllTemplateRecords(): StoredTemplateRecord[] {
  return [
    hydrateTemplateRecord(getDefaultTemplateStorageRecord()),
    ...getStoredTemplates().map(hydrateTemplateRecord),
  ];
}

export function getStoredTemplateRecord(name?: string): StoredTemplateRecord | undefined {
  if (!name) {
    return undefined;
  }

  const defaultRecord = getDefaultTemplateStorageRecord();
  if (defaultRecord.template.name === name) {
    return defaultRecord;
  }

  return getStoredTemplates().find((record) => record.template.name === name);
}

export function getTemplateRecord(name?: string): StoredTemplateRecord | undefined {
  if (!name) {
    return undefined;
  }

  return getAllTemplateRecords().find((record) => record.template.name === name);
}

export function resolveTemplateDefinition(name?: string): Template | undefined {
  return getTemplateRecord(name)?.template;
}

export function resolveTemplateAssets(name?: string): TemplateAsset[] | undefined {
  const template = resolveTemplateDefinition(name);
  return template ? templateToAssets(template) : undefined;
}

export function resolveTemplateBlueprintContent(templateName: string | undefined, assetName: string): string | undefined {
  const record = getTemplateRecord(templateName);
  if (!record) {
    return undefined;
  }

  const asset = record.template.assets.find((candidate) => candidate.name === assetName);
  if (!asset) {
    return undefined;
  }

  const blueprintFile = getAssetBlueprintKey(asset);
  return record.blueprint_contents[blueprintFile] || findBlueprintContent(blueprintFile) || undefined;
}

export function inferCharacterDisplayNameForTemplate(
  assets: Record<string, string>,
  templateName?: string
): string | undefined {
  const template = resolveTemplateDefinition(templateName);
  const preferredAssets = template
    ? getOrderedAssets(template).map((asset) => asset.name)
    : ['character_sheet', 'char_basic_info'];

  const displayName = inferCharacterDisplayNameFromAssets(assets, preferredAssets);
  return displayName ?? undefined;
}