export interface ReleaseNoteLink {
  label: string;
  to: string;
}

export interface ReleaseNoteEntry {
  version: string;
  releasedOn: string;
  badge: string;
  headline: string;
  summary: string;
  highlights: string[];
  links: ReleaseNoteLink[];
}

// Generated and maintained by tools/generation/generate-release-notes.mjs.
export const releaseNotes: ReleaseNoteEntry[] = [
  {
    version: '2.0.10',
    releasedOn: '2026-03-12',
    badge: 'Current release',
    headline: 'Documentation and platform update',
    summary: 'This release packages 12 recent commits focused on documentation, platform, and templates.',
    highlights: [
      'Add data attribute for global assistant root in ChatPanel component',
      'Update version to 2.0.9; enhance changelog and release notes with recent documentation, platform updates, and new links',
      'Add modal open state handling for ExportModal and GlobalAssistant components',
      'Doc update',
      'Update version to 2.0.7; enhance changelog and release notes with recent documentation, UI updates, and new links',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.9',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and platform update',
    summary: 'This release packages 12 recent commits focused on documentation, platform, and templates.',
    highlights: [
      'Add modal open state handling for ExportModal and GlobalAssistant components',
      'Doc update',
      'Update version to 2.0.7; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.6; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.5; enhance changelog and release notes with recent documentation, UI updates, and new links',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.8',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and themes update',
    summary: 'This release packages 12 recent commits focused on documentation, themes, and platform.',
    highlights: [
      'Update version to 2.0.7; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.6; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.5; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.4; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.3; enhance changelog and release notes with recent documentation, UI updates, and export functionality improvements',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.7',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and themes.',
    highlights: [
      'Update version to 2.0.6; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.5; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.4; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.3; enhance changelog and release notes with recent documentation, UI updates, and export functionality improvements',
      'Update version to 2.0.2 and enhance changelog with recent documentation and UI updates; refactor download functions for improved usability',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.6',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and themes.',
    highlights: [
      'Update version to 2.0.5; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.4; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.3; enhance changelog and release notes with recent documentation, UI updates, and export functionality improvements',
      'Update version to 2.0.2 and enhance changelog with recent documentation and UI updates; refactor download functions for improved usability',
      'Update version to 2.0.1 and enhance release notes with documentation and UI updates',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.5',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and themes.',
    highlights: [
      'Update version to 2.0.4; enhance changelog and release notes with recent documentation, UI updates, and new links',
      'Update version to 2.0.3; enhance changelog and release notes with recent documentation, UI updates, and export functionality improvements',
      'Update version to 2.0.2 and enhance changelog with recent documentation and UI updates; refactor download functions for improved usability',
      'Update version to 2.0.1 and enhance release notes with documentation and UI updates',
      'Enhance release notes generation and add changelog for version 2.0.0',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.4',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and themes.',
    highlights: [
      'Update version to 2.0.3; enhance changelog and release notes with recent documentation, UI updates, and export functionality improvements',
      'Update version to 2.0.2 and enhance changelog with recent documentation and UI updates; refactor download functions for improved usability',
      'Update version to 2.0.1 and enhance release notes with documentation and UI updates',
      'Enhance release notes generation and add changelog for version 2.0.0',
      'Add "What\'s New" page and integrate release notes; implement version check in CI',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.3',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and themes.',
    highlights: [
      'Update version to 2.0.2 and enhance changelog with recent documentation and UI updates; refactor download functions for improved usability',
      'Update version to 2.0.1 and enhance release notes with documentation and UI updates',
      'Enhance release notes generation and add changelog for version 2.0.0',
      'Add "What\'s New" page and integrate release notes; implement version check in CI',
      'Enhance theme documentation and add new themes',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.2',
    releasedOn: '2026-03-12',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and themes.',
    highlights: [
      'Update version to 2.0.1 and enhance release notes with documentation and UI updates',
      'Enhance release notes generation and add changelog for version 2.0.0',
      'Add "What\'s New" page and integrate release notes; implement version check in CI',
      'Enhance theme documentation and add new themes',
      'Update license in README and enhance security policy in SECURITY.md; clarify usage instructions in openrouter.toml and midnight.toml',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.1',
    releasedOn: '2026-03-11',
    badge: 'Previous release',
    headline: 'Documentation and UI update',
    summary: 'This release packages 12 recent commits focused on documentation, UI, and platform.',
    highlights: [
      'Enhance release notes generation and add changelog for version 2.0.0',
      'Add "What\'s New" page and integrate release notes; implement version check in CI',
      'Enhance theme documentation and add new themes',
      'Update license in README and enhance security policy in SECURITY.md; clarify usage instructions in openrouter.toml and midnight.toml',
      'Refactor themes: Remove unused color variables and delete obsolete theme files',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '2.0.0',
    releasedOn: '2026-03-11',
    badge: 'Previous release',
    headline: 'Browser-first workspace upgrade',
    summary: 'The app now centers the browser runtime with tighter template tooling, local draft workflows, and clearer in-app boundaries around browser-only storage.',
    highlights: [
      'Home, drafts, and generation flows now reflect the active browser-only product surface instead of older local-server assumptions.',
      'Template, blueprint, and validation tools are wired for the current web workflow with stricter contract visibility.',
      'Theme and export management continue to run client-side with built-in presets and browser-stored customization.',
    ],
    links: [
      { label: 'Open generation', to: '/generate' },
      { label: 'Review templates', to: '/templates' },
    ],
  },
  {
    version: '1.9.0',
    releasedOn: '2026-02-24',
    badge: 'Stability',
    headline: 'Draft review and validation pass',
    summary: 'Recent work tightened draft browsing and review workflows so saved outputs are easier to inspect before export.',
    highlights: [
      'Recent draft metadata and favorites are surfaced more clearly in the browser workspace.',
      'Validation and comparison surfaces were expanded to make format problems easier to catch before export.',
      'Library and review placeholders were aligned with the current roadmap so staged features stay visible without implying they already ship.',
    ],
    links: [
      { label: 'Browse drafts', to: '/drafts' },
      { label: 'Run validation', to: '/validation' },
    ],
  },
  {
    version: '1.8.0',
    releasedOn: '2026-02-03',
    badge: 'Workflow',
    headline: 'Template-aware generation baseline',
    summary: 'Generation, shared parsing, and export helpers were stabilized around the current official template families.',
    highlights: [
      'The web flow stays aligned with official V2/V3 and Aksho template realities instead of flattening them into one asset graph.',
      'Shared parsing and export helpers were tightened around stricter asset expectations and template metadata.',
      'Blueprint-focused tooling was organized around contract safety and lower-diff maintenance.',
    ],
    links: [
      { label: 'Inspect blueprints', to: '/blueprints' },
      { label: 'View templates', to: '/templates' },
    ],
  },
];