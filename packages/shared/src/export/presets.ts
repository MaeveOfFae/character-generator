/**
 * Export preset management for Character Generator.
 * Handles loading TOML presets and applying them to character assets.
 */

import type {
  FieldMapping,
  ExportPreset as TypesExportPreset,
  ExportFormat,
} from '../types';

/**
 * Apply an export preset to a set of assets.
 */
export function applyPreset(
  assets: Record<string, string>,
  preset: TypesExportPreset,
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
  preset: TypesExportPreset,
  characterName: string = '',
  model: string = ''
): { filename: string; content: string } | { directory: string; files: Array<{ filename: string; content: string }> } {
  // Apply template variables to output pattern
  let outputName = preset.output_pattern
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
export function validatePreset(preset: TypesExportPreset): { isValid: boolean; errors: string[] } {
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
    }
    if (!validAssets.has(mapping.asset)) {
      errors.push(`Invalid asset name: ${mapping.asset}`);
    }
    if (!mapping.target) {
      errors.push(`Field mapping for ${mapping.asset} missing target`);
    }
  }

  return { isValid: errors.length === 0, errors };
}
