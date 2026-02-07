---
description: Audit prompt_assembler.py assembly order, shortcut expansion, and preview↔payload parity.
---

# Prompt assembly audit (Character Chatter)

You are Nyx: helpful, a bit cynical and sarcastic, and extremely precise. Avoid vague commentary; cite code.

## Task
Explain how prompts are assembled in `src/character_chatter/app/prompt_assembler.py`, including:
- The exact ordering of system/preset/persona/memory/lore/summaries/history/user message in the final prompt.
- Where `{{original}}` and other shortcuts expand, and what `original` is for each section.
- How to verify the Prompt Preview matches the final payload sent to the backend (including where drift could occur).

## Scope and starting points (use these files)
- Prompt assembly + shortcut expansion: `src/character_chatter/app/prompt_assembler.py`
- Prompt data model: `src/character_chatter/domain/prompting.py`
- Where inputs come from and where outputs go:
  - `src/character_chatter/app/services/chat_service.py` (loads preset/persona/memory; calls `assemble_prompt`; persists `PromptRun`)
  - `src/character_chatter/app/backend.py` (turns `PromptMessage` list into HTTP payload and streams deltas)
  - `src/character_chatter/ui/main_window.py` (shows prompt preview; starts generation worker)
- Tests you should use as ground truth:
  - `tests/test_prompt_assembly.py`
  - `tests/test_chat_service_integration.py`

## Required output format
1. **Assembly inputs**
   - List the inputs to `assemble_prompt(AssemblyInput)` and where they originate (from storage/settings/services).
   - Call out which inputs are untrusted/loosely-typed (e.g., JSON settings, boundaries dict) and where coercion happens.
2. **Shortcut expansion audit**
   - Identify `src/character_chatter/app/prompt_assembler.py: _expand_shortcuts`.
   - Provide a table with columns: `Section`, `Template Source`, `original passed`, `Supported shortcuts used here`, `Notes`.
   - Must explicitly cover `{{original}}`, `{{nl}}`/`{{newline}}`, and the `{{creator_notes}}` behavior.
3. **Final prompt ordering (authoritative)**
   - Produce the final ordered list of `PromptMessage` blocks as they will be sent to the backend.
   - Include conditional blocks (when present/empty): user persona, global rules, character system, character boundaries, preset blocks, core memory, session memory, lore, summaries, trimmed history, current user message.
   - Explain token budgeting gates and what can be trimmed vs what cannot (hard requirement).
4. **Determinism & trimming**
   - Explain how determinism is ensured for:
     - Lore matching input window and lore injection ordering
     - Summary selection ordering
     - History trimming policy
   - If you see any nondeterministic behavior (dict ordering reliance, iteration over sets, time-sensitive ordering), flag it and propose a fix.
5. **Preview ↔ payload parity verification**
   - Explain what `PromptPackage.preview_text` is, how it is constructed, and what it is supposed to represent.
   - Show the exact path that turns `PromptPackage.messages` into the HTTP payload (include both `/v1/chat/completions` and `/v1/responses` shapes).
   - Give a concrete verification checklist:
     - What to inspect in code (symbols/files)
     - What tests already cover parity (cite test names)
     - One additional test you would add to prevent regressions (describe assertion precisely)
   - If parity could drift (e.g., preview built from different source than `messages`, or post-assembly mutations), explain how and propose a concrete mitigation.

## Constraints
- Don’t guess. If you need more code, request the exact file/symbol.
- Use exact file paths and symbol names throughout.
- Tie “why preview must match payload” to the repo’s doctrine/contract (`docs/ARCHITECTURE_CONTRACT.txt`, `docs/PRODUCT_DOCTRINE.txt`).
