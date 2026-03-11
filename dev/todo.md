# Future Additions / Improvements

This file tracks possible future product and workflow additions.

It is intentionally scoped to new capabilities, UX improvements, and longer-term enhancements, not bug fixes or maintenance tasks.

Execution ownership for these backlog sections now lives in `packages/web/src/lib/roadmap.ts`.
Grouped placeholder modules have been added under existing feature directories so new work can start from real integration points instead of new top-level routes.

## Generation Workflow

- [ ] Asset-by-asset approval workflow before downstream generation continues
- [ ] Checkpointed generation sessions that let users pause, resume, or restart from any approved asset
- [ ] Partial regeneration flow for replacing one asset without discarding the rest of the draft
- [ ] Multi-model comparison runs for the same seed and template
- [ ] Batch generation queue with priorities, retry policies, and run history
- [ ] Scenario presets for common generation goals such as fast drafting, high-structure output, or art-focused packs
- [ ] Constraint builder for generation goals like tone, genre, style, and content level
- [ ] Seed remix feature that combines multiple saved concepts into one prompt
- [ ] Seed idea board with saved prompts, themes, and inspiration sets
- [ ] Assistant suggestions for strengthening weak or underspecified seeds
- [ ] Offline/local-model optimized workflow presets
- [ ] Guided first-run generation flow for helping new users reach a valid draft quickly

## Review and Editing

- [ ] Side-by-side draft comparison view for comparing alternate generations
- [ ] Structured review checklist for tone, consistency, safety, and export readiness
- [ ] Asset health scoring based on completeness, consistency, and format compliance
- [ ] Provenance view showing which upstream assets influenced each generated asset
- [ ] Inline review notes attached to individual assets
- [ ] Asset-level commenting with a simple resolved/unresolved state
- [ ] Draft branching system for exploring alternate versions of the same character
- [ ] Draft merge tools for selectively combining assets from different branches
- [ ] Version history for edited assets with restore points
- [ ] Focus mode for reviewing one asset with its immediate dependencies visible
- [ ] Assistant tools for rewriting a single asset while preserving established canon
- [ ] Read-only review links for sharing a draft state without enabling edits

## Templates and Blueprints

- [ ] Guided template creation wizard in the web UI
- [ ] Template migration assistant for updating older drafts to newer template versions
- [ ] Blueprint preview sandbox for testing prompts without saving a full draft
- [ ] Visual dependency graph for template assets and generation order
- [ ] Template marketplace or import/export bundle format for sharing templates
- [ ] Template starter kits for common character-card formats and content styles
- [ ] Template cloning flow for using an official template as a starting point for a custom one
- [ ] Template comparison view showing asset sets, dependencies, and blueprint overrides
- [ ] Blueprint linting dashboard for placeholder usage, dependency clarity, and output expectations
- [ ] Prompt experimentation lab for testing orchestrator and blueprint variants
- [ ] Shared blueprint snippet library for reusable sections and control blocks
- [ ] Template-aware onboarding tutorial for new users

## Draft Library and Organization

- [ ] Better draft library filters for archetype, tone, mode, template, and tags
- [ ] Saved searches and smart collections for large draft libraries
- [ ] Bulk metadata editing across multiple drafts
- [ ] Favorite and pin system for important drafts, templates, and presets
- [ ] Semantic search across draft content, not just metadata
- [ ] Auto-tagging suggestions based on generated content
- [ ] Archive and curation workflows for keeping large draft libraries manageable
- [ ] Custom foldering or collection system beyond timestamp-based draft storage
- [ ] Recently viewed and recently edited lists for faster navigation
- [ ] Duplicate-detection suggestions while browsing the library
- [ ] Custom metadata fields for project-specific cataloging
- [ ] Library summary dashboard with counts by template, mode, and generation source

## Canon, Worldbuilding, and Relationships

- [ ] Reusable canon library for traits, lore, tags, and recurring world details
- [ ] Worldbook or setting support that can be attached to multiple related drafts
- [ ] Relationship mapping between characters in the same universe
- [ ] Lineage timeline view showing how drafts evolved over time
- [ ] Similarity clustering to group near-duplicate or closely related drafts
- [ ] Shared faction, setting, and location records reusable across drafts
- [ ] Universe-level notes that can be referenced during generation and review
- [ ] Canon lock system for facts that should remain stable across derivative drafts
- [ ] Family tree and affiliation visualizations for related characters
- [ ] Cross-draft continuity assistant for keeping related characters aligned

## Export and Publishing

- [ ] Preset preview mode showing exactly which files and names an export will produce
- [ ] Platform capability matrix for checking which presets work with which templates
- [ ] Character pack publishing flow for producing a polished shareable bundle
- [ ] Export profiles with saved naming, packaging, and metadata rules
- [ ] One-click export bundles for common targets and sharing destinations
- [ ] Shareable web preview page for a generated character pack
- [ ] Optional branded export themes for more polished presentation packages
- [ ] Metadata manifest export for preserving provenance, model info, and template info alongside assets
- [ ] Export dry-run mode that shows mapped outputs before creating files
- [ ] Print-friendly or PDF-style presentation export for review and archiving

## Analysis and Evaluation

- [ ] Golden sample packs for template quality benchmarking
- [ ] Evaluation dashboard for model quality, cost, latency, and format success rate
- [ ] Token and cost analytics per asset, draft, template, and provider
- [ ] Usage history dashboard for models, templates, exports, and generation modes
- [ ] Quality trend tracking across model changes and template revisions
- [ ] Scorecards for comparing provider performance on specific templates
- [ ] Regression benchmark suite for measuring structural compliance over time
- [ ] Review analytics showing which assets most often need human edits
- [ ] Generation time breakdown by stage, provider, and asset count
- [ ] Template adoption analytics to show which workflows users actually prefer

## Collaboration and Sharing

- [ ] Collaboration-friendly review notes attached to individual assets
- [ ] Shared workspaces for teams curating the same draft library
- [ ] Commentable template reviews before publishing a new template version
- [ ] Import/export package format for moving drafts with metadata and history intact
- [ ] Team preset libraries for shared export and validation standards
- [ ] Curated featured templates and starter packs surfaced in-app
- [ ] Community template discovery with tags, screenshots, and example outputs
- [ ] Public/private visibility controls for shared templates and draft bundles
- [ ] Lightweight approval workflow for team-owned templates and presets
- [ ] Activity feed for recent library changes, exports, and published templates

## UX and Platform Surfaces

- [ ] Mobile-first review and approval flow for draft triage on smaller screens
- [ ] Desktop-native drag-and-drop import/export flows
- [ ] Responsive split-pane editor optimized for wide and narrow displays
- [ ] Keyboard-first review workflows across web, desktop, and TUI surfaces
- [ ] Quick actions palette for jumping to drafts, templates, exports, and tools
- [ ] Pinned dashboard widgets for recent drafts, saved searches, and active queues
- [ ] Guided empty states that teach features instead of just showing blank screens
- [ ] In-app documentation panels linked to templates, presets, and validation rules
- [ ] Customizable home screen tailored to the user's most common workflow
- [ ] Workspace mode for switching between solo drafting, review, and bulk operations

## Assistant and Automation

- [ ] Assistant tools for proposing alternate tones or styles for a selected asset
- [ ] Assistant-generated metadata suggestions like tags, summaries, and archetypes
- [ ] Auto-generated draft summaries for quick browsing in large libraries
- [ ] Conversational template helper for explaining what each asset does and depends on
- [ ] Smart recommendations for next actions after generation, review, or export
- [ ] Workflow automations for repeated sequences like generate, validate, review, and export
- [ ] Scheduled batch runs for seed lists or nightly model comparisons
- [ ] Auto-generated handoff notes summarizing what changed between draft revisions
- [ ] Safety profile presets tuned for different platforms or use cases
- [ ] Assistant-backed onboarding that adapts to the selected template and workflow
