/**
 * Codeblock parser for blueprint outputs.
 * Extracts and validates assets from LLM-generated content.
 */

// Ordered asset names as they appear in output
export const ASSET_ORDER = [
  'system_prompt',
  'post_history',
  'character_sheet',
  'intro_scene',
  'intro_page',
  'a1111',
  'suno',
] as const;

// Default filename mapping (can be overridden by templates)
export const DEFAULT_ASSET_FILENAMES = {
  system_prompt: 'system_prompt.txt',
  post_history: 'post_history.txt',
  character_sheet: 'character_sheet.txt',
  intro_scene: 'intro_scene.txt',
  intro_page: 'intro_page.md',
  a1111: 'a1111_prompt.txt',
  suno: 'suno_prompt.txt',
} as const;

export type AssetName = typeof ASSET_ORDER[number];

export interface AssetDefinition {
  name: string;
  required: boolean;
  dependsOn: string[];
  description: string;
  blueprintFile?: string;
}

export interface Template {
  name: string;
  version: string;
  description: string;
  assets: AssetDefinition[];
  isOfficial?: boolean;
}

export interface ParseResult {
  assets: Record<string, string>;
  adjustmentNote?: string;
}

export class ParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ParseError';
  }
}

/**
 * Extract all fenced codeblocks from text.
 * Does NOT handle nested codeblocks (acceptable for intended use case).
 */
export function extractCodeblocks(text: string): string[] {
  // Match ```...``` blocks (handles language tags)
  const pattern = /```(?:[a-z]*\n)?(.*?)```/gs;
  const matches = text.match(pattern);
  if (!matches) return [];
  return matches.map(m => m.trim());
}

/**
 * Parse blueprint orchestrator output into assets.
 * @param text - LLM output containing codeblocks
 * @param template - Optional template defining expected assets
 * @returns Dict mapping asset names to content
 * @throws ParseError if output doesn't match expected structure
 */
export function parseBlueprintOutput(text: string, template?: Template): ParseResult {
  const blocks = extractCodeblocks(text);

  if (blocks.length === 0) {
    throw new ParseError('No codeblocks found in output');
  }

  // Check for optional Adjustment Note
  let startIdx = 0;
  let adjustmentNote: string | undefined;

  if (blocks[0].trim().startsWith('Adjustment Note:')) {
    adjustmentNote = blocks[0].trim();
    startIdx = 1;
  }

  const assetBlocks = blocks.slice(startIdx);

  // Determine expected asset order from template or use default
  let expectedAssets: AssetName[] = [];
  if (template && template.assets.length > 0) {
    expectedAssets = template.assets.map(a => a.name as AssetName);
  } else {
    expectedAssets = ASSET_ORDER.slice(0, 6); // Default V2/V3 Card (no suno)
  }

  const expectedCount = expectedAssets.length;

  // Validate asset count
  if (assetBlocks.length !== expectedCount) {
    const blockPreviews = assetBlocks
      .slice(0, 3)
      .map((b, i) => `  Block ${i}: ${b.substring(0, 75)}${b.length > 75 ? '...' : ''}`)
      .join('\n');

    if (assetBlocks.length > 3) {
      blockPreviews += `\n  ... and ${assetBlocks.length - 3} more blocks`;
    }

    throw new ParseError(
      `Expected ${expectedCount} asset blocks, found ${assetBlocks.length}. ` +
      `Template requires order: ${expectedAssets.join(', ')}\n` +
      `Actual blocks found:\n${blockPreviews}`
    );
  }

  // Map blocks to asset names
  const assets: Record<string, string> = {};
  for (let i = 0; i < expectedAssets.length; i++) {
    assets[expectedAssets[i]] = assetBlocks[i];
  }

  // Validate generated content for fatal contract violations
  const contentFailures = validateAssetsContent(assets);
  if (contentFailures && Object.keys(contentFailures).length > 0) {
    const details = Object.entries(contentFailures)
      .map(([asset, issues]) => `${asset}: ${Array.from(new Set(issues)).join(', ')}`)
      .join('; ');
    throw new ParseError('Generated content failed validation checks: ' + details);
  }

  return { assets, adjustmentNote };
}

/**
 * Extract a single asset from LLM output.
 */
export function extractSingleAsset(output: string, assetName: string): string {
  const blocks = extractCodeblocks(output);

  if (!blocks.length) {
    throw new ParseError(`No codeblocks found for ${assetName}`);
  }

  // Check for adjustment note
  let startIdx = 0;
  if (blocks[0].trim().startsWith('Adjustment Note:')) {
    startIdx = 1;
  }

  const assetBlocks = blocks.slice(startIdx);
  if (!assetBlocks.length) {
    throw new ParseError(`No asset block found for ${assetName}`);
  }

  return assetBlocks[0];
}

/**
 * Extract character name from character sheet.
 */
export function extractCharacterName(characterSheet: string): string | null {
  const displayName = extractCharacterDisplayName(characterSheet);
  if (!displayName) return null;
  return sanitizeCharacterName(displayName);
}

/**
 * Extract a human-readable character name from asset content.
 */
export function extractCharacterDisplayName(content: string): string | null {
  const match = content.match(/^name:\s*(.+)$/m);
  if (!match) return null;

  const name = match[1].trim().replace(/^['"]|['"]$/g, '');
  return name || null;
}

/**
 * Sanitize a character name for filesystem-safe identifiers.
 */
export function sanitizeCharacterName(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
}

/**
 * Infer a character's display name from generated asset contents.
 */
export function inferCharacterDisplayNameFromAssets(
  assets: Record<string, string>,
  preferredAssets: Iterable<string> = ['character_sheet', 'char_basic_info']
): string | null {
  const orderedAssetNames: string[] = [];
  const seen = new Set<string>();

  for (const asset of preferredAssets) {
    if (asset in assets && !seen.has(asset)) {
      orderedAssetNames.push(asset);
      seen.add(asset);
    }
  }

  for (const asset of Object.keys(assets)) {
    if (!seen.has(asset)) {
      orderedAssetNames.push(asset);
      seen.add(asset);
    }
  }

  for (const assetName of orderedAssetNames) {
    const displayName = extractCharacterDisplayName(assets[assetName] || '');
    if (displayName) return displayName;
  }

  return null;
}

/**
 * Infer a sanitized filesystem-safe character name from asset contents.
 */
export function inferCharacterNameFromAssets(
  assets: Record<string, string>,
  preferredAssets?: Iterable<string>
): string | null {
  const displayName = inferCharacterDisplayNameFromAssets(assets, preferredAssets);
  if (!displayName) return null;
  return sanitizeCharacterName(displayName);
}

// ============================================================================
// Content Validation
// ============================================================================

const PLACEHOLDER_PATTERNS: Array<[string, RegExp]> = [
  ['{PLACEHOLDER}', /\{PLACEHOLDER\}/g],
  ['Suno {TITLE}', /\{TITLE\}/g],
  [
    'Suno other {..}',
    /\{GENRE\}|\{STYLE\}|\{MOOD\}|\{ENERGY\}|\{TEMPO\}|\{BPM\}|\{TEXTURE\}|\{Remaster Style\}/g,
  ],
  ['A1111 slot ((...))', /\(\(\.\.\.\)\)/g],
  [
    'A1111 any slot ((...something...)) left',
    /\(\([^\)]*\.\.\.[^\)]*\)/g,
  ],
  [
    'Character sheet bracket placeholders',
    /\[(?!\")["'][A-Z][^\]]*\]/g,
  ],
];

const USER_AUTHORITY_PATTERNS: Array<[string, RegExp]> = [
  [
    'Narrates {{user}} action/thought/consent',
    /\{\{user\}\}\s+(?:is|was|feels?|felt|thinks?|thought|decides?|decided|knows?|knew|wants?|wanted|says?|said|nods?|smiles?|walks?|steps?|looks?|touches?|takes?|gives?|allows?|consents?|agrees?|gasps?|moans?)\b/gi,
  ],
  [
    'Narrates {{user}} internal state',
    /\{\{user\}\}'s\s+(?:mind|thoughts?|feelings?|emotions?|desire|consent|decision|reaction|actions?)\b/gi,
  ],
];

const INSTRUCTIONAL_USER_REFERENCE_PATTERN = /(?:never|do not|don't|avoid|without)\s+(?:narrat(?:e|ing)|describ(?:e|ing)|assign(?:ing)?)\s*$/gi;

const CHARACTER_SHEET_FILENAME = 'character_sheet.txt';

/**
 * Return placeholder-related validation issue labels for a file's content.
 */
function detectPlaceholderIssues(text: string, filename: string): string[] {
  const issues: string[] = [];

  for (const [label, pattern] of PLACEHOLDER_PATTERNS) {
    if (label === 'Character sheet bracket placeholders' && filename !== CHARACTER_SHEET_FILENAME) {
      continue;
    }
    if (pattern.test(text)) {
      issues.push(label);
    }
  }

  return issues;
}

/**
 * Return user-authorship issue labels for content that narrates {{user}}.
 */
function detectUserAuthorityIssues(text: string): string[] {
  const issues: string[] = [];

  for (const [label, pattern] of USER_AUTHORITY_PATTERNS) {
    for (const match of text.matchAll(pattern)) {
      const contextBefore = text.substring(Math.max(0, match.index! - 48), match.index!).trim();
      if (!INSTRUCTIONAL_USER_REFERENCE_PATTERN.test(contextBefore)) {
        issues.push(label);
        break;
      }
    }
  }

  return issues;
}

/**
 * Validate a generated asset's content and return issue labels.
 */
export function validateAssetContent(assetName: string, content: string): string[] {
  let filename = `${assetName}.txt`;
  if (assetName === 'intro_page') filename = 'intro_page.md';
  if (assetName === 'character_sheet') filename = CHARACTER_SHEET_FILENAME;

  const issues = detectPlaceholderIssues(content, filename);
  issues.push(...detectUserAuthorityIssues(content));
  return issues;
}

/**
 * Validate all generated assets and return {asset_name: issues} for failures.
 */
export function validateAssetsContent(assets: Record<string, string>): Record<string, string[]> | null {
  const failures: Record<string, string[]> = {};
  for (const [assetName, content] of Object.entries(assets)) {
    const issues = validateAssetContent(assetName, content);
    if (issues.length > 0) {
      failures[assetName] = issues;
    }
  }
  return Object.keys(failures).length > 0 ? failures : null;
}
