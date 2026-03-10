/**
 * Template system for custom asset types.
 */

import type { AssetDefinition as TypesAssetDefinition, Template as TypesTemplate } from '../types';

// Re-export types from types/index with local type names to avoid conflicts
export type AssetDefinition = TypesAssetDefinition;
export type Template = TypesTemplate;

/**
 * Official V2/V3 Card template
 */
export const OFFICIAL_TEMPLATE: Template = {
  name: 'V2/V3 Card',
  version: '3.1',
  description: 'Official character card template with 6 standard assets',
  is_official: true,
  assets: [
    {
      name: 'system_prompt',
      required: true,
      depends_on: [],
      description: 'System-level behavioral instructions',
      blueprint_file: 'system_prompt.md',
    },
    {
      name: 'post_history',
      required: true,
      depends_on: ['system_prompt'],
      description: 'Conversation context and relationship state',
      blueprint_file: 'post_history.txt',
    },
    {
      name: 'character_sheet',
      required: true,
      depends_on: ['system_prompt', 'post_history'],
      description: 'Structured character data',
      blueprint_file: 'character_sheet.txt',
    },
    {
      name: 'intro_scene',
      required: true,
      depends_on: ['system_prompt', 'post_history', 'character_sheet'],
      description: 'First interaction scenario',
      blueprint_file: 'intro_scene.txt',
    },
    {
      name: 'intro_page',
      required: true,
      depends_on: ['character_sheet'],
      description: 'Visual character introduction page',
      blueprint_file: 'intro_page.md',
    },
    {
      name: 'a1111',
      required: true,
      depends_on: ['character_sheet'],
      description: 'Stable Diffusion image generation prompt',
      blueprint_file: 'a1111.txt',
    },
  ],
};

/**
 * Default asset order (for parsing LLM output)
 */
export const DEFAULT_ASSET_ORDER = [
  'system_prompt',
  'post_history',
  'character_sheet',
  'intro_scene',
  'intro_page',
  'a1111',
] as const;

/**
 * Topological sort for assets based on dependencies.
 * Ensures assets are processed in the correct order.
 */
export function topologicalSort(assets: AssetDefinition[]): string[] {
  const assetNames = assets.map(a => a.name);
  const resolved: string[] = [];
  const resolvedSet = new Set<string>();
  const visiting = new Set<string>();

  function visit(assetName: string): void {
    if (resolvedSet.has(assetName)) return;
    if (visiting.has(assetName)) {
      // Circular dependency detected, break
      return;
    }

    visiting.add(assetName);

    const asset = assets.find(a => a.name === assetName);
    if (asset) {
      for (const dep of asset.depends_on) {
        visit(dep);
      }
    }

    resolvedSet.add(assetName);
    resolved.push(assetName);
    visiting.delete(assetName);
  }

  for (const assetName of assetNames) {
    if (!resolvedSet.has(assetName)) {
      visit(assetName);
    }
  }

  return resolved;
}

/**
 * Get assets in topological order for a template.
 */
export function getOrderedAssets(template?: Template): AssetDefinition[] {
  const targetTemplate = template || OFFICIAL_TEMPLATE;
  const orderedNames = topologicalSort(targetTemplate.assets);
  return orderedNames
    .map(name => targetTemplate.assets.find(a => a.name === name))
    .filter((a): a is AssetDefinition => a !== undefined);
}

/**
 * Validate a template for correctness.
 */
export function validateTemplate(template: Template): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!template.name) {
    errors.push('Template name is required');
  }

  if (!template.assets || template.assets.length === 0) {
    errors.push('Template must have at least one asset');
  }

  // Check for circular dependencies
  const assetMap = new Map(template.assets.map(a => [a.name, a]));
  function checkDeps(deps: string[], currentAssetName: string): boolean {
    for (const dep of deps) {
      if (dep === currentAssetName) {
        return true; // Circular!
      }
      const depAsset = assetMap.get(dep);
      if (depAsset && checkDeps(depAsset.depends_on, currentAssetName)) {
        return true;
      }
    }
    return false;
  }

  for (const asset of template.assets) {
    if (checkDeps(asset.depends_on, asset.name)) {
      errors.push(`Circular dependency detected for asset: ${asset.name}`);
    }
  }

  return { isValid: errors.length === 0, errors };
}
