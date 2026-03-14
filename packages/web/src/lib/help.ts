export const GETTING_STARTED_GUIDE_ID = 'getting-started';
export const GETTING_STARTED_TOUR_ID = 'getting-started';
export const SAFE_STORAGE_TOUR_ID = 'protect-your-work';
export const REVIEW_EXPORT_TOUR_ID = 'review-and-export';
export const DRAFT_LIBRARY_TOUR_ID = 'draft-library';
export const VALIDATION_TOUR_ID = 'validation-workflow';
export const BLUEPRINTS_SAFETY_TOUR_ID = 'blueprints-safety';

export interface HelpActionLink {
  label: string;
  to: string;
}

export interface HelpGuideStep {
  id: string;
  title: string;
  description: string;
  to: string;
  actionLabel: string;
}

export interface HelpTopic {
  id: string;
  title: string;
  category: 'Getting Started' | 'Concepts' | 'Troubleshooting';
  summary: string;
  bullets: string[];
  actions: HelpActionLink[];
}

export interface GuidedTourStep {
  id: string;
  title: string;
  description: string;
  to: string;
  routeLabel: string;
  bullets: string[];
  matchMode?: 'exact' | 'prefix';
  targetId?: string;
  targetLabel?: string;
}

export interface GuidedTour {
  id: string;
  title: string;
  summary: string;
  audience: string;
  estimatedMinutes: number;
  steps: GuidedTourStep[];
}

export interface PageHelpEntry {
  id: string;
  match: string;
  matchMode: 'exact' | 'prefix';
  title: string;
  summary: string;
  keyActions: string[];
  pitfalls: string[];
  actions: HelpActionLink[];
  relatedTopicIds: string[];
}

export interface RouteCoverageManifestEntry {
  route: string;
  pageHelpId: string;
  coverage: 'complete';
}

export interface AppRouteHelpCoverageEntry {
  path: string;
  pageHelpId: string;
}

export interface GuidedTourTargetCatalogEntry {
  id: string;
  route: string;
}

export const gettingStartedSteps: HelpGuideStep[] = [
  {
    id: 'browser-storage',
    title: 'Understand where your work lives',
    description: 'Drafts, templates, settings, and theme edits stay in this browser profile by default. Clearing browser storage removes them unless you export a backup first.',
    to: '/about',
    actionLabel: 'Read about browser storage',
  },
  {
    id: 'api-keys',
    title: 'Set up an API key',
    description: 'Open Settings, pick the provider you actually use, and paste the provider key you want the browser app to send with generation requests.',
    to: '/settings',
    actionLabel: 'Open Settings',
  },
  {
    id: 'template',
    title: 'Choose a template before you generate',
    description: 'Templates define which assets are produced and what export structure must be preserved. Start with an official template before making custom ones.',
    to: '/templates',
    actionLabel: 'Review templates',
  },
  {
    id: 'generate',
    title: 'Create your first draft',
    description: 'Go to Generate, enter a seed, confirm the content mode, and let the app produce a full draft pack you can review asset by asset.',
    to: '/generate',
    actionLabel: 'Start generating',
  },
  {
    id: 'review',
    title: 'Review before exporting',
    description: 'Open the saved draft, check for consistency and missing details, and refine anything that does not fit the character you want to keep.',
    to: '/drafts',
    actionLabel: 'Open draft library',
  },
  {
    id: 'export',
    title: 'Export with browser expectations in mind',
    description: 'On mobile or in a browser, export may use a share sheet, a new tab, or the download tray instead of a desktop-style save dialog.',
    to: '/data',
    actionLabel: 'See backup and export tools',
  },
];

export const helpTopics: HelpTopic[] = [
  {
    id: 'what-is-a-template',
    title: 'Templates vs. blueprints',
    category: 'Concepts',
    summary: 'Templates choose the asset graph. Blueprints define how each asset is generated. Most users should start with templates and leave blueprints alone until they understand the workflow.',
    bullets: [
      'Templates decide which files exist and in what order they depend on each other.',
      'Blueprints are stricter and can break parser-facing output if edited casually.',
      'Use official templates first, then move to custom templates only after you understand review and export.',
    ],
    actions: [
      { label: 'Open templates', to: '/templates' },
      { label: 'Open blueprints', to: '/blueprints' },
    ],
  },
  {
    id: 'how-export-works',
    title: 'How export works in the browser',
    category: 'Getting Started',
    summary: 'Browser export behavior depends on the device and browser. Normal web apps do not always get a native filename prompt.',
    bullets: [
      'Desktop browsers often save directly to Downloads.',
      'Mobile browsers may show a share sheet or open a new tab instead of prompting for a filename.',
      'Use Data Manager exports when you want a full backup of browser-stored content.',
    ],
    actions: [
      { label: 'Open Data Manager', to: '/data' },
      { label: 'Open draft review', to: '/drafts' },
    ],
  },
  {
    id: 'api-key-setup',
    title: 'API key setup without guesswork',
    category: 'Getting Started',
    summary: 'The browser app talks to your chosen model provider using the API key you enter in Settings. No local backend service is required for the current web runtime.',
    bullets: [
      'Choose the provider you really use before selecting a model.',
      'If a key looks corrupted or includes invisible characters, the app will reject it.',
      'Persist keys only on devices you control.',
    ],
    actions: [
      { label: 'Open Settings', to: '/settings' },
      { label: 'Read About storage', to: '/about' },
    ],
  },
  {
    id: 'first-draft-review',
    title: 'How to review a first draft',
    category: 'Concepts',
    summary: 'A good review checks structure first, then consistency, then polish. Do not export just because generation finished.',
    bullets: [
      'Confirm the character name, major facts, and tone stay consistent across assets.',
      'Watch for unresolved placeholders or format drift in strict assets.',
      'Use refinement and validation before exporting to a target format.',
    ],
    actions: [
      { label: 'Open Drafts', to: '/drafts' },
      { label: 'Open Validation', to: '/validation' },
    ],
  },
  {
    id: 'common-blockers',
    title: 'Common blockers and what to do next',
    category: 'Troubleshooting',
    summary: 'Most early problems are configuration or browser-behavior issues, not generator bugs.',
    bullets: [
      'If generation fails immediately, verify the provider, model, and API key in Settings.',
      'If export feels silent on mobile, check for a share sheet, a new tab, or the browser download tray.',
      'If you lose drafts after clearing browser data, restore from a JSON backup in Data Manager.',
    ],
    actions: [
      { label: 'Open Settings', to: '/settings' },
      { label: 'Open Data Manager', to: '/data' },
    ],
  },
];

export const helpCategories = ['Getting Started', 'Concepts', 'Troubleshooting'] as const;

export const guidedTours: GuidedTour[] = [
  {
    id: GETTING_STARTED_TOUR_ID,
    title: 'Getting Started Tour',
    summary: 'Walk through the safest first-run path from setup to a first export-ready draft.',
    audience: 'New users who want the app to tell them what to do next.',
    estimatedMinutes: 6,
    steps: [
      {
        id: 'start-home',
        title: 'Start from Home',
        description: 'Home is the launch surface for the beginner path. It tells you what the current browser app can do and where to go next.',
        to: '/',
        routeLabel: 'Home',
        bullets: [
          'Use Home when you are not sure which workflow to open first.',
          'The browser profile you are using is the current storage location for drafts and settings.',
        ],
      },
      {
        id: 'set-up-provider',
        title: 'Set up provider access',
        description: 'Open Settings before you generate anything. This avoids the most common first-run failure: trying to generate with a missing or mismatched provider key.',
        to: '/settings',
        routeLabel: 'Settings',
        targetId: 'settings-api-keys',
        targetLabel: 'API Keys',
        bullets: [
          'Pick the provider you actually use.',
          'Enter the API key you want the browser app to send.',
          'Use trusted devices if you choose to persist keys locally.',
        ],
      },
      {
        id: 'choose-template',
        title: 'Choose the template first',
        description: 'Templates decide which assets exist and how the draft will export. Make this choice before refining the prompt or seed.',
        to: '/templates',
        routeLabel: 'Templates',
        bullets: [
          'Start with an official template unless you already understand custom template behavior.',
          'Template changes are structural, not cosmetic.',
        ],
      },
      {
        id: 'generate-draft',
        title: 'Generate the first draft',
        description: 'Once provider setup and template choice are in place, Generate becomes the first full workflow step.',
        to: '/generate',
        routeLabel: 'Generate',
        targetId: 'generation-submit',
        targetLabel: 'Generate Character button',
        bullets: [
          'Enter a concrete seed instead of a vague one-liner.',
          'Treat the first result as a draft to review, not a final export.',
        ],
      },
      {
        id: 'review-library',
        title: 'Review saved drafts',
        description: 'Drafts is where you reopen saved work and decide what should move into deeper review, validation, or export.',
        to: '/drafts',
        routeLabel: 'Drafts',
        bullets: [
          'Open the draft library after generation to confirm the draft actually saved.',
          'Use draft review before export when details need cleanup.',
        ],
      },
      {
        id: 'protect-work',
        title: 'Protect your work with backups',
        description: 'Data Manager is the safety net for browser-local storage. Use it before clearing browser data or moving to another device.',
        to: '/data',
        routeLabel: 'Data Manager',
        bullets: [
          'Export backups before risky changes.',
          'Treat API key exports as sensitive data.',
        ],
      },
    ],
  },
  {
    id: SAFE_STORAGE_TOUR_ID,
    title: 'Protect Your Work Tour',
    summary: 'Learn the browser-storage model, backup path, and the pages that matter when you need to avoid losing work.',
    audience: 'Users who are worried about where data lives and how to recover it safely.',
    estimatedMinutes: 4,
    steps: [
      {
        id: 'storage-model',
        title: 'Confirm the storage model',
        description: 'About explains that the current product surface is the browser app. That matters because drafts and configuration live in browser storage by default.',
        to: '/about',
        routeLabel: 'About',
        bullets: [
          'Do not assume a local backend or desktop shell is saving your work for you.',
          'Treat this browser profile as the place where your work currently lives.',
        ],
      },
      {
        id: 'backup-tools',
        title: 'Use backup tools intentionally',
        description: 'Data Manager is where you export or restore browser-stored content when you need to migrate, recover, or safeguard work.',
        to: '/data',
        routeLabel: 'Data Manager',
        bullets: [
          'Back up before clearing site data.',
          'Use restore only with files you trust and understand.',
        ],
      },
      {
        id: 'privacy-expectations',
        title: 'Understand privacy expectations',
        description: 'Privacy explains the difference between local browser storage and the provider requests you intentionally send during generation.',
        to: '/privacy',
        routeLabel: 'Privacy',
        bullets: [
          'Local storage and provider traffic are different concerns.',
          'Backups can still expose sensitive material if handled carelessly.',
        ],
      },
      {
        id: 'secure-settings',
        title: 'Review secure settings habits',
        description: 'Settings is where you control provider keys and persistence choices, so it is part of the data-protection workflow too.',
        to: '/settings',
        routeLabel: 'Settings',
        targetId: 'settings-api-keys',
        targetLabel: 'API Keys',
        bullets: [
          'Persist keys only on devices you control.',
          'If something feels unsafe or unclear, return to Help Center before continuing.',
        ],
      },
    ],
  },
  {
    id: REVIEW_EXPORT_TOUR_ID,
    title: 'Review and Export Tour',
    summary: 'Walk through the review controls that matter before you hand a draft off to export.',
    audience: 'Users who already generated a draft and need a safe review path before exporting.',
    estimatedMinutes: 5,
    steps: [
      {
        id: 'review-actions',
        title: 'Start from the review action bar',
        description: 'The review header is the control surface for validation, favoriting, export, and draft deletion.',
        to: '/drafts/',
        routeLabel: 'Draft Review',
        matchMode: 'prefix',
        targetId: 'review-actions',
        targetLabel: 'Review actions',
        bullets: [
          'Do not export immediately if you have not checked the draft structure yet.',
          'Keep destructive actions separate from export so you do not rush them.',
        ],
      },
      {
        id: 'review-validate',
        title: 'Validate before export',
        description: 'Use validation before exporting when the draft has been edited or when the template has strict structure requirements.',
        to: '/drafts/',
        routeLabel: 'Draft Review',
        matchMode: 'prefix',
        targetId: 'review-validate',
        targetLabel: 'Validate button',
        bullets: [
          'Validation catches structural problems that a quick read can miss.',
          'Treat missing required pieces or unresolved placeholders as blockers.',
        ],
      },
      {
        id: 'review-assets',
        title: 'Read the assets, not just the title',
        description: 'The asset list is where consistency problems usually reveal themselves. Check names, tone, and required sections across multiple assets.',
        to: '/drafts/',
        routeLabel: 'Draft Review',
        matchMode: 'prefix',
        targetId: 'review-assets',
        targetLabel: 'Draft assets',
        bullets: [
          'A draft can look good in one asset while still being broken elsewhere.',
          'Use targeted editing when only one asset drifts.',
        ],
      },
      {
        id: 'review-export',
        title: 'Export with browser expectations in mind',
        description: 'When the draft is coherent, use Export. On browser and mobile surfaces this may hand off through a share sheet, new tab, or downloads tray instead of a native save dialog.',
        to: '/drafts/',
        routeLabel: 'Draft Review',
        matchMode: 'prefix',
        targetId: 'review-export',
        targetLabel: 'Export button',
        bullets: [
          'The app now tells you which handoff method was used.',
          'If export feels silent on mobile, check share and browser download surfaces.',
        ],
      },
      {
        id: 'export-choose-preset',
        title: 'Choose the export preset inside the modal',
        description: 'Once the export modal opens, choose the preset that matches the system you are exporting for instead of blindly taking the first option.',
        to: '/drafts/',
        routeLabel: 'Export Modal',
        matchMode: 'prefix',
        targetId: 'export-preset-selection',
        targetLabel: 'Export preset selection',
        bullets: [
          'Presets change output structure and destination compatibility.',
          'If you are unsure, review the preset description before continuing.',
        ],
      },
      {
        id: 'export-confirm',
        title: 'Confirm export and watch the handoff result',
        description: 'Use the Export button after the preset is selected, then follow the browser-specific save or share flow the app reports back to you.',
        to: '/drafts/',
        routeLabel: 'Export Modal',
        matchMode: 'prefix',
        targetId: 'export-confirm',
        targetLabel: 'Export confirm button',
        bullets: [
          'A successful export in the browser may still look different from a desktop save dialog.',
          'Use the success message to know whether the file went to share, download, or a new tab.',
        ],
      },
    ],
  },
  {
    id: DRAFT_LIBRARY_TOUR_ID,
    title: 'Draft Library Tour',
    summary: 'Learn how to use the library as a review queue instead of a pile of saved outputs.',
    audience: 'Users who generated drafts and need to understand where to reopen, compare, and triage them.',
    estimatedMinutes: 4,
    steps: [
      {
        id: 'draft-library-overview',
        title: 'Treat Drafts as your working library',
        description: 'The library is not just storage. It is where you decide which drafts are worth opening for deeper review or export.',
        to: '/drafts',
        routeLabel: 'Drafts',
        targetId: 'drafts-list',
        targetLabel: 'Draft list',
        bullets: [
          'Open drafts from here after generation instead of relying on memory or browser history.',
          'Use names, tags, and favorites to keep the library readable as it grows.',
        ],
      },
      {
        id: 'draft-workbench',
        title: 'Use the workbench for comparison and checks',
        description: 'The workbench keeps review aids in view so you can compare outputs and think before opening a draft for editing.',
        to: '/drafts',
        routeLabel: 'Drafts',
        targetId: 'drafts-workbench',
        targetLabel: 'Draft workbench',
        bullets: [
          'Comparison and review tools help you choose the better draft before you start editing.',
          'Staged placeholders are visible here, but only the active tools should drive your next action.',
        ],
      },
      {
        id: 'draft-review-hand-off',
        title: 'Open one draft for real review',
        description: 'Once a draft looks worth keeping, open it and continue with validation, editing, and export on the review page.',
        to: '/drafts',
        routeLabel: 'Drafts',
        targetId: 'drafts-open-review',
        targetLabel: 'Draft review links',
        bullets: [
          'The library is the triage layer. The review page is the editing and export layer.',
          'Back up important work before risky cleanup or browser-data changes.',
        ],
      },
    ],
  },
  {
    id: VALIDATION_TOUR_ID,
    title: 'Validation Workflow Tour',
    summary: 'Walk through the validation screen so structural checks become a normal part of review instead of a last-minute panic step.',
    audience: 'Users who edit drafts or export to strict formats and need to know when validation matters.',
    estimatedMinutes: 4,
    steps: [
      {
        id: 'validation-overview',
        title: 'Use validation as a structural checkpoint',
        description: 'Validation is where you confirm the draft still matches the expected structure before you export or hand it off to another tool.',
        to: '/validation',
        routeLabel: 'Validation',
        targetId: 'validation-draft-panel',
        targetLabel: 'Validate saved draft panel',
        bullets: [
          'Run validation after major edits, not only after generation.',
          'Treat structural failures as blockers instead of cosmetic warnings.',
        ],
      },
      {
        id: 'validation-run',
        title: 'Choose the simplest input path',
        description: 'Most users should validate a saved draft by review ID instead of typing a manual path unless they know exactly what they are checking.',
        to: '/validation',
        routeLabel: 'Validation',
        targetId: 'validation-draft-run',
        targetLabel: 'Validate Draft button',
        bullets: [
          'Use saved-draft validation for normal browser workflows.',
          'Manual paths are useful when you are investigating a specific stored location.',
        ],
      },
      {
        id: 'validation-results',
        title: 'Read the results for real blockers',
        description: 'The result panel tells you whether the draft passed and shows the lines that need attention before export.',
        to: '/validation',
        routeLabel: 'Validation',
        targetId: 'validation-results',
        targetLabel: 'Validation results',
        bullets: [
          'Fix missing required sections and unresolved placeholders first.',
          'If the result passes, move back to review or export with more confidence.',
        ],
      },
    ],
  },
  {
    id: BLUEPRINTS_SAFETY_TOUR_ID,
    title: 'Blueprint Safety Tour',
    summary: 'Learn when to leave blueprints alone, when to inspect them carefully, and where to bail out to safer surfaces.',
    audience: 'Non-technical or first-time users who might wander into blueprints before understanding template contracts.',
    estimatedMinutes: 4,
    steps: [
      {
        id: 'blueprints-search',
        title: 'Treat Blueprints as inspection first, editing second',
        description: 'Start by searching and reading. Do not jump into editing unless you know why a blueprint needs to change.',
        to: '/blueprints',
        routeLabel: 'Blueprints',
        targetId: 'blueprints-search',
        targetLabel: 'Blueprint search',
        bullets: [
          'Search helps you understand which blueprint family you are looking at.',
          'Reading the path and description usually tells you whether the file is core, system, or template-specific.',
        ],
      },
      {
        id: 'blueprints-tools',
        title: 'Use browser safety tools before editing',
        description: 'The lint and sandbox tools exist so you can inspect behavior without immediately rewriting contract-heavy text.',
        to: '/blueprints',
        routeLabel: 'Blueprints',
        targetId: 'blueprints-tools',
        targetLabel: 'Blueprint tools',
        bullets: [
          'Use lint and preview to reduce guesswork.',
          'A readable blueprint is not automatically a safe blueprint.',
        ],
      },
      {
        id: 'blueprints-exit-ramp',
        title: 'Know the safer alternative',
        description: 'If you are trying to change workflow shape rather than raw blueprint text, templates are usually the safer surface for early users.',
        to: '/blueprints',
        routeLabel: 'Blueprints',
        targetId: 'blueprints-list',
        targetLabel: 'Blueprint list',
        bullets: [
          'Do not edit a blueprint just because you found the right file name.',
          'When in doubt, go back to Templates or Help Center before making changes.',
        ],
      },
    ],
  },
];

export const pageHelpEntries: PageHelpEntry[] = [
  {
    id: 'home',
    match: '/',
    matchMode: 'exact',
    title: 'Home help',
    summary: 'Use Home as the launch surface for first-run guidance, recent updates, quick actions, and your next step into the workflow.',
    keyActions: [
      'Start with the Getting Started guide if this is your first run.',
      'Use Quick Actions to jump straight into Generate, Drafts, or Seeds.',
      'Check What’s New when behavior changes after an update.',
    ],
    pitfalls: [
      'Do not assume your work syncs automatically. This browser profile is the storage location by default.',
      'Do not skip Settings if generation cannot start; most early issues begin there.',
    ],
    actions: [
      { label: 'Open Help Center', to: '/help' },
      { label: 'Open Settings', to: '/settings' },
    ],
    relatedTopicIds: ['api-key-setup', 'common-blockers'],
  },
  {
    id: 'generate',
    match: '/generate',
    matchMode: 'exact',
    title: 'Generate help',
    summary: 'Generation is where you choose the template, seed, provider, and content mode that become a full draft pack.',
    keyActions: [
      'Choose the template before you spend time refining the seed.',
      'Keep the seed concrete enough that the model has something to preserve across assets.',
      'Use review after generation instead of trying to perfect everything in one pass.',
    ],
    pitfalls: [
      'A missing or invalid API key will usually fail generation before useful output appears.',
      'Changing template assumptions late can invalidate your review expectations.',
    ],
    actions: [
      { label: 'Open Settings', to: '/settings' },
      { label: 'Open templates', to: '/templates' },
    ],
    relatedTopicIds: ['api-key-setup', 'what-is-a-template'],
  },
  {
    id: 'seed-generator',
    match: '/seed-generator',
    matchMode: 'exact',
    title: 'Seed Generator help',
    summary: 'Use Seed Generator when you need raw concept material before you commit to a full draft workflow.',
    keyActions: [
      'Generate multiple seeds and keep the one with the clearest identity.',
      'Pass the best seed into Generate instead of trying to export from here.',
    ],
    pitfalls: [
      'A seed is not a finished draft; it still needs a template and generation pass.',
    ],
    actions: [
      { label: 'Open Generate', to: '/generate' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
  {
    id: 'validation',
    match: '/validation',
    matchMode: 'exact',
    title: 'Validation help',
    summary: 'Validation helps you catch structural issues before export, especially on strict templates or edited drafts.',
    keyActions: [
      'Validate after major edits and before export.',
      'Treat missing required assets or unresolved placeholders as blockers, not cosmetic warnings.',
    ],
    pitfalls: [
      'Passing generation does not guarantee export readiness.',
    ],
    actions: [
      { label: 'Open Drafts', to: '/drafts' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['first-draft-review', 'common-blockers'],
  },
  {
    id: 'batch',
    match: '/batch',
    matchMode: 'exact',
    title: 'Batch help',
    summary: 'Batch generation is for running multiple drafts in sequence without driving the app one draft at a time.',
    keyActions: [
      'Keep concurrency conservative until you know your provider limits.',
      'Use batch for throughput, not for first-time learning of the workflow.',
    ],
    pitfalls: [
      'High concurrency can make failures harder to interpret.',
    ],
    actions: [
      { label: 'Open Generate', to: '/generate' },
      { label: 'Open Settings', to: '/settings' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
  {
    id: 'drafts',
    match: '/drafts',
    matchMode: 'exact',
    title: 'Draft library help',
    summary: 'Drafts is where you reopen saved work, check metadata, and decide which draft should move into review or export.',
    keyActions: [
      'Open the review page for the draft you want to polish or export.',
      'Use metadata and favorites to keep the library manageable as it grows.',
    ],
    pitfalls: [
      'Deleting a draft removes the browser-local copy unless you already exported or backed it up.',
    ],
    actions: [
      { label: 'Open Data Manager', to: '/data' },
      { label: 'Open Validation', to: '/validation' },
    ],
    relatedTopicIds: ['first-draft-review', 'common-blockers'],
  },
  {
    id: 'draft-review',
    match: '/drafts/',
    matchMode: 'prefix',
    title: 'Draft review help',
    summary: 'Review is where you inspect generated assets, refine weak spots, validate structure, and export only when the pack is coherent.',
    keyActions: [
      'Check the character name, core traits, and tone across multiple assets before exporting.',
      'Use refine tools for targeted edits instead of regenerating the whole draft immediately.',
      'Validate after meaningful edits.',
    ],
    pitfalls: [
      'A draft that reads well in one asset can still fail export because another asset drifted or broke format.',
      'Do not ignore placeholders or empty required sections in strict assets.',
    ],
    actions: [
      { label: 'Open Validation', to: '/validation' },
      { label: 'Open Data Manager', to: '/data' },
    ],
    relatedTopicIds: ['first-draft-review', 'how-export-works'],
  },
  {
    id: 'templates',
    match: '/templates',
    matchMode: 'exact',
    title: 'Templates help',
    summary: 'Templates define which assets exist, how they depend on each other, and what export structure needs to remain valid.',
    keyActions: [
      'Use official templates first so you understand the app’s baseline workflow.',
      'Treat template changes as structural decisions, not cosmetic ones.',
    ],
    pitfalls: [
      'Changing template expectations late can invalidate assumptions in review and export.',
    ],
    actions: [
      { label: 'Open Generate', to: '/generate' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['what-is-a-template'],
  },
  {
    id: 'blueprints',
    match: '/blueprints',
    matchMode: 'exact',
    title: 'Blueprints help',
    summary: 'Blueprints are advanced prompt/compiler definitions. They are powerful, but they are not a safe first editing surface for non-technical users.',
    keyActions: [
      'Prefer templates unless you are intentionally changing generation structure.',
      'Preserve parser-facing formats and placeholders carefully when editing.',
    ],
    pitfalls: [
      'A casual blueprint edit can break validation or export even if the text still looks readable.',
    ],
    actions: [
      { label: 'Open templates', to: '/templates' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['what-is-a-template'],
  },
  {
    id: 'blueprint-editor',
    match: '/blueprints/edit',
    matchMode: 'prefix',
    title: 'Blueprint editor help',
    summary: 'The editor is for advanced changes to blueprint text and should be treated as a strict contract surface, not a freeform note field.',
    keyActions: [
      'Keep output structures intact when the target asset expects rigid formatting.',
      'Validate edits before using them in a generation workflow.',
    ],
    pitfalls: [
      'Unfilled placeholders, broken structure, or dependency mistakes can cascade through later assets.',
    ],
    actions: [
      { label: 'Open Validation', to: '/validation' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['what-is-a-template', 'common-blockers'],
  },
  {
    id: 'similarity',
    match: '/similarity',
    matchMode: 'exact',
    title: 'Similarity help',
    summary: 'Similarity helps you inspect overlap between drafts so you can catch repeats, redundancy, or near-duplicates.',
    keyActions: [
      'Use it after building a larger draft library or batch output set.',
    ],
    pitfalls: [
      'Similarity is analysis support, not a replacement for human review.',
    ],
    actions: [
      { label: 'Open Drafts', to: '/drafts' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['first-draft-review'],
  },
  {
    id: 'offspring',
    match: '/offspring',
    matchMode: 'exact',
    title: 'Offspring help',
    summary: 'Offspring combines parent drafts into a derivative result, so parent quality and consistency matter before you start.',
    keyActions: [
      'Choose parents that are already reviewed and structurally healthy.',
    ],
    pitfalls: [
      'Using unstable or contradictory parents gives unstable offspring output.',
    ],
    actions: [
      { label: 'Open Drafts', to: '/drafts' },
      { label: 'Open Validation', to: '/validation' },
    ],
    relatedTopicIds: ['first-draft-review'],
  },
  {
    id: 'lineage',
    match: '/lineage',
    matchMode: 'exact',
    title: 'Lineage help',
    summary: 'Lineage shows how related drafts connect over time so you can track derivations and review ancestry.',
    keyActions: [
      'Use lineage when you need provenance, not when you need direct editing.',
    ],
    pitfalls: [
      'Lineage helps you understand relationships, but it does not repair structural draft issues on its own.',
    ],
    actions: [
      { label: 'Open Drafts', to: '/drafts' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['first-draft-review'],
  },
  {
    id: 'themes',
    match: '/themes',
    matchMode: 'exact',
    title: 'Themes help',
    summary: 'Themes control the browser UI appearance. Runtime theme behavior lives in the app, not in the reference TOML files under resources.',
    keyActions: [
      'Use presets as a base and save customizations intentionally.',
    ],
    pitfalls: [
      'Editing reference theme files in the repo is not the same as changing the live browser theme runtime.',
    ],
    actions: [
      { label: 'Open Settings', to: '/settings' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
  {
    id: 'settings',
    match: '/settings',
    matchMode: 'exact',
    title: 'Settings help',
    summary: 'Settings controls provider access, model defaults, browser persistence choices, theme behavior, and tutorial/help preferences.',
    keyActions: [
      'Start here if generation fails, models are missing, or you are unsure where data is stored.',
      'Use the Help and Tutorials section to restart the starter guide or re-enable tips.',
    ],
    pitfalls: [
      'Saving API keys in browser storage is convenient, but it should be limited to devices you trust.',
    ],
    actions: [
      { label: 'Open Help Center', to: '/help' },
      { label: 'Open About', to: '/about' },
    ],
    relatedTopicIds: ['api-key-setup', 'common-blockers'],
  },
  {
    id: 'data',
    match: '/data',
    matchMode: 'exact',
    title: 'Data Manager help',
    summary: 'Data Manager is the safety net for browser-local drafts, config, and backups.',
    keyActions: [
      'Export backups before clearing browser data or changing devices.',
      'Treat API-key export files as sensitive data.',
    ],
    pitfalls: [
      'Clearing browser storage without a backup removes local drafts and settings.',
    ],
    actions: [
      { label: 'Open Help Center', to: '/help' },
      { label: 'Open Settings', to: '/settings' },
    ],
    relatedTopicIds: ['how-export-works', 'common-blockers'],
  },
  {
    id: 'whats-new',
    match: '/whats-new',
    matchMode: 'exact',
    title: 'What’s New help',
    summary: 'Use this page to understand recent product changes and staged roadmap work before assuming the workflow still behaves the same way.',
    keyActions: [
      'Check release notes after updates when a flow feels different.',
    ],
    pitfalls: [
      'Roadmap items are not the same as implemented features.',
    ],
    actions: [
      { label: 'Open Help Center', to: '/help' },
      { label: 'Open Home', to: '/' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
  {
    id: 'about',
    match: '/about',
    matchMode: 'exact',
    title: 'About help',
    summary: 'About explains the current browser-first product surface, storage model, and the difference between the app runtime and repo reference assets.',
    keyActions: [
      'Use About when you need to confirm how the browser app stores or handles your work.',
    ],
    pitfalls: [
      'Do not assume older Python/backend flows exist in the current product unless you can see them in the app.',
    ],
    actions: [
      { label: 'Open Help Center', to: '/help' },
      { label: 'Open Settings', to: '/settings' },
    ],
    relatedTopicIds: ['api-key-setup', 'common-blockers'],
  },
  {
    id: 'help-center',
    match: '/help',
    matchMode: 'exact',
    title: 'Help Center help',
    summary: 'Help Center is the structured fallback when you want answers without guessing which page or workflow to visit next.',
    keyActions: [
      'Start with the Getting Started section if you are still learning the workflow.',
      'Use concepts when the terminology is the blocker.',
      'Use troubleshooting when the app behavior does not match your expectation.',
    ],
    pitfalls: [
      'The Help Center explains the browser app. It does not guarantee parity with future mobile or desktop surfaces.',
    ],
    actions: [
      { label: 'Open Home', to: '/' },
      { label: 'Open Settings', to: '/settings' },
    ],
    relatedTopicIds: ['api-key-setup', 'common-blockers'],
  },
  {
    id: 'license',
    match: '/license',
    matchMode: 'exact',
    title: 'License help',
    summary: 'License explains the repository licensing terms and should be read when you need usage or redistribution clarity.',
    keyActions: [
      'Use this page when you need the exact license text or attribution expectations.',
    ],
    pitfalls: [
      'License answers legal distribution questions, not workflow or storage questions.',
    ],
    actions: [
      { label: 'Open About', to: '/about' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
  {
    id: 'terms',
    match: '/terms',
    matchMode: 'exact',
    title: 'Terms help',
    summary: 'Terms of Use covers the rules around using the app, exports, and generated content through the current browser surface.',
    keyActions: [
      'Use this page when you need policy guidance rather than workflow guidance.',
    ],
    pitfalls: [
      'Terms is not a how-to page. Use Help Center for workflow questions.',
    ],
    actions: [
      { label: 'Open Help Center', to: '/help' },
      { label: 'Open Privacy', to: '/privacy' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
  {
    id: 'privacy',
    match: '/privacy',
    matchMode: 'exact',
    title: 'Privacy help',
    summary: 'Privacy explains what stays in browser storage, what reaches provider APIs, and what sensitive data you are responsible for handling carefully.',
    keyActions: [
      'Use this page when you need to understand local storage, API key handling, or data exposure to providers.',
    ],
    pitfalls: [
      'Browser-local does not mean impossible to lose. You still need backups if the data matters.',
    ],
    actions: [
      { label: 'Open Data Manager', to: '/data' },
      { label: 'Open Settings', to: '/settings' },
    ],
    relatedTopicIds: ['api-key-setup', 'common-blockers'],
  },
  {
    id: 'security',
    match: '/security',
    matchMode: 'exact',
    title: 'Security help',
    summary: 'Security covers vulnerability reporting and safe handling of provider keys and browser-stored configuration.',
    keyActions: [
      'Use this page when the question is about secure handling or vulnerability reporting.',
    ],
    pitfalls: [
      'Security policy does not replace provider-specific account protection practices.',
    ],
    actions: [
      { label: 'Open Settings', to: '/settings' },
      { label: 'Open Privacy', to: '/privacy' },
    ],
    relatedTopicIds: ['api-key-setup'],
  },
  {
    id: 'code-of-conduct',
    match: '/code-of-conduct',
    matchMode: 'exact',
    title: 'Code of Conduct help',
    summary: 'Code of Conduct covers collaboration expectations for the repository and project community spaces.',
    keyActions: [
      'Use this page for contribution and interaction standards, not workflow setup.',
    ],
    pitfalls: [
      'Community rules are separate from app usage or licensing terms.',
    ],
    actions: [
      { label: 'Open About', to: '/about' },
      { label: 'Open Help Center', to: '/help' },
    ],
    relatedTopicIds: ['common-blockers'],
  },
];

export const routeCoverageManifest: RouteCoverageManifestEntry[] = [
  { route: '/', pageHelpId: 'home', coverage: 'complete' },
  { route: '/generate', pageHelpId: 'generate', coverage: 'complete' },
  { route: '/seed-generator', pageHelpId: 'seed-generator', coverage: 'complete' },
  { route: '/validation', pageHelpId: 'validation', coverage: 'complete' },
  { route: '/batch', pageHelpId: 'batch', coverage: 'complete' },
  { route: '/drafts', pageHelpId: 'drafts', coverage: 'complete' },
  { route: '/drafts/:id', pageHelpId: 'draft-review', coverage: 'complete' },
  { route: '/templates', pageHelpId: 'templates', coverage: 'complete' },
  { route: '/blueprints', pageHelpId: 'blueprints', coverage: 'complete' },
  { route: '/blueprints/edit/*', pageHelpId: 'blueprint-editor', coverage: 'complete' },
  { route: '/lineage', pageHelpId: 'lineage', coverage: 'complete' },
  { route: '/similarity', pageHelpId: 'similarity', coverage: 'complete' },
  { route: '/offspring', pageHelpId: 'offspring', coverage: 'complete' },
  { route: '/themes', pageHelpId: 'themes', coverage: 'complete' },
  { route: '/settings', pageHelpId: 'settings', coverage: 'complete' },
  { route: '/data', pageHelpId: 'data', coverage: 'complete' },
  { route: '/about', pageHelpId: 'about', coverage: 'complete' },
  { route: '/help', pageHelpId: 'help-center', coverage: 'complete' },
  { route: '/whats-new', pageHelpId: 'whats-new', coverage: 'complete' },
  { route: '/license', pageHelpId: 'license', coverage: 'complete' },
  { route: '/terms', pageHelpId: 'terms', coverage: 'complete' },
  { route: '/privacy', pageHelpId: 'privacy', coverage: 'complete' },
  { route: '/security', pageHelpId: 'security', coverage: 'complete' },
  { route: '/code-of-conduct', pageHelpId: 'code-of-conduct', coverage: 'complete' },
];

export const appRouteHelpCoverage: AppRouteHelpCoverageEntry[] = routeCoverageManifest.map((entry) => ({
  path: entry.route,
  pageHelpId: entry.pageHelpId,
}));

export const guidedTourTargetCatalog: GuidedTourTargetCatalogEntry[] = [
  { id: 'settings-api-keys', route: '/settings' },
  { id: 'settings-model', route: '/settings' },
  { id: 'settings-help-tutorials', route: '/settings' },
  { id: 'generation-seed', route: '/generate' },
  { id: 'generation-content-mode', route: '/generate' },
  { id: 'generation-template', route: '/generate' },
  { id: 'generation-submit', route: '/generate' },
  { id: 'drafts-workbench', route: '/drafts' },
  { id: 'drafts-list', route: '/drafts' },
  { id: 'drafts-open-review', route: '/drafts' },
  { id: 'review-actions', route: '/drafts/:id' },
  { id: 'review-validate', route: '/drafts/:id' },
  { id: 'review-export', route: '/drafts/:id' },
  { id: 'review-assets', route: '/drafts/:id' },
  { id: 'export-preset-selection', route: '/drafts/:id' },
  { id: 'export-confirm', route: '/drafts/:id' },
  { id: 'validation-draft-panel', route: '/validation' },
  { id: 'validation-draft-run', route: '/validation' },
  { id: 'validation-results', route: '/validation' },
  { id: 'blueprints-search', route: '/blueprints' },
  { id: 'blueprints-tools', route: '/blueprints' },
  { id: 'blueprints-list', route: '/blueprints' },
];

function normalizeRoutePattern(path: string): string {
  const withoutWildcard = path.replace(/\*$/, '');
  const withoutParams = withoutWildcard.replace(/:[^/]+/g, '');
  return withoutParams.endsWith('/') || withoutParams === '/' ? withoutParams : `${withoutParams}`;
}

function routeSupportsPath(routePath: string, stepPath: string, matchMode: 'exact' | 'prefix'): boolean {
  const normalizedRoute = normalizeRoutePattern(routePath);

  if (matchMode === 'exact') {
    return routePath === stepPath || normalizedRoute === stepPath;
  }

  return stepPath.startsWith(normalizedRoute) || normalizedRoute.startsWith(stepPath);
}

export function resolvePageHelp(pathname: string): PageHelpEntry | null {
  const matches = pageHelpEntries.filter((entry) =>
    entry.matchMode === 'exact' ? pathname === entry.match : pathname.startsWith(entry.match)
  );

  if (matches.length === 0) {
    return null;
  }

  return matches.sort((left, right) => right.match.length - left.match.length)[0] ?? null;
}

export function getGuidedTour(tourId: string): GuidedTour | null {
  return guidedTours.find((tour) => tour.id === tourId) ?? null;
}

export function isGuidedTourStepActive(pathname: string, step: GuidedTourStep): boolean {
  const matchMode = step.matchMode ?? 'exact';
  return matchMode === 'exact' ? pathname === step.to : pathname.startsWith(step.to);
}

export function validateHelpRouteCoverage(routeEntries: readonly AppRouteHelpCoverageEntry[]): string[] {
  const pageHelpIds = new Set(pageHelpEntries.map((entry) => entry.id));
  const seenRoutes = new Set<string>();
  const issues: string[] = [];

  for (const entry of routeEntries) {
    if (seenRoutes.has(entry.path)) {
      issues.push(`Duplicate help coverage route: ${entry.path}`);
      continue;
    }

    seenRoutes.add(entry.path);

    if (!pageHelpIds.has(entry.pageHelpId)) {
      issues.push(`Missing page help entry for route ${entry.path}: ${entry.pageHelpId}`);
    }
  }

  for (const pageHelpEntry of pageHelpEntries) {
    const routeExists = routeEntries.some((entry) => entry.pageHelpId === pageHelpEntry.id);
    if (!routeExists) {
      issues.push(`Page help entry is not mapped to an app route: ${pageHelpEntry.id}`);
    }
  }

  return issues;
}

export function validateGuidedTourConfiguration(
  routeEntries: readonly AppRouteHelpCoverageEntry[],
  targetEntries: readonly GuidedTourTargetCatalogEntry[]
): string[] {
  const targetCatalog = new Map(targetEntries.map((entry) => [entry.id, entry.route]));
  const issues: string[] = [];

  for (const tour of guidedTours) {
    for (const step of tour.steps) {
      const matchMode = step.matchMode ?? 'exact';
      const routeExists = routeEntries.some((entry) => routeSupportsPath(entry.path, step.to, matchMode));

      if (!routeExists) {
        issues.push(`Guided tour step points to an unmapped route: ${tour.id}/${step.id} -> ${step.to}`);
      }

      if (!step.targetId) {
        continue;
      }

      const targetRoute = targetCatalog.get(step.targetId);
      if (!targetRoute) {
        issues.push(`Guided tour step references an unknown target anchor: ${tour.id}/${step.id} -> ${step.targetId}`);
        continue;
      }

      if (!routeSupportsPath(targetRoute, step.to, matchMode)) {
        issues.push(
          `Guided tour step target route mismatch: ${tour.id}/${step.id} -> ${step.targetId} is cataloged for ${targetRoute}, step route is ${step.to}`
        );
      }
    }
  }

  return issues;
}