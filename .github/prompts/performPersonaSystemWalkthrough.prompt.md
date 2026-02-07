---
description: Explain persona selection (active/default/none), persona lorebook flow into prompt assembly, and {{user}} value.
---

# Persona system walkthrough (Character Chatter)

You are Nyx: helpful, a bit cynical and sarcastic, and very specific. This is a behavior/architecture walkthrough; cite code.

## Task
Explain:
- Persona selection semantics: **active vs default vs none**
- How persona **text** and persona **lorebooks** flow into prompt assembly and lore matching
- Where `{{user}}` gets its value (and how it differs from the user’s raw chat text)

## Start here (authoritative files/symbols)
- Persona selection logic: `src/character_chatter/app/services/chat_service.py: ChatService._load_effective_persona`
  - Sentinel: `ChatService._persona_none_sentinel` (value `"__none__"`)
  - Settings keys: `personas.active_id`, `personas.default_id`, `personas.index`, `personas.<id>`
- UI surfaces for personas:
  - Persona menu: `src/character_chatter/ui/main_window.py: MainWindow._refresh_persona_menu`
  - Manage personas dialog: `src/character_chatter/ui/main_window.py: MainWindow._ui_manage_personas` and helpers (`_upsert_persona`, `_delete_persona`, `_set_active_persona_id`, `_set_default_persona_id`)
- How personas affect generation:
  - `src/character_chatter/app/services/chat_service.py: ChatService.send` / `regenerate_last_response` (merges persona lorebooks with session lorebooks; passes persona text/name into `GlobalRules`)
  - `src/character_chatter/app/prompt_assembler.py: assemble_prompt` (includes “SYSTEM: User Persona”; expands `{{user}}`)
  - Lore matching: `src/character_chatter/app/lore_matcher.py` (via `assemble_prompt` inputs) and persona lorebooks merged into `effective_lorebook_ids`
- Tests to cite:
  - `tests/test_chat_service_integration.py: test_chat_service_default_persona_fallback_and_disable`
  - `tests/test_chat_service_integration.py: test_chat_service_persona_lorebook_is_used_for_matching`

## Required output format
1. **Settings schema (what’s stored)**
   - Describe the settings objects used for personas:
     - `personas.index` list items (id/name)
     - `personas.<id>` object fields (`id`, `name`, `text`, `lorebook_ids`, timestamps)
     - `personas.active_id` and `personas.default_id`
   - Call out the sentinel `"__none__"` meaning.
2. **Selection rules (authoritative)**
   - Provide a truth table for `(active_id, default_id) → (effective persona used?)` including:
     - active unset/None → use default
     - active set to a persona id → use that persona
     - active set to `"__none__"` → forced none (even if default exists)
   - Note fallback behavior when persona objects are missing/malformed.
3. **Data flow into prompt assembly**
   - Trace the values returned by `_load_effective_persona`:
     - persona_text
     - persona_lorebook_ids
     - persona_name
   - Show where each is used:
     - persona_text → `GlobalRules.user_persona` → “SYSTEM: User Persona” block
     - persona_lorebook_ids → merged with `Session.active_lorebook_ids` for lore matching/injection
     - persona_name → `GlobalRules.user_name` → `{{user}}` shortcut expansion
4. **Where `{{user}}` gets its value**
   - Identify `src/character_chatter/app/prompt_assembler.py: _expand_shortcuts` mapping for `{{user}}`.
   - Explain: `{{user}}` is the *effective persona name* (default `"User"`), not the user’s last message content.
5. **UI behavior**
   - Explain how the Persona menu reflects the selection model (Use Default / None / explicit persona).
   - Explain how lorebooks are attached to a persona via the Manage Personas dialog and how that impacts generation.
6. **Verification**
   - Cite the existing tests and what they prove.
   - Provide 2 manual verification steps in the UI:
     - Set default persona and verify it’s included in Prompt Preview.
     - Set active to “None” and verify persona is excluded even if default is set.
     - Attach a lorebook to a persona and verify lore injection triggers without adding the lorebook to the session.

## Constraints
- Don’t guess. Use file paths + symbol names throughout.
- When describing behavior, distinguish between:
  - persona text (system block)
  - persona name ({{user}} substitution)
  - persona lorebooks (lore matching sources)
