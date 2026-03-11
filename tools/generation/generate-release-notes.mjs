import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import fs from 'node:fs/promises';
import { execFile } from 'node:child_process';
import path from 'node:path';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '../..');
const rootPackageJsonPath = path.join(repoRoot, 'package.json');
const webPackageJsonPath = path.join(repoRoot, 'packages/web/package.json');
const releaseNotesPath = path.join(repoRoot, 'packages/web/src/lib/whats-new.ts');
const changelogPath = path.join(repoRoot, 'CHANGELOG.md');
const execFileAsync = promisify(execFile);

const CATEGORY_RULES = [
  { id: 'theme', label: 'theme', pluralLabel: 'themes', keywords: ['theme', 'themes', 'palette', 'color'] },
  { id: 'docs', label: 'documentation', pluralLabel: 'documentation', keywords: ['readme', 'security', 'license', 'terms', 'privacy', 'conduct', 'docs', 'documentation'] },
  { id: 'ui', label: 'UI', pluralLabel: 'UI', keywords: ['home', 'layout', 'page', 'pages', 'widget', 'button', 'sidebar', 'screen'] },
  { id: 'template', label: 'template', pluralLabel: 'templates', keywords: ['template', 'blueprint', 'export', 'preset'] },
  { id: 'runtime', label: 'runtime', pluralLabel: 'runtime', keywords: ['api', 'provider', 'openrouter', 'llm', 'storage', 'fetch', 'router', 'build'] },
];

function parseArgs(argv) {
  const options = {
    highlights: [],
    links: [],
    dryRun: false,
    deriveFromCommits: false,
    bump: 'patch',
    allowDirty: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];

    if (!token.startsWith('--')) {
      continue;
    }

    const [flag, inlineValue] = token.split('=', 2);
    const value = inlineValue ?? argv[index + 1];

    switch (flag) {
      case '--version':
        options.version = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--bump':
        options.bump = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--date':
        options.date = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--badge':
        options.badge = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--headline':
        options.headline = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--summary':
        options.summary = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--highlights':
        options.highlights.push(...splitPipeList(value));
        if (inlineValue === undefined) index += 1;
        break;
      case '--links':
        options.links.push(...splitPipeList(value));
        if (inlineValue === undefined) index += 1;
        break;
      case '--from-ref':
        options.fromRef = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--to-ref':
        options.toRef = value;
        if (inlineValue === undefined) index += 1;
        break;
      case '--commits':
        options.commits = Number.parseInt(value, 10);
        if (inlineValue === undefined) index += 1;
        break;
      case '--derive-from-commits':
        options.deriveFromCommits = true;
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--allow-dirty':
        options.allowDirty = true;
        break;
      case '--help':
        options.help = true;
        break;
      default:
        throw new Error(`Unknown argument: ${flag}`);
    }
  }

  return options;
}

function splitPipeList(value) {
  return String(value ?? '')
    .split('|')
    .map((item) => item.trim())
    .filter(Boolean);
}

function escapeSingleQuoted(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function formatEntry(entry) {
  const highlightsBlock = entry.highlights
    .map((highlight) => `      '${escapeSingleQuoted(highlight)}',`)
    .join('\n');
  const linksBlock = entry.links
    .map((link) => `      { label: '${escapeSingleQuoted(link.label)}', to: '${escapeSingleQuoted(link.to)}' },`)
    .join('\n');

  return [
    '  {',
    `    version: '${escapeSingleQuoted(entry.version)}',`,
    `    releasedOn: '${escapeSingleQuoted(entry.releasedOn)}',`,
    `    badge: '${escapeSingleQuoted(entry.badge)}',`,
    `    headline: '${escapeSingleQuoted(entry.headline)}',`,
    `    summary: '${escapeSingleQuoted(entry.summary)}',`,
    '    highlights: [',
    highlightsBlock,
    '    ],',
    '    links: [',
    linksBlock,
    '    ],',
    '  },',
  ].join('\n');
}

function printHelp() {
  console.log(`Usage: pnpm release:notes [options]\n\nOptions:\n  --version <x.y.z>     Explicit release version; overrides automatic bumping\n  --bump <type>         Version bump type: patch, minor, or major (default: patch)\n  --date <YYYY-MM-DD>   Defaults to today's date\n  --badge <label>       Defaults to "Current release"\n  --headline <text>     Release title\n  --summary <text>      One-paragraph summary\n  --highlights <a|b|c>  Pipe-separated highlights\n  --links <Label:/path|Label:/path>  Pipe-separated action links\n  --derive-from-commits Derive headline, summary, and highlights from git commits\n  --from-ref <ref>      Start of git range when deriving from commits\n  --to-ref <ref>        End of git range when deriving from commits (defaults to HEAD)\n  --commits <n>         Use the latest n commits when deriving without an explicit range\n  --allow-dirty         Permit writes when the git worktree already has changes\n  --dry-run             Print the generated entry without writing\n  --help                Show this message`);
}

function escapeMarkdown(value) {
  return String(value).replace(/\[/g, '\\[').replace(/\]/g, '\\]');
}

function formatChangelogEntry(entry) {
  const linksBlock = entry.links
    .map((link) => `- [${escapeMarkdown(link.label)}](${link.to})`)
    .join('\n');
  const highlightsBlock = entry.highlights
    .map((highlight) => `- ${highlight}`)
    .join('\n');

  return [
    `## v${entry.version} - ${entry.releasedOn}`,
    '',
    `### ${entry.headline}`,
    '',
    entry.summary,
    '',
    '### Highlights',
    highlightsBlock,
    '',
    '### Links',
    linksBlock,
    '',
  ].join('\n');
}

function parseSemver(version) {
  const match = String(version).match(/^(\d+)\.(\d+)\.(\d+)$/);

  if (!match) {
    throw new Error(`Invalid semantic version: ${version}. Expected X.Y.Z`);
  }

  return {
    major: Number.parseInt(match[1], 10),
    minor: Number.parseInt(match[2], 10),
    patch: Number.parseInt(match[3], 10),
  };
}

function bumpSemver(version, bumpType) {
  const parsed = parseSemver(version);

  switch (bumpType) {
    case 'patch':
      return `${parsed.major}.${parsed.minor}.${parsed.patch + 1}`;
    case 'minor':
      return `${parsed.major}.${parsed.minor + 1}.0`;
    case 'major':
      return `${parsed.major + 1}.0.0`;
    default:
      throw new Error(`Invalid bump type: ${bumpType}. Expected patch, minor, or major.`);
  }
}

function normalizeCommitSubject(subject) {
  const trimmed = subject.trim();
  const withoutPrefix = trimmed.replace(/^(feat|fix|docs|refactor|chore|build|ci|test|perf|style)(\([^)]*\))?:\s*/i, '');
  const normalized = withoutPrefix.replace(/\s+/g, ' ').trim();

  return normalized ? normalized[0].toUpperCase() + normalized.slice(1) : '';
}

function classifyCommit(subject) {
  const lowered = subject.toLowerCase();

  for (const rule of CATEGORY_RULES) {
    if (rule.keywords.some((keyword) => lowered.includes(keyword))) {
      return rule;
    }
  }

  return { id: 'general', label: 'platform', pluralLabel: 'platform', keywords: [] };
}

async function getCommitSubjects(options) {
  const args = ['--no-pager', 'log', '--format=%s'];

  if (options.fromRef || options.toRef) {
    const toRef = options.toRef ?? 'HEAD';
    const range = `${options.fromRef ?? `${toRef}~${options.commits ?? 12}`}..${toRef}`;
    args.push(range);
  } else {
    args.push('-n', String(options.commits ?? 12));
  }

  const { stdout } = await execFileAsync('git', args, { cwd: repoRoot });

  return stdout
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

function deriveReleaseContent(commitSubjects) {
  if (commitSubjects.length === 0) {
    throw new Error('No commits found for the requested range.');
  }

  const normalizedSubjects = commitSubjects
    .map(normalizeCommitSubject)
    .filter(Boolean);

  if (normalizedSubjects.length === 0) {
    throw new Error('Commit derivation produced no usable subjects.');
  }

  const categoryCounts = new Map();
  for (const subject of normalizedSubjects) {
    const category = classifyCommit(subject);
    categoryCounts.set(category.id, {
      category,
      count: (categoryCounts.get(category.id)?.count ?? 0) + 1,
    });
  }

  const rankedCategories = [...categoryCounts.values()].sort((left, right) => right.count - left.count);
  const primary = rankedCategories[0]?.category ?? { label: 'platform', pluralLabel: 'platform' };
  const secondary = rankedCategories[1]?.category;
  const headline = secondary && secondary.id !== primary.id
    ? `${capitalize(primary.pluralLabel)} and ${secondary.pluralLabel} update`
    : `${capitalize(primary.label)} update`;
  const summaryTopics = rankedCategories.slice(0, 3).map((entry) => entry.category.pluralLabel);
  const summary = `This release packages ${normalizedSubjects.length} recent commits focused on ${joinPhrase(summaryTopics)}.`;
  const highlights = normalizedSubjects.slice(0, 5);

  return { headline, summary, highlights };
}

function capitalize(value) {
  return value[0].toUpperCase() + value.slice(1);
}

function joinPhrase(values) {
  if (values.length === 0) {
    return 'recent project updates';
  }

  if (values.length === 1) {
    return values[0];
  }

  if (values.length === 2) {
    return `${values[0]} and ${values[1]}`;
  }

  return `${values.slice(0, -1).join(', ')}, and ${values.at(-1)}`;
}

async function promptForMissing(options, defaults) {
  if (options.headline && options.summary && options.highlights.length > 0 && options.links.length > 0) {
    return options;
  }

  const rl = createInterface({ input, output });

  try {
    if (!options.headline) {
      options.headline = (await rl.question('Headline: ')).trim();
    }

    if (!options.summary) {
      options.summary = (await rl.question('Summary: ')).trim();
    }

    if (options.highlights.length === 0) {
      const answer = await rl.question('Highlights (pipe-separated): ');
      options.highlights = splitPipeList(answer);
    }

    if (options.links.length === 0) {
      const answer = await rl.question(`Links (pipe-separated Label:/path) [${defaults.links.join(' | ')}]: `);
      options.links = splitPipeList(answer || defaults.links.join('|'));
    }
  } finally {
    rl.close();
  }

  return options;
}

function normalizeLinks(rawLinks) {
  return rawLinks.map((link) => {
    const separatorIndex = link.indexOf(':');

    if (separatorIndex <= 0 || separatorIndex === link.length - 1) {
      throw new Error(`Invalid link format: ${link}. Expected Label:/path`);
    }

    return {
      label: link.slice(0, separatorIndex).trim(),
      to: link.slice(separatorIndex + 1).trim(),
    };
  });
}

function validateEntry(entry) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.releasedOn)) {
    throw new Error(`Invalid date format: ${entry.releasedOn}. Expected YYYY-MM-DD`);
  }

  if (!entry.headline) {
    throw new Error('Headline is required.');
  }

  if (!entry.summary) {
    throw new Error('Summary is required.');
  }

  if (entry.highlights.length === 0) {
    throw new Error('At least one highlight is required.');
  }

  if (entry.links.length === 0) {
    throw new Error('At least one link is required.');
  }
}

async function ensureCleanWorktree(options) {
  if (options.dryRun || options.allowDirty) {
    return;
  }

  const { stdout } = await execFileAsync('git', ['status', '--porcelain'], { cwd: repoRoot });

  if (stdout.trim()) {
    throw new Error('Refusing to write release notes with a dirty git worktree. Commit or stash your changes, or rerun with --allow-dirty.');
  }
}

async function updateChangelog(entry) {
  const header = '# Changelog\n\nGenerated release history for the browser app.\n\n';
  let source;

  try {
    source = await fs.readFile(changelogPath, 'utf8');
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      source = header;
    } else {
      throw error;
    }
  }

  if (source.includes(`## v${entry.version}`)) {
    throw new Error(`CHANGELOG.md already contains version ${entry.version}.`);
  }

  if (!source.startsWith('# Changelog')) {
    source = `${header}${source.trimStart()}`;
  }

  const insertAt = source.indexOf('\n\n') + 2;
  const prefix = source.slice(0, insertAt);
  const suffix = source.slice(insertAt).replace(/^\n+/, '');

  return `${prefix}\n${formatChangelogEntry(entry)}${suffix ? `${suffix}\n` : ''}`;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));

  if (options.help) {
    printHelp();
    return;
  }

  const rootPackageJson = JSON.parse(await fs.readFile(rootPackageJsonPath, 'utf8'));
  const webPackageJson = JSON.parse(await fs.readFile(webPackageJsonPath, 'utf8'));
  const today = new Date().toISOString().slice(0, 10);
  const targetVersion = options.version ?? bumpSemver(webPackageJson.version, options.bump);
  const defaults = {
    version: targetVersion,
    date: today,
    badge: 'Current release',
    links: ['Open generation:/generate', 'Review templates:/templates'],
  };

  if (options.commits !== undefined && (!Number.isInteger(options.commits) || options.commits <= 0)) {
    throw new Error('--commits must be a positive integer.');
  }

  parseSemver(targetVersion);

  if (options.links.length === 0) {
    options.links = [...defaults.links];
  }

  if (options.deriveFromCommits || options.fromRef || options.toRef || options.commits) {
    const derived = deriveReleaseContent(await getCommitSubjects(options));

    options.headline ??= derived.headline;
    options.summary ??= derived.summary;

    if (options.highlights.length === 0) {
      options.highlights = derived.highlights;
    }
  }

  await promptForMissing(options, defaults);

  const entry = {
    version: options.version ?? defaults.version,
    releasedOn: options.date ?? defaults.date,
    badge: options.badge ?? defaults.badge,
    headline: options.headline?.trim(),
    summary: options.summary?.trim(),
    highlights: options.highlights,
    links: normalizeLinks(options.links.length > 0 ? options.links : defaults.links),
  };

  validateEntry(entry);

  const source = await fs.readFile(releaseNotesPath, 'utf8');

  if (source.includes(`version: '${entry.version}'`)) {
    throw new Error(`Release notes already contain version ${entry.version}.`);
  }

  const updatedSource = source
    .replace("badge: 'Current release'", "badge: 'Previous release'")
    .replace(
      'export const releaseNotes: ReleaseNoteEntry[] = [\n',
      `export const releaseNotes: ReleaseNoteEntry[] = [\n${formatEntry(entry)}\n`,
    );

  if (updatedSource === source) {
    throw new Error('Failed to update release notes source. Expected releaseNotes array header was not found.');
  }

  const updatedChangelog = await updateChangelog(entry);

  if (options.dryRun) {
    console.log(`Would bump version: web ${webPackageJson.version} -> ${targetVersion}`);
    if (rootPackageJson.version !== targetVersion) {
      console.log(`Would sync root package version: ${rootPackageJson.version} -> ${targetVersion}`);
    }
    console.log(`Would update changelog: ${path.relative(repoRoot, changelogPath)}`);
    console.log(formatEntry(entry));
    return;
  }

  await ensureCleanWorktree(options);

  webPackageJson.version = targetVersion;
  rootPackageJson.version = targetVersion;

  await fs.writeFile(webPackageJsonPath, `${JSON.stringify(webPackageJson, null, 2)}\n`, 'utf8');
  await fs.writeFile(rootPackageJsonPath, `${JSON.stringify(rootPackageJson, null, 2)}\n`, 'utf8');
  await fs.writeFile(releaseNotesPath, updatedSource, 'utf8');
  await fs.writeFile(changelogPath, updatedChangelog, 'utf8');
  console.log(`Bumped package versions to ${targetVersion}`);
  console.log(`Added release note ${entry.version} to ${path.relative(repoRoot, releaseNotesPath)}`);
  console.log(`Updated ${path.relative(repoRoot, changelogPath)}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});