/**
 * Prompt Builder
 * Builds LLM prompts for character generation, similarity, etc.
 */

import type {
  ChatMessage,
  ContentMode,
} from '@char-gen/shared';
import { buildSeedGeneratorSystemPrompt } from '../seed-generator.js';
import type {
  TemplateAsset,
} from './blueprint.js';
import {
  loadBlueprint,
  topologicalSort,
} from './blueprint.js';

/**
 * Build orchestrator prompt for character generation
 */
export async function buildOrchestratorPrompt(
  seed: string,
  mode: ContentMode | null = null,
  templateAssets?: TemplateAsset[],
  baseUrl?: string
): Promise<[system: string, user: string]> {
  // Load orchestrator blueprint
  let orchestrator = await loadBlueprint('rpbotgenerator', baseUrl);

  // If template provided, modify orchestrator to list custom assets
  if (templateAssets && templateAssets.length > 0) {
    try {
      const assetOrder = topologicalSort(templateAssets);
      const assetList = assetOrder.join(', ');

      let templateOverride = `\n\n## TEMPLATE OVERRIDE\n\nUsing custom template with ${templateAssets.length} assets\n`;
      templateOverride += `Generate these assets in order: ${assetList}\n`;
      templateOverride += 'Follow dependency order defined in template.\n';

      orchestrator = orchestrator + templateOverride;
    } catch {
      // Use unsorted list if topological sort fails
      const assetList = templateAssets.map(a => a.name).join(', ');
      orchestrator += `\n\n## TEMPLATE OVERRIDE\n\nGenerate these assets: ${assetList}\n`;
    }
  }

  const systemPrompt = orchestrator;

  const userLines: string[] = [];
  if (mode) {
    userLines.push(`Mode: ${mode}`);
  }
  userLines.push(`SEED: ${seed}`);

  return [systemPrompt, userLines.join('\n')];
}

/**
 * Build asset prompt for single asset generation
 */
export async function buildAssetPrompt(
  assetName: string,
  seed: string,
  mode: ContentMode | null = null,
  priorAssets: Record<string, string> = {},
  blueprintContent: string | null = null,
  baseUrl?: string
): Promise<[system: string, user: string]> {
  // Load blueprint content
  const blueprint = blueprintContent || await loadBlueprint(assetName, baseUrl);

  const systemPrompt = `# BLUEPRINT: ${assetName}\n\n${blueprint}`;

  const userLines: string[] = [];
  if (mode) {
    userLines.push(`Mode: ${mode}`);
  }
  userLines.push(`SEED: ${seed}`);

  // Add prior assets as context
  if (priorAssets && Object.keys(priorAssets).length > 0) {
    userLines.push('\n---\n## Prior Assets (for context):\n');
    for (const [priorName, priorContent] of Object.entries(priorAssets)) {
      userLines.push(`### ${priorName}:\n\`\`\`\n${priorContent}\n\`\`\`\n`);
    }
  }

  return [systemPrompt, userLines.join('\n')];
}

/**
 * Build seed generation prompt
 */
export async function buildSeedGenPrompt(
  genreLines: string
): Promise<[system: string, user: string]> {
  const systemPrompt = buildSeedGeneratorSystemPrompt();

  return [systemPrompt, genreLines];
}

/**
 * Build similarity analysis prompt
 */
export function buildSimilarityPrompt(
  profile1: {
    name?: string;
    age?: number;
    gender?: string;
    species?: string;
    occupation?: string;
    role?: string;
    power_level?: string;
    mode?: string;
    personality_traits?: string[];
    core_values?: string[];
    motivations?: string[];
    goals?: string[];
    fears?: string[];
  },
  profile2: {
    name?: string;
    age?: number;
    gender?: string;
    species?: string;
    occupation?: string;
    role?: string;
    power_level?: string;
    mode?: string;
    personality_traits?: string[];
    core_values?: string[];
    motivations?: string[];
    goals?: string[];
    fears?: string[];
  }
): [system: string, user: string] {
  const systemPrompt = `You are an expert character analyst specializing in understanding character relationships, dynamics, and narrative potential. Your task is to deeply analyze two characters and provide insights about how they would interact in a story.

You will receive structured character profiles containing:
- Basic information (name, age, gender, species, occupation)
- Personality traits
- Core values and beliefs
- Motivations and goals
- Fears and weaknesses
- Narrative role and power level

Your analysis should focus on:

1. **Narrative Dynamics**: How these characters would interact, tension or harmony between them, and what makes their relationship interesting for readers.

2. **Story Opportunities**: Specific plot hooks, conflicts, or situations that would arise from their relationship.

3. **Scene Suggestions**: 2-3 specific scene ideas that would showcase their dynamic (setting, situation, what happens).

4. **Dialogue Style**: How they would talk to each other - conversational patterns, tone, verbal conflicts, etc.

5. **Relationship Arc**: How their relationship might evolve over a story - beginning, middle, and end states.

Provide your response as JSON with this structure:

${'```'}json
{
  "narrative_dynamics": "2-3 paragraphs describing core dynamic",
  "story_opportunities": [
    "opportunity 1",
    "opportunity 2",
    "opportunity 3"
  ],
  "scene_suggestions": [
    "Scene 1 description with setting and action",
    "Scene 2 description with setting and action",
    "Scene 3 description with setting and action"
  ],
  "dialogue_style": "Description of their conversational patterns",
  "relationship_arc": "Description of how their relationship would develop"
}
${'```'}

Be specific, insightful, and focus on narrative potential. Consider:
- Would they clash or complement each other?
- What secrets or conflicts could emerge?
- How would they challenge each other to grow?
- What would readers find compelling about their relationship?
- What themes or conflicts would their relationship explore?`;

  const userLines: string[] = [];

  // Character 1
  userLines.push(`## CHARACTER 1: ${profile1.name || 'Character 1'}`);
  userLines.push(`**Age**: ${profile1.age || 'Unknown'}`);
  userLines.push(`**Gender**: ${profile1.gender || 'Unknown'}`);
  userLines.push(`**Species**: ${profile1.species || 'Unknown'}`);
  userLines.push(`**Occupation**: ${profile1.occupation || 'Unknown'}`);
  userLines.push(`**Role**: ${profile1.role || 'Unknown'}`);
  userLines.push(`**Power Level**: ${profile1.power_level || 'Unknown'}`);
  userLines.push(`**Mode**: ${profile1.mode || 'Unknown'}`);

  if (profile1.personality_traits && profile1.personality_traits.length > 0) {
    userLines.push(`**Personality Traits**: ${profile1.personality_traits.slice(0, 10).join(', ')}`);
  }
  if (profile1.core_values && profile1.core_values.length > 0) {
    userLines.push(`**Core Values**: ${profile1.core_values.slice(0, 10).join(', ')}`);
  }
  if (profile1.motivations && profile1.motivations.length > 0) {
    userLines.push(`**Motivations**: ${profile1.motivations.slice(0, 10).join(', ')}`);
  }
  if (profile1.goals && profile1.goals.length > 0) {
    userLines.push(`**Goals**: ${profile1.goals.slice(0, 10).join(', ')}`);
  }
  if (profile1.fears && profile1.fears.length > 0) {
    userLines.push(`**Fears**: ${profile1.fears.slice(0, 10).join(', ')}`);
  }

  // Character 2
  userLines.push(`\n## CHARACTER 2: ${profile2.name || 'Character 2'}`);
  userLines.push(`**Age**: ${profile2.age || 'Unknown'}`);
  userLines.push(`**Gender**: ${profile2.gender || 'Unknown'}`);
  userLines.push(`**Species**: ${profile2.species || 'Unknown'}`);
  userLines.push(`**Occupation**: ${profile2.occupation || 'Unknown'}`);
  userLines.push(`**Role**: ${profile2.role || 'Unknown'}`);
  userLines.push(`**Power Level**: ${profile2.power_level || 'Unknown'}`);
  userLines.push(`**Mode**: ${profile2.mode || 'Unknown'}`);

  if (profile2.personality_traits && profile2.personality_traits.length > 0) {
    userLines.push(`**Personality Traits**: ${profile2.personality_traits.slice(0, 10).join(', ')}`);
  }
  if (profile2.core_values && profile2.core_values.length > 0) {
    userLines.push(`**Core Values**: ${profile2.core_values.slice(0, 10).join(', ')}`);
  }
  if (profile2.motivations && profile2.motivations.length > 0) {
    userLines.push(`**Motivations**: ${profile2.motivations.slice(0, 10).join(', ')}`);
  }
  if (profile2.goals && profile2.goals.length > 0) {
    userLines.push(`**Goals**: ${profile2.goals.slice(0, 10).join(', ')}`);
  }
  if (profile2.fears && profile2.fears.length > 0) {
    userLines.push(`**Fears**: ${profile2.fears.slice(0, 10).join(', ')}`);
  }

  userLines.push('\n## TASK');
  userLines.push('Provide a deep analysis of these two characters\' relationship potential.');
  userLines.push('Return your response as valid JSON following the structure specified in the system prompt.');

  return [systemPrompt, userLines.join('\n')];
}

/**
 * Build offspring generation prompt
 */
export async function buildOffspringPrompt(
  parent1Assets: Record<string, string>,
  parent2Assets: Record<string, string>,
  parent1Name: string,
  parent2Name: string,
  mode: ContentMode | null = null,
  baseUrl?: string
): Promise<[system: string, user: string]> {
  // Load offspring generator blueprint
  const systemPrompt = await loadBlueprint('offspring_generator', baseUrl);

  const userLines: string[] = [];

  if (mode) {
    userLines.push(`Mode: ${mode}`);
  }

  // Add parent 1's assets
  userLines.push(`\n## PARENT 1: ${parent1Name}`);
  userLines.push('### System Prompt:\n```');
  userLines.push(parent1Assets.system_prompt || '');
  userLines.push('```');
  userLines.push('### Post History:\n```');
  userLines.push(parent1Assets.post_history || '');
  userLines.push('```');
  userLines.push('### Character Sheet:\n```');
  userLines.push(parent1Assets.character_sheet || '');
  userLines.push('```');
  userLines.push('### Intro Scene:\n```');
  userLines.push(parent1Assets.intro_scene || '');
  userLines.push('```');

  // Add parent 2's assets
  userLines.push(`\n## PARENT 2: ${parent2Name}`);
  userLines.push('### System Prompt:\n```');
  userLines.push(parent2Assets.system_prompt || '');
  userLines.push('```');
  userLines.push('### Post History:\n```');
  userLines.push(parent2Assets.post_history || '');
  userLines.push('```');
  userLines.push('### Character Sheet:\n```');
  userLines.push(parent2Assets.character_sheet || '');
  userLines.push('```');
  userLines.push('### Intro Scene:\n```');
  userLines.push(parent2Assets.intro_scene || '');
  userLines.push('```');

  // Instruction
  userLines.push('\n## INSTRUCTION:');
  userLines.push('Analyze how these two parents would shape a new character\'s upbringing and generate the offspring\'s SEED.');

  return [systemPrompt, userLines.join('\n')];
}

/**
 * Build refinement chat system prompt
 */
export async function buildRefinementSystemPrompt(
  assetName: string,
  currentContent: string,
  characterSheet: string,
  baseUrl?: string
): Promise<string> {
  // Asset labels for friendly names
  const assetLabels: Record<string, string> = {
    system_prompt: 'System Prompt',
    post_history: 'Post History',
    character_sheet: 'Character Sheet',
    intro_scene: 'Intro Scene',
    intro_page: 'Intro Page',
    a1111: 'A1111 Image Prompt',
    suno: 'Suno Music Prompt',
  };

  const label = assetLabels[assetName] || assetName;

  // Load blueprint for this asset
  let blueprint: string;
  try {
    blueprint = await loadBlueprint(assetName, baseUrl);
  } catch {
    blueprint = '(Blueprint not found)';
  }

  const prompt = `You are an expert assistant helping refine a character asset: **${label}**.

The user is working on an Eidolon Simulacra project using the blueprint system. You have access to:
1. The blueprint specification for this asset
2. The current asset content
3. The character sheet (for maintaining consistency)

## Blueprint Specification for ${label}:

\`\`\`markdown
${blueprint}
\`\`\`

## Current Asset: ${label}

\`\`\`
${currentContent}
\`\`\`

## Character Sheet (for context):

\`\`\`
${characterSheet}
\`\`\`

## Your Role:

- **Discuss**: Answer questions about the asset, explain choices, suggest improvements
- **Refine**: When requested, provide an edited version of the asset
- **Maintain Consistency**: Ensure edits align with the character sheet and blueprint requirements
- **Follow Blueprint**: Strictly adhere to the format, rules, and constraints specified in the blueprint above
- **Format**: When providing an edited version, output it in a single code block (\`\`\`)

## Key Guidelines:

- **Never narrate {{user}} actions, thoughts, emotions, sensations, decisions, or consent**
- Preserve the asset's required format and structure exactly as specified in the blueprint
- Keep tone and voice consistent with the character's established personality
- Respect all "Hard Rules" and constraints from the blueprint
- Maintain token limits where specified
- For system_prompt and post_history: paragraph-only, ≤300 tokens, no headers/lists
- For character_sheet: maintain field order and structure exactly
- For intro_scene: second-person narrative, end with open loop
- For a1111/suno: follow the modular prompt format exactly (including [Control] blocks)

If the user asks for changes, provide the complete edited asset in a code block. Otherwise, discuss and advise.`;

  return prompt;
}

/**
 * Format messages for LLM API
 */
export function formatMessages(
  systemPrompt: string,
  userPrompt: string,
  conversationHistory?: ChatMessage[]
): ChatMessage[] {
  const messages: ChatMessage[] = [
    { role: 'system', content: systemPrompt },
  ];

  if (conversationHistory && conversationHistory.length > 0) {
    messages.push(...conversationHistory);
  }

  messages.push({ role: 'user', content: userPrompt });

  return messages;
}
