export interface GenerationScenarioDefinition {
  id: string;
  label: string;
  description: string;
  owner: 'generation';
}

export const generationScenarioDefinitions: GenerationScenarioDefinition[] = [
  {
    id: 'fast-draft',
    label: 'Fast Draft',
    description: 'Placeholder scenario for low-friction generation presets.',
    owner: 'generation',
  },
  {
    id: 'high-structure',
    label: 'High Structure',
    description: 'Placeholder scenario for stricter prompt and review constraints.',
    owner: 'generation',
  },
  {
    id: 'art-focused',
    label: 'Art Focused',
    description: 'Placeholder scenario for image-forward generation workflows.',
    owner: 'generation',
  },
];

export function getGenerationScenarioDefinitions(): GenerationScenarioDefinition[] {
  return generationScenarioDefinitions;
}