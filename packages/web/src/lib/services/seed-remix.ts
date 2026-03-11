export interface SeedRemixInput {
  seeds: string[];
  tone?: string;
  genre?: string;
}

export interface SeedRemixPreview {
  title: string;
  combinedSeed: string;
}

export function buildSeedRemixPreview(input: SeedRemixInput): SeedRemixPreview {
  const cleanedSeeds = input.seeds.map((seed) => seed.trim()).filter(Boolean);
  return {
    title: input.genre ? `${input.genre} remix` : 'seed remix preview',
    combinedSeed: cleanedSeeds.join(' | '),
  };
}