/**
 * Export preset management for Character Generator.
 * Handles loading TOML presets and applying them to character assets.
 */

export interface FieldMapping {
  asset: string;
  target: string;
  wrapper?: string;
  optional?: boolean;
}

export interface ExportPreset {
  name: string;
  format: 'text' | 'json' | 'combined';
  description: string;
  fields: FieldMapping[];
  metadata: Record<string, unknown>;
  outputPattern: string;
}

export type ExportFormat = ExportPreset['format'];

/**
 * Parse a simple TOML-like value
 */
function parseTOMLValue(value: string): string | number | boolean {
  const trimmed = value.trim();

  // Boolean
  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;

  // Number
  const num = Number(trimmed);
  if (!isNaN(num) && trimmed === String(num)) return num;

  // String (remove quotes)
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
      (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }

  return trimmed;
}

/**
 * Parse a simple TOML file
 * Note: This is a minimal parser for the preset format, not a full TOML implementation
 */
export function parsePreset(toml: string): ExportPreset | null {
  try {
    const result: Record<string, any> = {};
    const currentSection: { [key: string]: any } = {};
    let currentField: FieldMapping | null = null;
    const fields: FieldMapping[] = [];

    const lines = toml.split('\n');
    let inPreset = false;
    let inFields = false;
    let inOutput = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Skip comments and empty lines
      if (line.startsWith('#') || line === '') continue;

      // Section headers
      if (line.startsWith('[') && line.endsWith(']')) {
        const section = line.slice(1, -1);
        if (section === 'preset') {
          inPreset = true;
          inFields = false;
          inOutput = false;
        } else if (section === 'fields') {
          inPreset = false;
          inFields = true;
          inOutput = false;
        } else if (section === 'output') {
          inPreset = false;
          inFields = false;
          inOutput = true;
        }
        continue;
      }

      // Key-value pairs
      const match = line.match(/^(\w+)\s*=\s*(.+)$/);
      if (!match) continue;

      const [, key, rawValue] = match;
      const value = parseTOMLValue(rawValue);

      if (inPreset) {
        currentSection[key] = value;
      } else if (inOutput) {
        currentSection[key] = value;
      } else if (inFields && currentField) {
        if (key === 'asset') {
          currentField.asset = String(value);
        } else if (key === 'target') {
          currentField.target = String(value);
        } else if (key === 'wrapper') {
          currentField.wrapper = String(value);
        } else if (key === 'optional') {
          currentField.optional = Boolean(value);
        }
      }

      // Array item marker for fields (double brackets [[field]])
      if (line.startsWith('[[') && line.endsWith(']]')) {
        if (currentField) {
          fields.push(currentField);
        }
        currentField = { asset: '', target: '' };
      }
    }

    // Add last field
    if (currentField) {
      fields.push(currentField);
    }

    // Build preset
    return {
      name: currentSection.name || 'Unknown',
      format: (currentSection.format as ExportFormat) || 'text',
      description: currentSection.description || '',
      fields,
      metadata: {},
      outputPattern: currentSection.filename || currentSection.directory || '{{character_name}}',
    };
  } catch {
    return null;
  }
}

/**
 * Apply an export preset to a set of assets.
 */
export function applyPreset(
  assets: Record<string, string>,
  preset: ExportPreset,
  characterName: string = ''
): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  // Apply metadata
  Object.assign(result, preset.metadata);

  // Extract character name from character_sheet if not provided
  if (!characterName && assets.character_sheet) {
    const lines = assets.character_sheet.split('\n').slice(0, 20);
    for (const line of lines) {
      if (line.trim().toLowerCase().startsWith('name:')) {
        characterName = line.split(':', 2)[1].trim();
        break;
      }
    }
  }

  // Apply field mappings
  for (const mapping of preset.fields) {
    if (!(mapping.asset in assets)) continue;

    let content = assets[mapping.asset];

    // Skip if optional and missing
    if (!content && mapping.optional) continue;

    // Apply wrapper if specified
    if (mapping.wrapper) {
      content = mapping.wrapper
        .replace(/\{\{content\}\}/g, content)
        .replace(/\{\{char\}\}/g, characterName || '{{char}}')
        .replace(/\{\{user\}\}/g, '{{user}}');
    }

    result[mapping.target] = content;
  }

  // Add character name if not already present
  if (!('name' in result) && characterName) {
    result.name = characterName;
  }

  return result;
}

/**
 * Format export data according to preset format.
 */
export function formatExport(
  data: Record<string, unknown>,
  preset: ExportPreset,
  characterName: string = '',
  model: string = ''
): { filename: string; content: string } | { directory: string; files: Array<{ filename: string; content: string }> } {
  // Apply template variables to output pattern
  let outputName = preset.outputPattern
    .replace(/\{\{character_name\}\}/g, characterName || 'character')
    .replace(/\{\{model\}\}/g, model || 'unknown')
    .replace(/\{\{timestamp\}\}/g, '');

  // Remove any double separators
  outputName = outputName.replace(/\(\)/g, '').replace(/__/g, '_');

  if (preset.format === 'text') {
    // Create directory with separate text files
    const files: Array<{ filename: string; content: string }> = [];

    for (const [key, value] of Object.entries(data)) {
      let filename = key;
      // Determine file extension
      if (key.includes('.')) {
        // Key already has an extension
        filename = key;
      } else if (key === 'intro_page' || key.includes('page')) {
        filename = `${key}.md`;
      } else {
        filename = `${key}.txt`;
      }
      files.push({ filename, content: String(value) });
    }

    return { directory: outputName, files };
  } else if (preset.format === 'json') {
    // Create single JSON file
    if (!outputName.endsWith('.json')) {
      outputName += '.json';
    }
    return { filename: outputName, content: JSON.stringify(data, null, 2) };
  } else if (preset.format === 'combined') {
    // Create single combined text file
    if (!outputName.endsWith('.txt')) {
      outputName += '.txt';
    }
    const lines: string[] = [];
    for (const [key, value] of Object.entries(data)) {
      lines.push(`=== ${key.toUpperCase()} ===`);
      lines.push('');
      lines.push(String(value));
      lines.push('');
      lines.push('');
    }
    return { filename: outputName, content: lines.join('\n') };
  }

  throw new Error(`Unknown preset format: ${preset.format}`);
}

/**
 * Validate a preset for completeness and correctness.
 */
export function validatePreset(preset: ExportPreset): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!preset.name) {
    errors.push('Preset name is required');
  }

  if (!['text', 'json', 'combined'].includes(preset.format)) {
    errors.push(`Invalid format: ${preset.format}`);
  }

  if (!preset.fields.length) {
    errors.push('Preset must have at least one field mapping');
  }

  const validAssets = new Set([
    'system_prompt', 'post_history', 'character_sheet',
    'intro_scene', 'intro_page', 'a1111', 'suno',
  ]);

  for (const mapping of preset.fields) {
    if (!mapping.asset) {
      errors.push('Field mapping missing asset name');
    } else if (!validAssets.has(mapping.asset)) {
      errors.push(`Invalid asset name: ${mapping.asset}`);
    }

    if (!mapping.target) {
      errors.push(`Field mapping for ${mapping.asset} missing target`);
    }
  }

  return { isValid: errors.length === 0, errors };
}
