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

const BLUEPRINT_PATH_ALIASES: Record<string, string> = {
  rpbotgenerator: 'system/rpbotgenerator.md',
  offspring_generator: 'system/offspring_generator.md',
  system_prompt: 'templates/official_v2v3/assets/system_prompt.md',
  post_history: 'templates/official_v2v3/assets/post_history.md',
  character_sheet: 'templates/official_v2v3/assets/character_sheet.md',
  intro_scene: 'templates/official_v2v3/assets/intro_scene.md',
  intro_page: 'templates/official_v2v3/assets/intro_page.md',
  a1111: 'templates/official_v2v3/assets/a1111.md',
  char_basic_info: 'templates/official_aksho/assets/char_basic_info.md',
  char_physical: 'templates/official_aksho/assets/char_physical.md',
  char_clothing: 'templates/official_aksho/assets/char_clothing.md',
  char_personality: 'templates/official_aksho/assets/char_personality.md',
  char_background: 'templates/official_aksho/assets/char_background.md',
  initial_message: 'templates/official_aksho/assets/initial_message.md',
};

function resolveBlueprintPath(nameOrPath: string): string {
  const normalized = nameOrPath.replace(/^\/+/, '');

  if (normalized.endsWith('.md')) {
    return normalized;
  }

  return BLUEPRINT_PATH_ALIASES[normalized] ?? `${normalized}.md`;
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
  const resolvedPath = resolveBlueprintPath(name);
  const url = `${baseUrl}/${resolvedPath}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Blueprint not found: ${resolvedPath}`);
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
  const systemBlueprints = [
    'rpbotgenerator',
    'offspring_generator',
  ];

  const blueprints: Blueprint[] = [];

  for (const name of systemBlueprints) {
    try {
      const content = await loadBlueprint(name, baseUrl);
      const metadata = parseBlueprintFrontmatter(content);
      const resolvedPath = resolveBlueprintPath(name);

      blueprints.push({
        ...metadata,
        category: 'system',
        content,
        path: `${baseUrl}/${resolvedPath}`,
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
