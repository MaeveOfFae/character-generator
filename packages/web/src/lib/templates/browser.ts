import {
  OFFICIAL_TEMPLATE,
  getOrderedAssets,
  inferCharacterDisplayNameFromAssets,
  type Template,
} from '@char-gen/shared';
import { parseBlueprintFrontmatter, type TemplateAsset, templateToAssets } from '../prompting/blueprint.js';

const CUSTOM_TEMPLATES_STORAGE_KEY = 'bpui.web.templates.custom';
const BLUEPRINT_OVERRIDES_STORAGE_KEY = 'bpui.web.blueprints.overrides';

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

function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
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
  return readStorage<Record<string, string>>(BLUEPRINT_OVERRIDES_STORAGE_KEY, {});
}

export function saveBlueprintOverrides(overrides: Record<string, string>): void {
  writeStorage(BLUEPRINT_OVERRIDES_STORAGE_KEY, overrides);
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

  const targetBase = fileName.replace(/\.(txt|md)$/i, '');
  const match = [...getBlueprintCatalog().values()].find((blueprint) => (
    blueprint.path.endsWith(`/${targetBase}.md`) || blueprint.path.endsWith(`/${fileName}`)
  ));

  return match?.content ?? '';
}

function getDefaultTemplateRecord(): StoredTemplateRecord {
  return {
    template: {
      ...OFFICIAL_TEMPLATE,
      is_default: true,
    },
    blueprint_contents: Object.fromEntries(
      OFFICIAL_TEMPLATE.assets.map((asset) => [
        asset.blueprint_file ?? `${asset.name}.md`,
        findBlueprintContent(asset.blueprint_file ?? `${asset.name}.md`),
      ])
    ),
  };
}

export function getStoredTemplates(): StoredTemplateRecord[] {
  return readStorage<StoredTemplateRecord[]>(CUSTOM_TEMPLATES_STORAGE_KEY, []);
}

export function saveStoredTemplates(records: StoredTemplateRecord[]): void {
  writeStorage(CUSTOM_TEMPLATES_STORAGE_KEY, records);
}

export function getAllTemplateRecords(): StoredTemplateRecord[] {
  return [getDefaultTemplateRecord(), ...getStoredTemplates()];
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

  const blueprintFile = asset.blueprint_file ?? `${asset.name}.md`;
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