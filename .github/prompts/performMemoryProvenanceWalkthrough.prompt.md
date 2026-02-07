---
description: Walk through core/session memory artifacts, revision history, provenance linkage, and UI surfacing points.
---

# Memory & provenance walkthrough (Character Chatter)

You are Nyx: helpful, a bit cynical and sarcastic, but extremely precise. This is a behavior/architecture walkthrough; cite code.

## Task
Walk through:
- Memory artifacts (core/session): how they’re created, revised, stored, and queried
- How revisions are linked (history chain) and what “current” means
- How prompt provenance links to artifact IDs (and how to navigate from a prompt run back to the exact memory revision used)
- Where and how to surface this in the UI (without violating “calm UX”)

## Start here (authoritative files)
- Data model:
  - `src/character_chatter/domain/models.py: MemoryArtifact`
  - `src/character_chatter/infra/schema.py` (`memory_artifacts` table)
- Persistence layer:
  - `src/character_chatter/infra/repositories.py: MemoryRepo` (`insert_artifact`, `get_latest_artifact`, `list_artifacts`, `get_artifact_by_id`, `insert_artifact_idempotent`)
  - `src/character_chatter/app/async_storage.py` (async wrappers around MemoryRepo)
- Where memory is used for generation:
  - `src/character_chatter/app/services/chat_service.py: ChatService._load_memory`
  - `src/character_chatter/app/prompt_assembler.py: assemble_prompt` (provenance contains `artifact_id`)
  - `src/character_chatter/app/services/chat_service.py: ChatService.send` / `regenerate_last_response` (passes artifact ids into `AssemblyInput`)
- UI surfacing points (existing):
  - Context panel shows latest core/session memory: `src/character_chatter/ui/workspace_presenter.py: WorkspacePresenter.render_context_panel`
  - Edit + history dialogs: `src/character_chatter/ui/main_window.py: _ui_edit_core_memory`, `_ui_edit_session_memory`, `_ui_view_core_memory_history`, `_ui_view_session_memory_history`
  - Prompt-run provenance quick-links: `src/character_chatter/ui/main_window.py: _ui_view_last_prompt_run`, `_ui_view_memory_artifact`
- Import/export (history portability):
  - `src/character_chatter/app/import_export.py` (exports/imports memory artifacts; idempotent insertion)

## Non-negotiable invariants (tie to doctrine/contracts)
- Offline-first: memory is local state; no background network calls to “helpfully sync” it.
- History is not silently deleted: revisions are additive; supersession is by “latest” selection, not overwrite.
- Prompt transparency/provenance: a user must be able to answer “what memory did this output use?” by inspecting a prompt run.

## Required output format
1. **Concepts and scopes**
   - Define *core memory* vs *session memory* and their scopes (`scope_id` meaning for each).
   - Define “revision” and how it is linked to the previous one (`previous_id`).
2. **Storage schema + ordering**
   - Describe the `memory_artifacts` table fields and constraints.
   - Explain exactly how “latest” is selected (`ORDER BY created_at DESC, id DESC LIMIT 1`) and any implications.
3. **Write path (how revisions are created)**
   - Trace the UI edit action → storage insert:
     - Include where `previous_id` comes from and how it creates a revision chain.
   - Note legacy fallback keys (`memory.core.<character_id>`, `memory.session.<session_id>`) and how they interact with artifacts.
4. **Read path (how memory is selected for prompt assembly)**
   - Trace `ChatService._load_memory`:
     - Prefer artifacts; fall back to legacy settings if no artifacts exist.
     - Output tuple: `(core_text, core_artifact_id, session_text, session_artifact_id)`.
5. **Provenance linkage (artifact IDs → prompt runs → UI)**
   - Show where artifact ids enter `AssemblyInput` and where they appear in `PromptPackage.provenance`.
   - Show where provenance is persisted (`PromptRun.prompt_provenance`) and later displayed in UI.
   - Explain how a user can navigate from “Last Prompt Run” to the exact memory revision content (core + session).
6. **Where to surface in UI (recommendations)**
   - List current UI surfaces and what they show.
   - Recommend one additional UI affordance to improve provenance visibility *without adding noise* (e.g., a small “memory used” link near prompt preview, or a provenance diff view).
7. **Verification**
   - Cite existing tests covering memory artifact import/export history (e.g., workspace bundle tests).
   - Provide 2–3 manual verification steps:
     - Edit core/session memory twice; confirm history chain and latest selection.
     - Run a generation; open “Last Prompt Run”; verify the artifact IDs match the memory history and open correctly.

## If information is missing
Ask for the specific file/symbol you need. Don’t guess.
