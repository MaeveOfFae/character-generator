/**
 * Blueprint Loader and Parser
 * Client-side blueprint loading from static resources
 */

import type {
  Template,
  DraftMetadata,
  ContentMode,
} from '@char-gen/shared';

export interface Blueprint {
  name: string;
  description: string;
  invokable: boolean;
  version: string;
  category: 'core' | 'system' | 'template' | 'example';
  content: string;
  path: string;
}

/**
 * Blueprint repository URL
 * Can be configured to point to a CDN or local folder
 */
const BLUEPRINT_REPO_URL = '/blueprints';

/**
 * Load a blueprint from the repository
 */
export async function loadBlueprint(name: string, baseUrl: string = BLUEPRINT_REPO_URL): Promise<string> {
  const url = `${baseUrl}/${name}.md`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Blueprint not found: ${name}`);
    }
    return await response.text();
  } catch (error) {
    throw new Error(`Failed to load blueprint '${name}': ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Parse blueprint metadata from frontmatter
 */
export function parseBlueprintFrontmatter(content: string): {
  name: string;
  description: string;
  invokable: boolean;
  version: string;
} {
  // Look for YAML frontmatter between --- markers
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);

  if (!frontmatterMatch) {
    const headingMatch = content.match(/^#\s+(.+)$/m);
    const paragraphMatch = content
      .split('\n')
      .map((line) => line.trim())
      .find((line) => line.length > 0 && !line.startsWith('#') && !line.startsWith('```'));

    return {
      name: headingMatch?.[1]?.trim() || 'Untitled Blueprint',
      description: paragraphMatch || 'No description',
      invokable: false,
      version: '1.0',
    };
  }

  const frontmatter = frontmatterMatch[1];
  const metadata: Record<string, unknown> = {};

  // Simple YAML parser (enough for our needs)
  const lines = frontmatter.split('\n');
  for (const line of lines) {
    const match = line.match(/^(\w+):\s*(.+)$/);
    if (match) {
      const [, key, value] = match;
      // Handle boolean values
      if (value.toLowerCase() === 'true') {
        metadata[key] = true;
      } else if (value.toLowerCase() === 'false') {
        metadata[key] = false;
      } else {
        // Remove quotes if present
        metadata[key] = value.replace(/^['"]|['"]$/g, '');
      }
    }
  }

  return {
    name: String(metadata.name || 'unknown'),
    description: String(metadata.description || ''),
    invokable: Boolean(metadata.invokable),
    version: String(metadata.version || '1.0'),
  };
}

/**
 * Get all available blueprints
 */
export async function listBlueprints(baseUrl: string = BLUEPRINT_REPO_URL): Promise<Blueprint[]> {
  // In production, this would be a static list or fetched from an index
  // For now, return the core orchestrator blueprint
  const coreBlueprints = [
    'rpbotgenerator',
    'offspring_generator',
  ];

  const blueprints: Blueprint[] = [];

  for (const name of coreBlueprints) {
    try {
      const content = await loadBlueprint(name, baseUrl);
      const metadata = parseBlueprintFrontmatter(content);

      blueprints.push({
        ...metadata,
        category: 'core',
        content,
        path: `${baseUrl}/${name}.md`,
      });
    } catch {
      // Skip failed blueprints
    }
  }

  return blueprints;
}

/**
 * Template asset definitions from template
 */
export interface TemplateAsset {
  name: string;
  required: boolean;
  dependsOn: string[];
  description: string;
  blueprintFile?: string;
}

/**
 * Convert Template object to asset list
 */
export function templateToAssets(template: Template): TemplateAsset[] {
  return template.assets.map(asset => ({
    name: asset.name,
    required: asset.required,
    dependsOn: asset.depends_on,
    description: asset.description,
    blueprintFile: asset.blueprint_file,
  }));
}

/**
 * Topological sort of assets based on dependencies
 */
export function topologicalSort(assets: TemplateAsset[]): string[] {
  const visited = new Set<string>();
  const visiting = new Set<string>();
  const result: string[] = [];

  const visit = (assetName: string) => {
    if (visited.has(assetName)) {
      return;
    }
    if (visiting.has(assetName)) {
      throw new Error(`Circular dependency detected involving ${assetName}`);
    }

    visiting.add(assetName);

    const asset = assets.find(a => a.name === assetName);
    if (asset) {
      for (const dep of asset.dependsOn) {
        visit(dep);
      }
    }

    visiting.delete(assetName);
    visited.add(assetName);
    result.push(assetName);
  };

  for (const asset of assets) {
    visit(asset.name);
  }

  return result;
}
