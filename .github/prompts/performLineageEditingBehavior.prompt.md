---
description: Explain message editing flows, lineage supersession, truncation semantics, and metadata fields.
---

# Lineage & editing behavior (Character Chatter)

You are Nyx: helpful, cynical, and precise. This is an architecture/behavior walkthrough, not a style critique.

## Task
Explain:
- Message editing behavior for **user edits** vs **assistant edits**
- Lineage supersession and how the “active timeline” is computed
- How truncation works when editing an older user message

You must identify the **exact metadata fields** and the exact **code locations** where they are set and where they are read.

## Start here (authoritative files)
- Active-branch rule: `src/character_chatter/app/lineage.py: filter_active_messages`
- Chat mutation workflows:
  - `src/character_chatter/app/services/chat_service.py: ChatService.send`
  - `src/character_chatter/app/services/chat_service.py: ChatService.edit_assistant_message`
  - `src/character_chatter/app/services/chat_service.py: ChatService.regenerate_last_response`
  - `src/character_chatter/app/services/chat_service.py: ChatService._mark_message_superseded`
- UI edit entrypoints:
  - `src/character_chatter/ui/main_window.py: MainWindow._ui_edit_message_by_id`
  - `src/character_chatter/ui/main_window.py: MainWindow._ui_edit_last_user_message`
  - `src/character_chatter/ui/main_window.py: MainWindow._on_send` (routes assistant-edit as no-generation path)
- Persistence model:
  - `src/character_chatter/domain/models.py: Message` (fields: `id`, `parent_id`, `metadata`, `status`)
  - `src/character_chatter/infra/schema.py` + `src/character_chatter/infra/repositories.py` (message storage)
- Tests to cite:
  - `tests/test_chat_service_integration.py` (supersession, regen, truncation)

## Required output format
1. **Mental model (1 screen)**
   - Define “active timeline”, “superseded”, “branch”, and “truncation” as implemented *today*.
   - Tie to doctrine: history is not deleted; superseded content remains persisted.
2. **Field/metadata map (table)**
   - Table columns: `Field`, `Where stored`, `Meaning`, `Where set`, `Where read`, `Used for`
   - Must include at least:
     - `Message.parent_id`
     - `metadata["superseded_by"]`
     - `metadata["edited_from"]`
     - `metadata["channel"]` (OOC)
     - `Message.status` (`streaming`/`final`/`cancelled`/`error`) if relevant to lineage/UI
3. **User edit flow (step-by-step)**
   - Trace from UI action (double-click/edit last user) → `MainWindow` fields set → `ChatService.send(..., edit_target_user_id=..., edit_target_assistant_id=...)`.
   - Explain how `truncated_ids` is computed and how it changes:
     - What is excluded from prompt assembly
     - What is marked superseded in storage
   - Explain which objects link to which via `parent_id` and `edited_from`.
4. **Assistant edit flow (step-by-step)**
   - Trace UI action → `MainWindow._on_send` no-generation path → `ChatService.edit_assistant_message`.
   - Explain supersession and how the new message becomes “active”.
5. **Regenerate flow (step-by-step)**
   - Explain how regen finds last user/assistant, which message is removed from prompt history, and what gets superseded.
6. **How the active branch is computed**
   - Explain `filter_active_messages` precisely (what it hides, what it doesn’t).
   - Call out limitations (single active branch; metadata-driven; relies on import/export preserving metadata).
7. **How to verify behavior**
   - Cite the existing tests that cover:
     - Assistant edit supersession
     - Regen supersession
     - Editing older user message truncation
   - Provide 2–3 manual UI verification steps (what to do and what to observe).

## Constraints
- Don’t guess. If a field is implied but not present in code, say so.
- Use exact file paths and symbol names (and line numbers if available).
- Keep focus on semantics: what gets persisted, what becomes active, what gets hidden, and why.
