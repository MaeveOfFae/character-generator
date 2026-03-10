/**
 * Template system for custom asset types.
 */

import type { AssetDefinition as BaseAssetDefinition } from '../types';

export interface AssetDefinition extends BaseAssetDefinition {
  dependsOn: string[];
  blueprintFile?: string;
}

export interface Template {
  name: string;
  version: string;
  description: string;
  assets: AssetDefinition[];
  isOfficial?: boolean;
  path?: string;
}

/**
 * Official V2/V3 Card template
 */
export const OFFICIAL_TEMPLATE: Template = {
  name: 'V2/V3 Card',
  version: '3.1',
  description: 'Official character card template with 6 standard assets',
  isOfficial: true,
  assets: [
    {
      name: 'system_prompt',
      required: true,
      dependsOn: [],
      description: 'System-level behavioral instructions',
      blueprintFile: 'system_prompt.md',
    },
    {
      name: 'post_history',
      required: true,
      dependsOn: ['system_prompt'],
      description: 'Conversation context and relationship state',
      blueprintFile: 'post_history.txt',
    },
    {
      name: 'character_sheet',
      required: true,
      dependsOn: ['system_prompt', 'post_history'],
      description: 'Structured character data',
      blueprintFile: 'character_sheet.txt',
    },
    {
      name: 'intro_scene',
      required: true,
      dependsOn: ['system_prompt', 'post_history', 'character_sheet'],
      description: 'First interaction scenario',
      blueprintFile: 'intro_scene.txt',
    },
    {
      name: 'intro_page',
      required: true,
      dependsOn: ['character_sheet'],
      description: 'Visual character introduction page',
      blueprintFile: 'intro_page.md',
    },
    {
      name: 'a1111',
      required: true,
      dependsOn: ['character_sheet'],
      description: 'Stable Diffusion image generation prompt',
      blueprintFile: 'a1111.txt',
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
      for (const dep of asset.dependsOn) {
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
  for (const asset of template.assets) {
    const visited = new Set<string>();
    function checkDeps(deps: string[]): boolean {
      for (const dep of deps) {
        if (dep === asset.name) {
          return true; // Circular!
        }
        if (visited.has(dep)) continue;
        visited.add(dep);
        const depAsset = assetMap.get(dep);
        if (depAsset && checkDeps(depAsset.dependsOn)) {
          return true;
        }
      }
      return false;
    }

    if (checkDeps(asset.dependsOn)) {
      errors.push(`Circular dependency detected for asset: ${asset.name}`);
    }
  }

  return { isValid: errors.length === 0, errors };
}
